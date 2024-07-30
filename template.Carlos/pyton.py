from io import BytesIO
from msilib import Table
from tkinter import Canvas
from turtle import color
from flask import Flask, make_response, render_template, request, redirect
import psycopg2
import math
import os
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
from reportlab.pdfgen import canvas

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle, Paragraph

aplicativo = Flask(__name__)

#Método que faz a conexão com o banco de dados
def conecta_db():
    conecta = psycopg2.connect(host='localhost', database='postgres', user='postgres', password='12345')
    return conecta

#Rota principal
@aplicativo.route("/")
def homepage():
    return render_template('form.html')


#Cadastro
@aplicativo.route("/cadastro", methods=['POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        cidade = request.form['cidade']
        estado = request.form['estado']
        profissao = request.form['profissao']

        conexao = conecta_db()
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO cliente (nome, cpf, cidade, estado, profissao) VALUES (%s, %s, %s, %s, %s)", (nome, cpf, cidade, estado, profissao))
        conexao.commit()
        cursor.close()
        conexao.close()

        return render_template('form_sucesso.html')






#Grid (relatório)
@aplicativo.route("/grid", methods=['GET','POST'])
def grid():
    if request.method == 'POST':
        relatorio = request.form['gerar_grid']
        conexao = conecta_db()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM cliente")
        resultado = cursor.fetchall()

        cursor.close()

        return render_template('grid_completo.html', resultado=resultado)
    else:
        return render_template('grid_completo.html', resultado=None)






#Filtro de pesquisaa
@aplicativo.route("/filtro_rota", methods=['GET','POST'])
def filtro():
    if request.method == 'POST':
        filtro_pesquisa = request.form['filtro_input']
        conexao = conecta_db()
        cursor = conexao.cursor()
        cursor.execute("SELECT nome, cpf, estado FROM cliente WHERE nome LIKE %s", ('%' + filtro_pesquisa + '%',))
        resultado = cursor.fetchall()

        cursor.close()

        return render_template('filtro.html', resultado=resultado)
    else:
        return render_template('filtro.html', resultado=None)


#Rota da paginação
@aplicativo.route("/paginacao", methods=['GET', 'POST'])
def paginacao():
    page = request.args.get('page', 1, type=int)
    quantidade = 5

    conexao = conecta_db()
    cursor = conexao.cursor()
    #Aqui ele vai contar a quantidade de registros
    cursor.execute('SELECT count(*) FROM cliente')
    total_items = cursor.fetchone()[0]

    #Calcular o número total de páginas
    total_pages = math.ceil(total_items / quantidade)

    #Calcular a saída da consulta
    offset = (page - 1) * quantidade

    cursor.execute('''SELECT nome, cpf, cidade, estado, profissao FROM cliente ORDER BY nome LIMIT %s OFFSET %s''', (quantidade, offset))

    clientes = cursor.fetchall()
    cursor.close()
    conexao.close()

    clientes_lista = []
    for cliente in clientes:
        clientes_lista.append({
            'nome':cliente[0],
            'cpf':cliente[1],
            'cidade':cliente[2],
            'estado':cliente[3],
            'profissao':cliente[4]
        })

    #return render_template('grid_completo.html', clientes=clientes_lista, page=page, total_pages=total_pages)
    return render_template('grid_teste.html', clientes=clientes_lista, page=page, total_pages=total_pages)

#Gerar relatório em pdf
@aplicativo.route('/gerar_pdf')
def gerar_pdf():
    conexao = conecta_db()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM cliente")
    dados = cursor.fetchall()
    conexao.close()

# Pdf_buffer é uma variável que usa a função da classe BytesIO para armazenar o PDF em memória
    pdf_buffer = BytesIO()


# Cria o canvas para o PDF com um tamanho de página personalizado
    custom_page_size = (800, 600)  # Exemplo de tamanho personalizado
    p = Canvas.Canvas(pdf_buffer, pagesize=custom_page_size)
    width, height = custom_page_size

    # Adiciona a imagem de fundo
    #p.drawImage("static/imgs/senac.jpg", 0, 0, width=width, height=height, mask='auto')

    # Estilos
   
    styles = getSampleStyleSheet() # type: ignore
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.darkblue, underline=True) # type: ignore
    table_header_style = ParagraphStyle(name='TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.white) # type: ignore
    table_cell_style = ParagraphStyle(name='TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=12, textColor=colors.darkblue) # type: ignore

    # Adiciona o título
    title = Paragraph("Relatório de Alunos", title_style) # type: ignore
    title.wrapOn(p, width - 200, 40)
    title.drawOn(p, 100, 750)

    # Prepara os dados da tabela
    tabela_dados = [["Nome", "CPF", "Cidade", "Estado", "Profissão"]] + list(dados)
    colWidths = [110, 110, 110, 120, 190]  # Ajuste essas larguras conforme necessário
    tabela = Table(tabela_dados, colWidths=colWidths)


    #Estilos da tabela
    tabela_estilos = TableStyle([ # type: ignore
        ('BACKGROUND', (0, 0), (-1, 0), color.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), color.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), color.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, color.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 1), (-1, -1), color.darkblue),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica')
    ])
    tabela.setStyle(tabela_estilos)

    # Adiciona a tabela ao canvas
    tabela.wrapOn(p, width - 100, height - 200)

    # Ajuste aqui para alterar o espaçamento do topo (50 é X, 600 - ... é Y)
    tabela.drawOn(p, 50, 600 - (len(dados) * 20) - 50)  

    # Finaliza a página e salva o PDF
    p.showPage()
    p.save()

    # Define o cabeçalho do arquivo PDF
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=relatorio.pdf'

    return response


#Informações padrão do sistema web
if __name__ == "__main__":
    aplicativo.run(debug=True, port=8085, host='127.0.0.1')

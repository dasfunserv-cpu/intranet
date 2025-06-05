from flask import Flask, render_template, send_from_directory, request
import os
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# Caminho base onde os arquivos estão organizados por diretoria
BASE_DIR = 'static/recados'

@app.route('/')
def index():
    # Lista completa das diretorias disponíveis
    diretorias = [
        'PRE-DF - Diretoria Financeira',
        'PRE-DPR - Diretoria de Previdência',
        'PRE-GC - Gestao de Compliance',
        'PRE-GS - Gestão de Saúde',
        'PRE-JUR - Jurídico',
        'PRE-SA - Supervisão Administrativa',
        'PRE-ST - Supervisão Técnica'
    ]
    # Renderiza a página inicial com os botões de acesso às diretorias
    return render_template('index.html', diretorias=diretorias)

@app.route('/recados/<diretoria>')
def recados(diretoria):
    # Obtém o termo de busca da query string, se houver
    busca = request.args.get('busca', '').lower()
    # Define o caminho da pasta específica da diretoria
    caminho = os.path.join(BASE_DIR, diretoria)

    # Lista de extensões permitidas
    extensoes_permitidas = ['.pdf', '.docx', '.xlsx', '.xls', '.png', '.jpg', '.jpeg', '.txt', '.webm', '.mp4', '.csv']

    # Lista os arquivos com extensões permitidas
    arquivos = [f for f in os.listdir(caminho)
                if os.path.splitext(f)[1].lower() in extensoes_permitidas]

    # Filtra os arquivos se um termo de busca foi informado
    if busca:
        arquivos = [f for f in arquivos if busca in f.lower()]

    # Agrupamento por mês/ano de modificação
    arquivos_agrupados = defaultdict(list)
    for arquivo in arquivos:
        caminho_arquivo = os.path.join(caminho, arquivo)
        timestamp = os.path.getmtime(caminho_arquivo)
        data_modificacao = datetime.fromtimestamp(timestamp)
        chave_data = data_modificacao.strftime('%B %Y')  # Ex: 'Abril 2025'
        arquivos_agrupados[chave_data].append({
            'nome': arquivo,
            'data': data_modificacao.strftime('%d/%m/%Y'),
        })

    # Ordena os grupos por data decrescente
    arquivos_agrupados_ordenados = dict(sorted(
        arquivos_agrupados.items(),
        key=lambda item: datetime.strptime(item[0], '%B %Y'),
        reverse=True
    ))

    return render_template('recados.html',
                           diretoria=diretoria,
                           arquivos_agrupados=arquivos_agrupados_ordenados,
                           busca=busca)

@app.route('/recado/<diretoria>/<arquivo>')
def abrir_arquivo(diretoria, arquivo):
    # Envia o arquivo selecionado para o navegador abrir ou baixar
    return send_from_directory(os.path.join(BASE_DIR, diretoria), arquivo)

if __name__ == '__main__':
    # Executa o servidor Flask acessível em toda a rede local na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, render_template, send_from_directory, request, send_file, abort, redirect, url_for, flash
import os
from collections import defaultdict
from datetime import datetime
from docx2pdf import convert
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # necessário para usar flash()

# Caminho base onde os arquivos estão organizados por diretoria
BASE_DIR = 'static/recados'
UPLOAD_FOLDER = BASE_DIR
TEMP_PDF_FOLDER = 'temp_pdf'
os.makedirs(TEMP_PDF_FOLDER, exist_ok=True)

# Diretórios existentes
DIRETORIAS = [
    'Diretoria Financeira',
    'Diretoria de Previdência',
    'Gestao de Compliance',
    'Gestão de Saúde',
    'Jurídico',
    'Supervisão Administrativa',
    'Circulares e Instruções Normativas',
    'Gestão de Recursos'
]

# Extensões permitidas
EXTENSOES_PERMITIDAS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt', '.jpg', '.jpeg', '.png', '.mp4', '.webm'}

def extensao_permitida(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in EXTENSOES_PERMITIDAS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        diretoria = request.form.get('diretoria')
        file = request.files.get('arquivo')

        if diretoria not in DIRETORIAS:
            flash('Setor inválido.', 'danger')
            return redirect(request.url)

        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'warning')
            return redirect(request.url)

        if not extensao_permitida(file.filename):
            flash('Extensão de arquivo não permitida.', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        setor_path = os.path.join(UPLOAD_FOLDER, diretoria)
        os.makedirs(setor_path, exist_ok=True)
        file.save(os.path.join(setor_path, filename))

        flash('Arquivo enviado com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', diretorias=DIRETORIAS)

@app.route('/recados/<diretoria>')
def recados(diretoria):
    busca = request.args.get('busca', '').lower()
    caminho = os.path.join(BASE_DIR, diretoria)

    arquivos = [f for f in os.listdir(caminho)
                if os.path.splitext(f)[1].lower() in EXTENSOES_PERMITIDAS]

    if busca:
        arquivos = [f for f in arquivos if busca in f.lower()]

    arquivos_listados = []
    for arquivo in arquivos:
        caminho_arquivo = os.path.join(caminho, arquivo)
        timestamp = os.path.getmtime(caminho_arquivo)
        data_modificacao = datetime.fromtimestamp(timestamp)
        arquivos_listados.append({
            'nome': arquivo,
            'data': data_modificacao.strftime('%d/%m/%Y'),
            'timestamp': timestamp
        })

    arquivos_listados.sort(key=lambda x: x['timestamp'], reverse=True)

    return render_template('recados.html',
                           diretoria=diretoria,
                           arquivos=arquivos_listados,
                           busca=busca)

@app.route('/recado/<diretoria>/<arquivo>')
def abrir_arquivo_visualizador(diretoria, arquivo):
    return send_from_directory(os.path.join(BASE_DIR, diretoria), arquivo)

@app.route('/visualizar/<diretoria>/<arquivo>')
def visualizar_arquivo(diretoria, arquivo):
    ext = arquivo.rsplit('.', 1)[-1].lower()
    caminho_arquivo = os.path.join(UPLOAD_FOLDER, diretoria, arquivo)

    if not os.path.exists(caminho_arquivo):
        abort(404)

    if ext in ['doc', 'docx']:
        nome_pdf = f"{arquivo.rsplit('.', 1)[0]}_{diretoria.replace(' ', '_')}.pdf"
        caminho_pdf = os.path.join(TEMP_PDF_FOLDER, nome_pdf)

        if not os.path.exists(caminho_pdf):
            try:
                convert(caminho_arquivo, caminho_pdf)
            except Exception as e:
                return f"Erro na conversão do arquivo: {e}", 500

        return send_file(caminho_pdf, mimetype='application/pdf')

    return send_file(caminho_arquivo)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

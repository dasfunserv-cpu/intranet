from flask import Flask, render_template, send_from_directory, request, send_file, abort, redirect, url_for, flash
import os
from collections import defaultdict
from datetime import datetime
from docx2pdf import convert
from werkzeug.utils import secure_filename
import subprocess

def converter_para_pdf(input_path, output_path):
    try:
        output_dir = os.path.dirname(output_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        converted_pdf = os.path.join(output_dir, base_name + '.pdf')

        subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            input_path
        ], check=True)

        if os.path.exists(converted_pdf):
            os.rename(converted_pdf, output_path)
            return True
        else:
            print("Arquivo PDF não encontrado após a conversão.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Erro na conversão: {e}")
        return False

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

BASE_DIR = 'static/recados'
UPLOAD_FOLDER = BASE_DIR
TEMP_PDF_FOLDER = 'temp_pdf'
os.makedirs(TEMP_PDF_FOLDER, exist_ok=True)

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

EXTENSOES_PERMITIDAS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp',
    '.ppt', '.pptx', '.odt', '.ods', '.odp', '.rtf',
    '.mp4', '.webm', '.avi', '.mov', '.mkv',
    '.zip', '.rar', '.7z'
}

def extensao_permitida(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in EXTENSOES_PERMITIDAS

@app.route('/', methods=['GET', 'POST'])
def index():
    busca = request.args.get('busca', '').lower()
    resultados = []

    quantidade_por_diretoria = {}

    for diretoria in DIRETORIAS:
        caminho = os.path.join(BASE_DIR, diretoria)
        if os.path.exists(caminho):
            arquivos = [f for f in os.listdir(caminho)
                        if os.path.splitext(f)[1].lower() in EXTENSOES_PERMITIDAS]
            quantidade_por_diretoria[diretoria] = len(arquivos)
        else:
            quantidade_por_diretoria[diretoria] = 0

    if busca:
        for diretoria in DIRETORIAS:
            caminho = os.path.join(BASE_DIR, diretoria)
            if not os.path.exists(caminho):
                continue
            arquivos = [f for f in os.listdir(caminho)
                        if busca in f.lower() and os.path.splitext(f)[1].lower() in EXTENSOES_PERMITIDAS]
            for arquivo in arquivos:
                caminho_arquivo = os.path.join(caminho, arquivo)
                timestamp = os.path.getmtime(caminho_arquivo)
                data_modificacao = datetime.fromtimestamp(timestamp)
                resultados.append({
                    'nome': arquivo,
                    'diretoria': diretoria,
                    'data': data_modificacao.strftime('%d/%m/%Y'),
                    'timestamp': timestamp
                })
        resultados.sort(key=lambda x: x['timestamp'], reverse=True)

    return render_template('index.html',
                           diretorias=DIRETORIAS,
                           quantidade_por_diretoria=quantidade_por_diretoria,
                           resultados=resultados,
                           busca=busca)



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
                return f"Erro na conversão do Word para PDF: {e}", 500
        return send_file(caminho_pdf, mimetype='application/pdf')

    elif ext in ['ppt', 'pptx']:
        nome_pdf = f"{arquivo.rsplit('.', 1)[0]}_{diretoria.replace(' ', '_')}.pdf"
        caminho_pdf = os.path.join(TEMP_PDF_FOLDER, nome_pdf)
        if not os.path.exists(caminho_pdf):
            sucesso = converter_para_pdf(caminho_arquivo, caminho_pdf)
            if not sucesso:
                return "Erro na conversão do PowerPoint para PDF", 500
        return send_file(caminho_pdf, mimetype='application/pdf')

    return send_file(caminho_arquivo)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
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
        return redirect(url_for('upload'))

    return render_template('upload.html', diretorias=DIRETORIAS)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

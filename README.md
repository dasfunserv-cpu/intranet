# Intranet

Aplicação de intranet para gerenciamento de documentos desenvolvida em Flask e SQLite.

## Visão geral

Este projeto oferece um portal interno com:
- autenticação de usuários
- controle de permissões e papéis
- upload de documentos
- organização por setores e categorias
- busca e filtros por setor, categoria e tipo de arquivo
- visualização de documentos e miniaturas
- anúncios internos
- administração de usuários, setores, categorias e documentos
- logs de auditoria e acesso

## Tecnologias

- Python
- Flask
- Flask-Login
- SQLAlchemy
- SQLite
- Jinja2

## Dependências

O arquivo `requirements.txt` contém as dependências usadas:

- blinker==1.9.0
- click==8.2.1
- colorama==0.4.6
- docx2pdf==0.1.8
- Flask==3.1.1
- itsdangerous==2.2.0
- Jinja2==3.1.6
- MarkupSafe==3.0.2
- pywin32==310
- tqdm==4.67.1
- Werkzeug==3.1.3

## Instalação

1. Crie e ative o ambiente virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Instale as dependências:

```powershell
pip install -r requirements.txt
```

## Executando a aplicação

Você pode iniciar o projeto com o comando:

```powershell
python run.py
```

Ou use o atalho do Windows:

```powershell
./run_app.bat
```

A aplicação será executada em `http://127.0.0.1:5001`.

## Banco de dados

A aplicação usa SQLite e armazena o arquivo em `app/instance/intranet.db`.

Se você precisar criar as tabelas antes de rodar a aplicação, utilize:

```powershell
python migrate_to_db.py
```

Esse script também tenta migrar dados da pasta `app/recados` para o banco e para a pasta de uploads.

> Observação: o diretório de uploads é `app/uploads`. O aplicativo cria essa pasta automaticamente se ela não existir.

## Estrutura básica

- `run.py`: ponto de entrada da aplicação
- `app/__init__.py`: inicialização do Flask e blueprints
- `config.py`: configurações do app
- `app/models.py`: modelos do banco de dados
- `app/auth`, `app/admin`, `app/documents`: rotas e funcionalidades principais
- `requirements.txt`: lista de dependências

## Nota

Caso queira personalizar a chave secreta ou o banco de dados, edite `config.py`.

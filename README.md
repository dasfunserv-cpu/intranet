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
- microsite gamificado "Semana de Proteção de Dados" (LGPD), com conteúdo diário, quiz e ranking

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

> **Atenção:** o módulo "Semana de Proteção de Dados" (`app/semana_protecao_dados`) usa **PyYAML** para carregar o conteúdo dos arquivos `.yaml`, mas essa biblioteca **não está listada em `requirements.txt`**. Instale manualmente antes de rodar a aplicação:
>
> ```powershell
> pip install pyyaml
> ```

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

## Módulo: Semana de Proteção de Dados

Blueprint independente (`spd`, prefixo de URL `/semana-protecao-dados`), registrado em `app/__init__.py` e acessível pelo menu lateral em `app/templates/base.html`.

Funcionamento:
- **Conteúdo por dia**: os textos, quiz e categorias de cada um dos 5 dias ficam em arquivos YAML (`app/semana_protecao_dados/content/dia1.yaml` a `dia5.yaml`) e `dicas.yaml`, carregados por `content_loader.py` (via **PyYAML**, ver seção Dependências acima).
- **Liberação progressiva (gating)**: `gating.py` controla quais dias estão liberados com base na data atual, entre `INICIO_CAMPANHA` (2026-06-20) e `FIM_CAMPANHA` (2026-07-10). Antes do início, é exibida uma tela de contagem regressiva; após o fim, todos os 5 dias ficam permanentemente disponíveis. Para alterar o período da campanha, edite essas duas constantes.
- **Ranking/quiz**: `ranking.py` recebe as submissões do quiz de cada dia (rota `POST /dia/<n>/ranking`) e persiste o placar em arquivos JSON dentro de `app/semana_protecao_dados/data/` (um por dia, ex.: `ranking_dia1.json`), sem usar o banco de dados principal. Limita 1 registro por IP/dia e mantém apenas o Top 5 na resposta pública (nome, acertos, tempo e data — IP e User-Agent não são expostos).
- **Assets próprios**: CSS, JS e imagens do módulo ficam isolados em `app/semana_protecao_dados/static/`.

> Observação: a pasta `app/semana_protecao_dados/data/` guarda os arquivos JSON de ranking gerados em tempo de execução — não apague o `.gitkeep` nem os `.json` gerados se quiser preservar o histórico do ranking.

## Estrutura básica

- `run.py`: ponto de entrada da aplicação
- `app/__init__.py`: inicialização do Flask e blueprints
- `config.py`: configurações do app
- `app/models.py`: modelos do banco de dados
- `app/auth`, `app/admin`, `app/documents`: rotas e funcionalidades principais
- `app/semana_protecao_dados`: módulo/blueprint da campanha "Semana de Proteção de Dados" (conteúdo, quiz e ranking em LGPD)
- `requirements.txt`: lista de dependências

## Nota

Caso queira personalizar a chave secreta ou o banco de dados, edite `config.py`.

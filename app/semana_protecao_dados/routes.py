from flask import render_template, abort, request, jsonify
from app.semana_protecao_dados import bp
from app.semana_protecao_dados.gating import (
    dias_liberados, dia_disponivel, dias_para_inicio,
    INICIO_CAMPANHA,
)
from app.semana_protecao_dados.content_loader import carregar_dia, carregar_dicas
from app.semana_protecao_dados import ranking as ranking_mod
from .acessos import registrar_acesso


TITULOS_DIAS = {
    1: 'Dado Pessoal',
    2: 'Caça ao Phishing',
    3: 'No dia a dia',
    4: 'Você também é titular',
    5: 'Missão LGPD',
}

    
@bp.route('/')
def index():
    liberados = dias_liberados()

    if liberados == 0:
        return render_template(
            'spd/countdown.html',
            dias_restantes=dias_para_inicio(),
            data_inicio=INICIO_CAMPANHA,
            titulos=TITULOS_DIAS,
        )

    return render_template(
        'spd/index.html',
        liberados=liberados,
        titulos=TITULOS_DIAS,
        dicas=carregar_dicas(),
    )


@bp.route('/dia/<int:n>')
def dia(n):
    if not (1 <= n <= 5):
        abort(404)
    if not dia_disponivel(n):
        abort(403)

    conteudo = carregar_dia(n)
    if conteudo is None:
        abort(404)

    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '0.0.0.0'
    ip = ip.split(',')[0].strip()
    registrar_acesso(f'dia{n}', ip)

    # Template específico por dia, com fallback genérico
    template_especifico = f'spd/dia{n}.html'
    try:
        return render_template(
            template_especifico,
            n=n,
            conteudo=conteudo,
            liberados=dias_liberados(),
            titulos=TITULOS_DIAS,
            ranking=ranking_mod.ranking_publico(n),
        )
    except Exception:
        # Fallback para template genérico se específico não existir
        return render_template(
            'spd/dia.html',
            n=n,
            conteudo=conteudo,
            liberados=dias_liberados(),
            titulos=TITULOS_DIAS,
        )


@bp.route('/dia/<int:n>/ranking', methods=['POST'])
def submeter_ranking(n):
    if not (1 <= n <= 5):
        abort(404)
    if not dia_disponivel(n):
        abort(403)

    dados = request.get_json(silent=True) or {}
    nome = dados.get('nome', '')
    acertos = int(dados.get('acertos', 0))
    tempo_ms = int(dados.get('tempo_ms', 0))

    if acertos < 0 or acertos > 20 or tempo_ms < 0 or tempo_ms > 60 * 60 * 1000:
        return jsonify({'erro': 'Dados inválidos'}), 400

    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '0.0.0.0'
    ip = ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', '')

    resultado = ranking_mod.submeter(n, nome, acertos, tempo_ms, ip, user_agent)
    return jsonify(resultado)

@bp.route('/dia/<int:n>/ranking', methods=['GET'])
def obter_ranking(n):
    if not (1 <= n <= 5):
        abort(404)
    return jsonify({'ranking': ranking_mod.ranking_publico(n)})
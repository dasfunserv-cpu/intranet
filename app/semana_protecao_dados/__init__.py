from flask import Blueprint

bp = Blueprint(
    'spd',
    __name__,
    url_prefix='/semana-protecao-dados',
    template_folder='templates',
    static_folder='static',
)

from app.semana_protecao_dados import routes  # noqa: E402,F401
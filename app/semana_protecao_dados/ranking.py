import json
from pathlib import Path
from datetime import datetime, date
from threading import Lock

DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

TOP_N = 5
_lock = Lock()


def _arquivo(dia: int) -> Path:
    return DATA_DIR / f'ranking_dia{dia}.json'


def carregar(dia: int) -> list[dict]:
    arquivo = _arquivo(dia)
    if not arquivo.exists():
        return []
    with arquivo.open(encoding='utf-8') as f:
        return json.load(f)


def calcular_score(acertos: int, tempo_ms: int) -> int:
    """Quanto maior, melhor. Acertos pesam muito; tempo desempata."""
    tempo_s = tempo_ms / 1000
    return int(acertos * 1000 - tempo_s)


def submeter(dia: int, nome: str, acertos: int, tempo_ms: int,
             ip: str, user_agent: str = '') -> dict:
    """
    Retorna dict com:
      - aceito (bool): se entrou no top
      - posicao (int|None): posição no ranking (1-indexed)
      - score (int)
      - ranking (list): top atual após submissão (sem IP/UA)
    """
    nome = (nome or '').strip()[:20]
    if not nome:
        return {'aceito': False, 'erro': 'Nome vazio', 'ranking': _limpar(carregar(dia))}

    score = calcular_score(acertos, tempo_ms)
    hoje = date.today().isoformat()

    with _lock:
        ranking = carregar(dia)

        # Verifica se já existe entrada desse IP hoje
        entrada_existente = None
        for i, r in enumerate(ranking):
            if r.get('ip') == ip and r.get('data', '').startswith(hoje):
                entrada_existente = i
                break

        nova_entrada = {
            'nome': nome,
            'acertos': acertos,
            'tempo_ms': tempo_ms,
            'score': score,
            'ip': ip,
            'user_agent': user_agent[:200],
            'data': datetime.now().isoformat(timespec='seconds'),
        }

        if entrada_existente is not None:
            # Só substitui se o novo score for melhor
            if score > ranking[entrada_existente]['score']:
                ranking[entrada_existente] = nova_entrada
            else:
                ranking.sort(key=lambda r: r['score'], reverse=True)
                ranking_top = ranking[:TOP_N]
                _salvar(dia, ranking)  # mantém todos no disco, mas top retornado
                return {
                    'aceito': False,
                    'motivo': 'score_inferior',
                    'score': score,
                    'ranking': _limpar(ranking_top),
                }
        else:
            ranking.append(nova_entrada)

        ranking.sort(key=lambda r: r['score'], reverse=True)
        # Mantém todas as entradas no disco, mas só top no retorno
        _salvar(dia, ranking)
        ranking_top = ranking[:TOP_N]

        # Verifica se a entrada nova está no top final
        aceito = any(
            r.get('ip') == ip and r.get('data') == nova_entrada['data']
            for r in ranking_top
        )
        posicao = None
        for i, r in enumerate(ranking_top):
            if r.get('ip') == ip and r.get('data') == nova_entrada['data']:
                posicao = i + 1
                break

        return {
            'aceito': aceito,
            'posicao': posicao,
            'score': score,
            'ranking': _limpar(ranking_top),
        }


def _salvar(dia: int, ranking: list[dict]):
    with _arquivo(dia).open('w', encoding='utf-8') as f:
        json.dump(ranking, f, ensure_ascii=False, indent=2)


def _limpar(ranking: list[dict]) -> list[dict]:
    """Remove IP e User-Agent antes de mandar pro cliente."""
    campos_publicos = {'nome', 'acertos', 'tempo_ms', 'score', 'data'}
    return [
        {k: v for k, v in r.items() if k in campos_publicos}
        for r in ranking
    ]


def ranking_publico(dia: int) -> list[dict]:
    """Retorna só o Top N, sem IP nem User-Agent."""
    ranking = carregar(dia)
    ranking.sort(key=lambda r: r['score'], reverse=True)
    return _limpar(ranking[:TOP_N])
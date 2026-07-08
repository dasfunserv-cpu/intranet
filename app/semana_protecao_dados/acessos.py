import json
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timedelta
from flask import current_app

_lock = threading.Lock()

ACESSOS_PATH = Path(__file__).parent / "data" / "acessos.json"

DIAS_VALIDOS = {"dia1", "dia2", "dia3", "dia4", "dia5"}
JANELA_DEDUP = timedelta(hours=2)

# Cache só em memória — nunca vai para o disco.
# Some ao reiniciar o processo (efeito colateral aceitável: após um
# restart, o próximo acesso de cada IP conta de novo).
_cache_visitas = {dia: {} for dia in DIAS_VALIDOS}


def _carregar_contadores():
    if not ACESSOS_PATH.exists():
        return {dia: 0 for dia in DIAS_VALIDOS}
    with open(ACESSOS_PATH, "r", encoding="utf-8") as f:
        dados = json.load(f)
    for dia in DIAS_VALIDOS:
        dados.setdefault(dia, 0)
    return dados


def _salvar_contadores(contadores: dict):
    ACESSOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ACESSOS_PATH, "w", encoding="utf-8") as f:
        json.dump(contadores, f, ensure_ascii=False, indent=2)


def _hash_ip(ip: str) -> str:
    salt = current_app.config.get("SECRET_KEY", "spd-fallback-salt")
    return hashlib.sha256(f"{salt}:{ip}".encode("utf-8")).hexdigest()


def registrar_acesso(dia: str, ip: str) -> None:
    """Incrementa o contador do dia, no máximo 1x por IP a cada 2h.
    A checagem de IP fica só em memória; o arquivo guarda apenas o total."""
    if dia not in DIAS_VALIDOS:
        return

    ip_hash = _hash_ip(ip)
    agora = datetime.utcnow()

    with _lock:
        visitas_dia = _cache_visitas.setdefault(dia, {})

        # Limpa hashes expirados da memória
        _cache_visitas[dia] = {
            h: ts for h, ts in visitas_dia.items()
            if agora - ts < JANELA_DEDUP
        }
        visitas_dia = _cache_visitas[dia]

        ja_contado = ip_hash in visitas_dia
        visitas_dia[ip_hash] = agora

        if not ja_contado:
            contadores = _carregar_contadores()
            contadores[dia] += 1
            _salvar_contadores(contadores)


def obter_acessos() -> dict:
    return _carregar_contadores()
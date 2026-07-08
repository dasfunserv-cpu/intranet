from pathlib import Path
import yaml

CONTENT_DIR = Path(__file__).parent / 'content'


def carregar_dia(n: int) -> dict | None:
    arquivo = CONTENT_DIR / f'dia{n}.yaml'
    if not arquivo.exists():
        return None
    with arquivo.open(encoding='utf-8') as f:
        return yaml.safe_load(f)


def carregar_dicas() -> list[dict]:
    arquivo = CONTENT_DIR / 'dicas.yaml'
    if not arquivo.exists():
        return []
    with arquivo.open(encoding='utf-8') as f:
        return yaml.safe_load(f) or []
from datetime import date

# Campanha: 13 a 17 de julho de 2026 (segunda a sexta)
INICIO_CAMPANHA = date(2026, 6, 20)
FIM_CAMPANHA = date(2026, 7, 10)


def dias_liberados(hoje: date | None = None) -> int:
    """
    Retorna quantos dias estão liberados na data informada.
    - Antes de 13/jul: 0 (mostra countdown)
    - 13/jul (seg): 1
    - 14/jul (ter): 2
    - 15/jul (qua): 3
    - 16/jul (qui): 4
    - 17/jul (sex) em diante: 5 (permanente)
    """
    hoje = hoje or date.today()

    if hoje < INICIO_CAMPANHA:
        return 0
    if hoje >= FIM_CAMPANHA:
        return 5

    delta = (hoje - INICIO_CAMPANHA).days
    return delta + 1


def dia_disponivel(n: int, hoje: date | None = None) -> bool:
    return 1 <= n <= dias_liberados(hoje)


def dias_para_inicio(hoje: date | None = None) -> int:
    hoje = hoje or date.today()
    return max(0, (INICIO_CAMPANHA - hoje).days)
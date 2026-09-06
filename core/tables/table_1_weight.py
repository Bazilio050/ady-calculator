# ------------------------------------------------------------------------------
# БЛОК 1: Логика Таблицы 1 (Cədvəl 1) — Округление веса
# ------------------------------------------------------------------------------

def calculate_billable_weight(weight_tons: int) -> dict:
    """
    Рассчитывает расчетную категорию веса по Таблице 1.
    Возвращает словарь с расчетным весом и кодом правила для примечаний.
    """
    w = int(weight_tons)
    calc_w = w

    if w <= 12:
        calc_w = 10
    elif w <= 16:
        calc_w = 15
    elif w <= 23:
        calc_w = 20
    elif w <= 26:
        calc_w = 25
    elif w <= 31:
        calc_w = 30
    elif w <= 36:
        calc_w = 35
    elif w <= 40:
        calc_w = 40
    elif w <= 46:
        calc_w = 45
    elif w <= 51:
        calc_w = 50
    elif w <= 55:
        calc_w = 55
    elif w <= 60:
        calc_w = 60
    else:
        calc_w = w

    # Если фактический вес округлился, передаем системный ключ правила
    rule_code = "TABLE_1_ROUNDING" if calc_w != w else None

    return {
        "calculated_weight": calc_w,
        "rule_code": rule_code,
        "params": {"actual": w, "applied": calc_w} if rule_code else {}
    }

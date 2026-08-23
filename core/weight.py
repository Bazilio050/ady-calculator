# ==============================================================================
# МОДУЛЬ РАСЧЕТА ВЕСА ADY 2026 (Cədvəl 1)
# ==============================================================================
import math

def get_weight_category_cadvel_1(actual_weight: float) -> int:
    """
    Определяет категорию веса по Cədvəl 1 (стр. 9) для выбора колонки в таблицах 3 и 4.
    """
    w = float(actual_weight or 0)
    
    if w <= 12:
        return 10
    elif w <= 16:
        return 15
    elif w <= 23:
        return 20
    elif w <= 26:
        return 25
    elif w <= 31:
        return 30
    elif w <= 36:
        return 35
    elif w <= 40:
        return 40
    elif w <= 46:
        return 45
    elif w <= 51:
        return 50
    elif w <= 55:
        return 55
    else:
        return 60

def calculate_chargeable_weight(fact_weight: float, min_gng_norm: float = 0.0) -> dict:
    """
    Рассчитывает округленный оплачиваемый вес с учетом минимальной нормы по ГНГ.
    """
    # 1. Сравнение фактического веса и нормы ГНГ
    effective_weight = max(float(fact_weight or 0), float(min_gng_norm or 0))
    
    # 2. Округление до целых тонн в большую сторону
    chargeable_tons = math.ceil(effective_weight)
    
    # 3. Категория по Таблице 1
    weight_category = get_weight_category_cadvel_1(chargeable_tons)

    return {
        "fact_weight": fact_weight,
        "min_gng_norm": min_gng_norm,
        "chargeable_tons": chargeable_tons,
        "weight_category": weight_category
    }

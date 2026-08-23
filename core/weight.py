# ==============================================================================
# МОДУЛЬ РАСЧЕТА ВЕСА И ВЕСОВЫХ КАТЕГОРИЙ ADY 2026
# ==============================================================================
import math
import re

def calculate_chargeable_weight(
    fact_weight: float, 
    gng_code: str = "", 
    wagon_type: str = "", 
    transporter_axles: int = 0
) -> dict:
    """
    Рассчитывает расчетный вес и весовую категорию с учетом правил ADY 2026.
    """
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    w_type = str(wagon_type or "").strip().lower()

    # 1. Почта / Пассажирские вагоны (п. 3.1.2.5) -> фиксировано 66 тонн
    if clean_gng == "99910000" or "passenger" in w_type or "пассажир" in w_type:
        return {"chargeable_tons": 66, "weight_category": 25}

    # 2. Транспортеры 4, 6, 8 осей (п. 3.1.2.6) -> минимум 5 тонн на ось
    if transporter_axles in [4, 6, 8]:
        min_weight = transporter_axles * 5
        chargeable = math.ceil(max(fact_weight, min_weight))
        return {"chargeable_tons": chargeable, "weight_category": 60}

    # 3. Базовый расчет веса (округление в большую сторону до целых тонн)
    min_norm = 10  # По умолчанию минимальная норма
    chargeable_tons = math.ceil(max(fact_weight, min_norm))

    # Определение весовой категории по Cədvəl 1 (10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60 тонн)
    categories = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
    weight_category = 60
    for c in categories:
        if chargeable_tons <= c:
            weight_category = c
            break

    return {
        "chargeable_tons": chargeable_tons,
        "weight_category": weight_category
    }

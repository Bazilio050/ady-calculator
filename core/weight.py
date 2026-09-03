# ==============================================================================
# МОДУЛЬ РАСЧЕТА ВЕСОВЫХ ПАРАМЕТРОВ (CORE WEIGHT ENGINE)
# ==============================================================================
import re
import math
from data.translations import format_weight_string


# ------------------------------------------------------------------------------
# БЛОК 1: Определение минимальной нормы загрузки по ГНГ (стр. 11-12)
# ------------------------------------------------------------------------------
def get_min_loading_norm(gng_code) -> int:
    """
    Возвращает минимальную норму загрузки согласно Тарифной политике ADY (стр. 11-12).
    Применяется СТРОГО по коду ГНГ независимо от типа вагона.
    """
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    
    if not clean_gng:
        return 0

    if clean_gng.startswith("10"):
        return 60
    if any(clean_gng.startswith(p) for p in ["4403", "4404", "4407"]):
        return 45
    if clean_gng.startswith("72") and not clean_gng.startswith("7204"):
        return 60
    if clean_gng.startswith("31") and not clean_gng.startswith("3101"):
        return 60
    if any(clean_gng.startswith(p) for p in ["2701", "2702", "7201", "1701", "1101", "1102", "1103", "1107"]):
        return 60
    if any(clean_gng.startswith(p) for p in ["14042", "5201", "5202", "5203", "7204"]):
        return 50

    return 0


# ------------------------------------------------------------------------------
# БЛОК 2: Расчет расчетного веса и весовой категории (Cədvəl 1, стр. 9)
# ------------------------------------------------------------------------------
def calculate_chargeable_weight(
    fact_weight: float, 
    gng_code = "", 
    wagon_type: str = ""
) -> dict:
    w_type = str(wagon_type or "").strip().lower()
    fact_w = float(fact_weight or 0.0)

    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    if clean_gng == "99910000" or "passenger" in w_type or "пассажир" in w_type:
        return {"chargeable_tons": 66, "min_weight_norm": 66, "weight_category": 25}

    if w_type in ["autocar", "two_tier_car_platform"]:
        chargeable_tons = math.ceil(fact_w) if fact_w > 0 else 0
        return {"chargeable_tons": chargeable_tons, "min_weight_norm": 0, "weight_category": 10}

    min_norm = get_min_loading_norm(gng_code)
    
    if min_norm > 0:
        chargeable_tons = math.ceil(max(fact_w, min_norm))
    else:
        chargeable_tons = math.ceil(fact_w)

    if chargeable_tons <= 12:
        weight_category = 10
    elif chargeable_tons <= 16:
        weight_category = 15
    elif chargeable_tons <= 23:
        weight_category = 20
    elif chargeable_tons <= 26:
        weight_category = 25
    elif chargeable_tons <= 31:
        weight_category = 30
    elif chargeable_tons <= 36:
        weight_category = 35
    elif chargeable_tons <= 40:
        weight_category = 40
    elif chargeable_tons <= 46:
        weight_category = 45
    elif chargeable_tons <= 51:
        weight_category = 50
    elif chargeable_tons <= 55:
        weight_category = 55
    else:
        weight_category = 60

    return {
        "chargeable_tons": chargeable_tons,
        "min_weight_norm": min_norm,
        "weight_category": weight_category
    }


# ------------------------------------------------------------------------------
# БЛОК 3: Форматирование параметров веса через модуль data/translations.py
# ------------------------------------------------------------------------------
def get_weight_display_info(
    fact_weight: float, 
    gng_code: str = "", 
    wagon_type: str = "",
    lang: str = "AZ"
) -> dict:
    calc = calculate_chargeable_weight(fact_weight, gng_code, wagon_type)
    
    fact_w = float(fact_weight or 0.0)
    chargeable = calc["chargeable_tons"]
    min_norm = calc["min_weight_norm"]
    
    weight_info_str = format_weight_string(fact_w, chargeable, min_norm, lang=lang)

    return {
        "fact_weight": fact_w,
        "chargeable_tons": chargeable,
        "min_weight_norm": min_norm,
        "weight_category": calc["weight_category"],
        "weight_info_str": weight_info_str
    }

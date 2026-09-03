# ==============================================================================
# МОДУЛЬ РАСЧЕТА ВЕСА И ВЕСОВЫХ КАТЕГОРИЙ ADY 2026 (СТР. 9, 11, 12)
# ==============================================================================
import math
import re

# ------------------------------------------------------------------------------
# БЛОК 1: Определение минимальной нормы загрузки по Таблице (стр. 11-12)
# ------------------------------------------------------------------------------
def get_min_loading_norm(gng_code) -> int:
    """
    Возвращает минимальную норму загрузки согласно Тарифной политике ADY (стр. 11-12).
    """
    # Гарантируем преобразование в строку независимо от того, пришел int или str
    clean_gng = re.sub(r'\D', '', str(gng_code if gng_code is not None else ""))
    
    if not clean_gng:
        return 0

    # 1. Зерновая группа (ГНГ 1001, 1002, 1005 и т.д.) — СТРОГО 60 тонн
    if clean_gng.startswith("10"):
        return 60

    # 2. Лесоматериалы (4403, 4404, 4407) — 45 тонн
    if any(clean_gng.startswith(p) for p in ["4403", "4404", "4407"]):
        return 45

    # 3. Черные металлы (Группа 72, кроме лома 7204) — 60 тонн
    if clean_gng.startswith("72") and not clean_gng.startswith("7204"):
        return 60

    # 4. Минеральные удобрения (Группа 31, кроме 3101) — 60 тонн
    if clean_gng.startswith("31") and not clean_gng.startswith("3101"):
        return 60

    # 5. Уголь, Руда, Сахар, Мука — 60 тонн
    if any(clean_gng.startswith(p) for p in ["2701", "2702", "7201", "1701", "1101", "1102", "1103", "1107"]):
        return 60

    # 6. Хлопок, Лом черных металлов — 50 тонн
    if any(clean_gng.startswith(p) for p in ["14042", "5201", "5202", "5203", "7204"]):
        return 50

    return 0


# ------------------------------------------------------------------------------
# БЛОК 2: Расчет расчетного веса и категории по Cədvəl 1 (без транспортеров)
# ------------------------------------------------------------------------------
def calculate_chargeable_weight(
    fact_weight: float, 
    gng_code = "", 
    wagon_type: str = ""
) -> dict:
    w_type = str(wagon_type or "").strip().lower()
    fact_w = float(fact_weight or 0.0)

    # 1. Почтово-пассажирские вагоны -> 66 тонн
    clean_gng = re.sub(r'\D', '', str(gng_code if gng_code is not None else ""))
    if clean_gng == "99910000" or "passenger" in w_type or "пассажир" in w_type:
        return {"chargeable_tons": 66, "min_weight_norm": 66, "weight_category": 25}

    # 2. Автовозы
    if w_type in ["autocar", "two_tier_car_platform"]:
        chargeable_tons = math.ceil(fact_w) if fact_w > 0 else 0
        return {"chargeable_tons": chargeable_tons, "min_weight_norm": 0, "weight_category": 10}

    # 3. Проверка минимальной нормы по ГНГ (стр. 11-12)
    min_norm = get_min_loading_norm(gng_code)
    
    if min_norm > 0:
        chargeable_tons = math.ceil(max(fact_w, min_norm))
    else:
        chargeable_tons = math.ceil(fact_w)

    # 4. Определение весовой категории (Cədvəl 1, стр. 9)
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
# БЛОК 3: Форматирование параметров веса для интерфейса (UI)
# ------------------------------------------------------------------------------
def get_weight_display_info(
    fact_weight: float, 
    gng_code: str = "", 
    wagon_type: str = ""
) -> dict:
    """
    Возвращает структуру данных веса и отформатированную строку для UI.
    """
    calc = calculate_chargeable_weight(fact_weight, gng_code, wagon_type)
    
    fact_w = float(fact_weight or 0.0)
    chargeable = calc["chargeable_tons"]
    min_norm = calc["min_weight_norm"]
    
    # Формирование строки доначисления до минимальной нормы
    if min_norm > 0 and fact_w < min_norm:
        weight_info_str = f"{fact_w:.1f} т (расчетный: {chargeable:.1f} т)"
    else:
        weight_info_str = f"{fact_w:.1f} т" if fact_w > 0 else f"{chargeable:.1f} т"

    return {
        "fact_weight": fact_w,
        "chargeable_tons": chargeable,
        "min_weight_norm": min_norm,
        "weight_category": calc["weight_category"],
        "weight_info_str": weight_info_str
    }

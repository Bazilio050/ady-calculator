# ==============================================================================
# МОДУЛЬ РАСЧЕТА ВЕСА И ВЕСОВЫХ КАТЕГОРИЙ ADY 2026 (СТР. 9, 11, 12)
# ==============================================================================
import math
import re

def get_min_loading_norm(gng_code: str) -> int:
    """
    Возвращает минимальную норму загрузки по таблице со стр. 11-12.
    Если кода нет в списке, возвращает 0 (норма не применяется).
    """
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    if not clean_gng:
        return 0

    # 45 тонн — Лесоматериалы (4403, 4404, 4407)
    if any(clean_gng.startswith(prefix) for prefix in ["4403", "4404", "4407"]):
        return 45

    # 60 тонн — Уголь, Руда, Чугун, Удобрения, Сахар, Мука, Зерно, Черные металлы
    if any(clean_gng.startswith(prefix) for prefix in [
        "2701", "2702", "7201", "1701", "1101", "1102", "1103", "10", "1107"
    ]):
        return 60
    if clean_gng.startswith("72") and not clean_gng.startswith("7204"):
        return 60
    if clean_gng.startswith("31") and not clean_gng.startswith("3101"):
        return 60

    # 50 тонн — Хлопок, Лом черных металлов
    if any(clean_gng.startswith(prefix) for prefix in ["14042", "5201", "5202", "5203", "7204"]):
        return 50

    # Специальные группы со стр. 12
    norm_50_codes = ["32121", "71101910", "7407", "7408", "7409", "7410", "7413", "7505", "7506", "7804", "78060080", "81019600", "81029600", "81032", "81039010"]
    if any(clean_gng.startswith(c) for c in norm_50_codes):
        return 50

    norm_40_codes = ["7404", "7503", "7602", "7802", "7902", "7903", "8002", "81019700", "81029700", "81033000", "81053", "81073", "81083", "81093", "81102", "85481", "85493", "85499"]
    if any(clean_gng.startswith(c) for c in norm_40_codes):
        return 40

    norm_30_codes = ["71159", "7411", "7412", "7415", "7419", "7507", "7508", "7608", "7613", "76152", "7616", "7806", "7907", "8007", "81059", "81060090", "81079", "81089", "81099", "81109", "8302", "83061", "83079", "8309", "8311", "8481", "8482", "8484"]
    if any(clean_gng.startswith(c) for c in norm_30_codes):
        return 30

    return 0

def calculate_chargeable_weight(
    fact_weight: float, 
    gng_code: str = "", 
    wagon_type: str = "", 
    transporter_axles: int = 0
) -> dict:
    """
    Рассчитывает расчетный вес и категорию по Таблице 1 (Cədvəl 1, стр. 9).
    """
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    w_type = str(wagon_type or "").strip().lower()
    fact_w = float(fact_weight or 0.0)

    # 1. Почта / Пассажирские вагоны -> фиксировано 66 тонн
    if clean_gng == "99910000" or "passenger" in w_type or "пассажир" in w_type:
        return {"chargeable_tons": 66, "min_weight_norm": 66, "weight_category": 25}

    # 2. Транспортеры -> минимум 5 тонн на ось
    if transporter_axles in [4, 6, 8]:
        min_norm = transporter_axles * 5
        chargeable = math.ceil(max(fact_w, min_norm))
        return {"chargeable_tons": chargeable, "min_weight_norm": min_norm, "weight_category": 60}

    # 3. Проверка минимальной нормы по списку со стр. 11-12
    min_norm = get_min_loading_norm(clean_gng)
    
    if min_norm > 0:
        chargeable_tons = math.ceil(max(fact_w, min_norm))
    else:
        chargeable_tons = math.ceil(fact_w)

    # 4. Определение весовой категории строго по Cədvəl 1 (стр. 9)
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

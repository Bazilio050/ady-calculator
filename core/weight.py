# ==============================================================================
# МОДУЛЬ РАСЧЕТА ВЕСА ADY 2026 (Cədvəl 1 и Страницы 11-12)
# ==============================================================================
import math
import re

def get_min_loading_norm(gng_code: str) -> float:
    """
    Определяет минимальную норму загрузки вагона (в тоннах) по коду ГНГ (YHN) 
    согласно таблице на стр. 11-12 руководства ADY 2026.
    """
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    if not clean_gng:
        return 0.0

    # 1. Специфические группы со стр. 11
    if clean_gng.startswith(("2701", "2702")):  # Каменный уголь
        return 60.0
    if clean_gng.startswith(("4403", "4404", "4407")):  # Лесоматериалы
        return 45.0
    if clean_gng.startswith("7201"):  # Чугун
        return 60.0
    if clean_gng.startswith("31") and not clean_gng.startswith("3101"):  # Удобрения
        return 60.0
    if clean_gng.startswith("1701"):  # Сахар
        return 60.0
    if clean_gng.startswith(("1101", "1102", "1103")):  # Мука
        return 60.0
    if clean_gng.startswith(("10", "1107")):  # Зерновые
        return 60.0
    if clean_gng.startswith(("14042", "5201", "5202", "5203")):  # Хлопок
        return 50.0
    if clean_gng.startswith("7204") and not clean_gng.startswith("72045"):  # Лом черных металлов
        return 50.0
    if clean_gng.startswith("72"):  # Черные металлы
        return 60.0
    if clean_gng.startswith("26") and not clean_gng.startswith(("2618", "2619", "2620", "2621")):  # Руды
        return 60.0
    if clean_gng.startswith(("7203", "7401", "7501", "81052", "28182000")):
        return 60.0

    # 2. Цветные металлы и редкие группы (стр. 11-12)
    # Норма 30 тонн (стр. 12)
    if clean_gng.startswith(("71159", "7411", "7412", "7415", "7419", "7507", "7508", "7608", "7613", "76152", "7616")):
        return 30.0

    # Норма 40 тонн (стр. 12)
    if clean_gng.startswith(("7404", "7503", "7602", "7802", "7902", "7903")):
        return 40.0

    # Норма 50 тонн (стр. 12)
    if clean_gng.startswith(("32121", "71101910", "7407", "7408", "7409", "7410", "7413", "7505", "7506", "7604", "7605", "7606", "7607", "76149", "7804")):
        return 50.0

    # Базовая норма для большинства прочих металлов (стр. 11)
    if clean_gng.startswith(("280450", "28049", "28053", "28054", "7106", "7107", "7108", "7109", "7110", "7402", "7403", "7405", "7406", "7502", "7504", "7601", "7603", "7801", "78042", "7901")):
        return 60.0

    # По умолчанию если не входит в таблицы минимальных норм
    return 0.0


def get_weight_category_cadvel_1(actual_weight: float) -> int:
    """
    Определяет категорию веса по Cədvəl 1 (стр. 9) для выбора колонки.
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


def calculate_chargeable_weight(fact_weight: float, gng_code: str = "") -> dict:
    """
    Рассчитывает финальный расчетный вес с учетом минимальной нормы по ГНГ и округления.
    """
    fact_w = float(fact_weight or 0)
    min_norm = get_min_loading_norm(gng_code)
    
    # Расчетный вес = МАКСИМУМ из фактического веса и минимальной нормы
    effective_weight = max(fact_w, min_norm)
    
    # Округление до целых тонн в большую сторону
    chargeable_tons = math.ceil(effective_weight)
    
    # Определение категории по Cədvəl 1
    weight_category = get_weight_category_cadvel_1(chargeable_tons)

    return {
        "fact_weight": fact_w,
        "min_gng_norm": min_norm,
        "chargeable_tons": chargeable_tons,
        "weight_category": weight_category
    }

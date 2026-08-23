# ==============================================================================
# МОДУЛЬ 2: РАСЧЕТ ОПЛАЧИВАЕМОГО ВЕСА И ПРИМЕНЕНИЕ МИНИМАЛЬНЫХ НОРМ
# ==============================================================================
import math
from utils import get_min_weight_by_gng  # Точный импорт из utils.py

def calculate_chargeable_weight(nlu_data: dict, clean_gng: str) -> dict:
    """
    Рассчитывает фактический и оплачиваемый (расчетный) вес на основе 
    минимальных норм загрузки из utils.py.
    """
    # 1. Получаем фактический вес (по умолчанию 60 тонн, если не указан)
    fact_weight = float(nlu_data.get("weight_tons") or 60.0)
    
    # 2. Вычисляем расчетный вес через функцию utils.py
    chargeable_weight = get_min_weight_by_gng(clean_gng, fact_weight)

    # 3. Округление до целых тонн в большую сторону по правилам ADY
    chargeable_weight_rounded = math.ceil(chargeable_weight)

    return {
        "fact_weight": fact_weight,
        "min_norm": None,
        "chargeable_weight": chargeable_weight_rounded
    }

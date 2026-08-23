# ==============================================================================
# МОДУЛЬ 2: РАСЧЕТ ОПЛАЧИВАЕМОГО ВЕСА И ПРИМЕНЕНИЕ МИНИМАЛЬНЫХ НОРМ
# ==============================================================================
import math
from utils import get_min_tonnage_for_gng  # Функция чтения норм из справочника

def calculate_chargeable_weight(nlu_data: dict, clean_gng: str) -> dict:
    """
    Рассчитывает фактический и оплачиваемый (расчетный) вес на основе 
    минимальных норм загрузки из справочника.
    """
    # 1. Получаем фактический вес (по умолчанию 60 тонн, если не указан)
    fact_weight = float(nlu_data.get("weight_tons") or 60.0)
    
    # 2. Получаем минимальную норму загрузки для данного ГНГ из справочника
    min_norm = get_min_tonnage_for_gng(clean_gng)
    
    # 3. Расчетный вес = МАКСИМУМ из фактического веса и минимальной нормы
    if min_norm is not None and min_norm > 0:
        chargeable_weight = max(fact_weight, float(min_norm))
    else:
        chargeable_weight = fact_weight

    # 4. Округление до целых тонн в большую сторону по правилам ADY
    chargeable_weight_rounded = math.ceil(chargeable_weight)

    return {
        "fact_weight": fact_weight,
        "min_norm": min_norm,
        "chargeable_weight": chargeable_weight_rounded
    }

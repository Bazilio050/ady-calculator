# ==============================================================================
# МОДУЛЬ 1: ОПРЕДЕЛЕНИЕ РЕЖИМА И РАСЧЕТНОГО РАССТОЯНИЯ (ЧИСТАЯ ВЕРСИЯ)
# ==============================================================================
import re
from utils import (
    get_distance_by_esr,
    get_calculation_distance,
    is_border_esr
)

def determine_shipment_mode(nlu_data: dict, origin_esr: str, dest_esr: str) -> str:
    """Определяет режим перевозки: import, export или transit."""
    explicit_mode = nlu_data.get("explicit_mode")
    if explicit_mode in ["import", "export", "transit"]:
        return explicit_mode
    
    if is_border_esr(origin_esr) and is_border_esr(dest_esr):
        return "transit"
    elif is_border_esr(origin_esr):
        return "import"
    elif is_border_esr(dest_esr):
        return "export"
    
    return "import"

def calculate_route_distances(nlu_data: dict, user_input_raw: str, origin_esr: str, dest_esr: str, shipment_mode: str) -> tuple[int, int]:
    """Возвращает тупл: (actual_dist_km, tariff_dist_km)."""
    input_lower = user_input_raw.lower()
    explicit_dist = nlu_data.get("distance_km") or nlu_data.get("actual_dist_km")
    
    if not explicit_dist and user_input_raw:
        m = re.search(r'(\d+)\s*(?:km|км)', input_lower)
        if m:
            explicit_dist = int(m.group(1))

    raw_dist = get_distance_by_esr(origin_esr, dest_esr)
    actual_dist_km = int(explicit_dist) if explicit_dist else (raw_dist or 204)

    # Официальное расчётное тарифное расстояние ADY
    tariff_dist_km = get_calculation_distance(actual_dist_km, shipment_mode)

    return actual_dist_km, tariff_dist_km

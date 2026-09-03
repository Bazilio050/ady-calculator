# ==============================================================================
# МОДУЛЬ ОПРЕДЕЛЕНИЯ МАРШРУТА И РАСЧЕТНОГО РАССТОЯНИЯ ADY 2026 (Стр. 13)
# ==============================================================================

def calculate_tariff_distance(fact_distance_km: int, shipment_type: str) -> dict:
    """
    Рассчитывает финальное тарифное расстояние с учетом минимальных порогов (стр. 13):
    - Экспорт (İxrac) = минимум 101 км
    - Импорт (İdxal) = минимум 151 км
    - Транзит (Tranzit) = фактическое расстояние
    """
    mode = str(shipment_type or "").strip().lower()
    fact_dist = max(0, int(fact_distance_km or 0))
    
    is_export = any(k in mode for k in ["ixrac", "export", "экспорт"])
    is_import = any(k in mode for k in ["idxal", "import", "импорт"])
    
    applied_min_km = 0
    calculated_dist = fact_dist

    if is_export:
        applied_min_km = 101
        calculated_dist = max(fact_dist, 101)
    elif is_import:
        applied_min_km = 151
        calculated_dist = max(fact_dist, 151)

    return {
        "fact_distance_km": fact_dist,
        "calculated_distance_km": calculated_dist,
        "applied_min_threshold_km": applied_min_km,
        "shipment_mode": "export" if is_export else ("import" if is_import else "transit")
    }


def get_route_and_distance(
    from_station: str = "",
    to_station: str = "",
    shipment_type: str = "transit",
    override_distance: int = None
) -> dict:
    """
    Вспомогательный хелпер для расчетных модулей.
    """
    fact_dist = override_distance if override_distance is not None else 680
    dist_info = calculate_tariff_distance(fact_dist, shipment_type)
    
    return {
        "from_station": from_station,
        "to_station": to_station,
        "fact_distance": dist_info["fact_distance_km"],
        "chargeable_distance": dist_info["calculated_distance_km"],
        "shipment_mode": dist_info["shipment_mode"]
    }

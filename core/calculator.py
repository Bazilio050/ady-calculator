# ==============================================================================
# ГЛАВНЫЙ МОДУЛЬ РАСЧЕТА ТАРИФОВ ADY 2026 (Таблицы 3 и 4)
# ==============================================================================
from core.weight import calculate_chargeable_weight
from core.route import calculate_tariff_distance
from core.table_selector import select_tariff_table
from core.table_parser import get_base_rate_from_table
from core.coefficients import get_applicable_coefficients
from core.currency import get_chf_usd_rate

def calculate_freight(
    fact_weight: float,
    gng_code: str,
    shipment_type: str,
    wagon_type: str = "universal",
    from_station: str = "",
    to_station: str = "",
    manual_distance_km: int = 0,
    calculation_date: str = None,
    is_empty_inventory: bool = False,
    is_private_wagon: bool = True,
    data_dir: str = "data"
) -> dict:
    """
    Главная функция расчета стоимости перевозки ADY 2026 с выводом результатов в USD за 1 тн.
    Формула: (CHF_rate / FX) * coeff * 1.015 * 0.85
    """
    # 1. Порожний возврат инвентарного парка
    if is_empty_inventory:
        return {
            "rate_usd_per_ton": 0.0,
            "total_usd": 0.0,
            "details": "Порожний возврат инвентарного парка (0 USD)"
        }

    # 2. Определение курса валюты на выбранную дату (или текущую по умолчанию)
    fx_rate = get_chf_usd_rate(calculation_date)

    # 3. Определение расстояния
    if manual_distance_km > 0:
        raw_distance = manual_distance_km
    else:
        from core.distance_finder import get_distance_between_stations
        raw_distance = get_distance_between_stations(from_station, to_station, data_dir)

    route_info = calculate_tariff_distance(raw_distance, shipment_type)
    calc_distance = route_info["calculated_distance_km"]

    # 4. Определение расчетного веса и категории
    weight_info = calculate_chargeable_weight(fact_weight, gng_code)
    chargeable_tons = weight_info["chargeable_tons"]
    weight_category = weight_info["weight_category"]

    # 5. Выбор тарифной таблицы (3 или 4)
    table_num = select_tariff_table(wagon_type, shipment_type, is_empty_inventory)

    # 6. Поиск базовой ставки (CHF/тонна)
    base_rate_chf = get_base_rate_from_table(table_num, calc_distance, weight_category, data_dir)

    # 7. Расчет всех коэффициентов (включая 1.015 для груженого и 0.85 для приватов)
    coeff_info = get_applicable_coefficients(
        shipment_type=shipment_type,
        gng_code=gng_code,
        table_number=table_num,
        wagon_type=wagon_type,
        from_station=from_station,
        to_station=to_station,
        is_loaded=True,
        is_private_wagon=is_private_wagon
    )
    total_multiplier = coeff_info["total_multiplier"]

    # 8. Итоговый расчет ставок в USD за 1 тонну
    # Базовая ставка переведенная в USD: CHF / FX
    base_rate_usd_per_ton = base_rate_chf / fx_rate

    # Финальная ставка в USD за 1 тонну со всеми коэффициентами
    rate_usd_per_ton = base_rate_usd_per_ton * total_multiplier

    # Общая стоимость на весь расчетный вес в USD
    total_usd = rate_usd_per_ton * chargeable_tons

    return {
        "base_rate_chf_per_ton": base_rate_chf,
        "fx_rate_used": fx_rate,
        "base_rate_usd_per_ton": round(base_rate_usd_per_ton, 3),
        "rate_usd_per_ton": round(rate_usd_per_ton, 2),
        "chargeable_tons": chargeable_tons,
        "weight_category": weight_category,
        "calculated_distance_km": calc_distance,
        "table_used": table_num,
        "coefficients": coeff_info["coefficients_list"],
        "total_multiplier": total_multiplier,
        "total_usd": round(total_usd, 2)
    }

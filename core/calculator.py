# ==============================================================================
# ГЛАВНЫЙ МОДУЛЬ РАСЧЕТА ТАРИФНЫХ СТАВОК ADY 2026
# ==============================================================================
import re
from core.weight import calculate_chargeable_weight
from core.route import calculate_tariff_distance
from core.table_selector import select_tariff_table
from core.table_parser import get_base_rate_from_table
from core.coefficients import get_applicable_coefficients
from core.currency import get_chf_usd_rate
from datetime import datetime

def calculate_freight(
    from_station,
    to_station,
    gng_code=None,
    fact_weight=0.0,
    wagon_type="universal",
    shipment_type="import",
    is_empty_wagon=False,
    is_private_wagon=True,
    is_round_trip=False,
    wagon_axles=4,
    manual_distance_km=None
    calculation_date=None,  # <-- Помещаем в параметры со значением по умолчанию
    **kwargs                 # <-- Принимает любые дополнительные поля (origin_country, gng_name)
):
    # Логика даты должна находиться ВНУТРИ функции:
    if not calculation_date:
        calculation_date = datetime.now().strftime("%Y-%m-%d")
  
    fx_rate = get_chf_usd_rate(calculation_date)

    # 1. Определение расстояния
    if manual_distance_km > 0:
        raw_distance = manual_distance_km
    else:
        from core.distance_finder import get_distance_between_stations
        raw_distance = get_distance_between_stations(from_station, to_station, data_dir)

    route_info = calculate_tariff_distance(raw_distance, shipment_type)
    calc_distance = route_info["calculated_distance_km"]

    # 2. Порожний пробег приватного вагона (п. 3.2.2: 0.10 CHF за ось-км)
    if is_empty_wagon:
        clean_gng = re.sub(r'\D', '', str(gng_code or "")) if gng_code else "99220000"
        axles = wagon_axles if wagon_axles > 0 else 4
        
        # Расчет в CHF: Расстояние * Количество осей * 0.10 CHF
        total_chf = calc_distance * axles * 0.10
        total_usd = total_chf / fx_rate
        
        return {
            "gng_code": clean_gng,
            "wagon_axles": axles,
            "calculated_distance_km": calc_distance,
            "rate_per_axle_km_chf": 0.10,
            "total_chf": round(total_chf, 2),
            "fx_rate_used": fx_rate,
            "total_usd": round(total_usd, 2),
            "details": f"Порожний пробег приватного вагона ({axles} осей, ГНГ {clean_gng}): {calc_distance} км * {axles} осей * 0.10 CHF/ось-км"
        }

    # 3. Расчет для груженых вагонов
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    weight_info = calculate_chargeable_weight(fact_weight, clean_gng, wagon_type)
    chargeable_tons = weight_info["chargeable_tons"]
    weight_category = weight_info["weight_category"]

    table_info = select_tariff_table(
        wagon_category=wagon_type,
        shipment_type=shipment_type,
        is_empty_inventory=False,
        gng_code=clean_gng
    )
    table_num = table_info["table"]

    base_rate_chf = get_base_rate_from_table(table_num, calc_distance, weight_category, data_dir)

    coeff_info = get_applicable_coefficients(
        shipment_type=shipment_type,
        gng_code=clean_gng,
        table_number=table_num,
        wagon_type=wagon_type,
        from_station=from_station,
        to_station=to_station,
        is_loaded=True,
        is_private_wagon=is_private_wagon
    )
    total_multiplier = coeff_info["total_multiplier"]

    base_rate_usd_per_ton = base_rate_chf / fx_rate
    rate_usd_per_ton = base_rate_usd_per_ton * total_multiplier
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

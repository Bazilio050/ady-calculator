# ==============================================================================
# ГЛАВНЫЙ МОДУЛЬ РАСЧЕТА ТАРИФНЫХ СТАВОК ADY 2026
# ==============================================================================
import os
import re
from datetime import datetime

from core.weight import calculate_chargeable_weight
from core.route import calculate_tariff_distance
from core.table_selector import select_tariff_table
from core.table_parser import get_base_rate_from_table
from core.coefficients import get_applicable_coefficients
from core.currency import get_chf_usd_rate
from core.distance_finder import get_distance_between_stations

def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

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
    manual_distance_km=None,
    calculation_date=None,
    **kwargs
):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    if not calculation_date:
        calculation_date = datetime.now().strftime("%Y-%m-%d")

    fact_weight = safe_float(fact_weight, 0.0)
    wagon_axles = int(safe_float(wagon_axles, 4))
    if wagon_axles <= 0:
        wagon_axles = 4

    is_empty_wagon = bool(is_empty_wagon)
    fx_rate = get_chf_usd_rate(calculation_date)

    # 1. Расстояние
    if safe_float(manual_distance_km) > 0:
        raw_distance = safe_float(manual_distance_km)
    else:
        raw_distance = get_distance_between_stations(from_station, to_station)

    route_info = calculate_tariff_distance(raw_distance, shipment_type)
    calc_distance = route_info["calculated_distance_km"]

    clean_gng = re.sub(r'\D', '', str(gng_code or "")) if gng_code else ("99220000" if is_empty_wagon else "00000000")

    # 2. Обработка веса (Фактический / Расчетный)
    weight_info = calculate_chargeable_weight(fact_weight, clean_gng, wagon_type)
    chargeable_tons = weight_info["chargeable_tons"]
    weight_category = weight_info["weight_category"]

    # 3. Выбор таблицы и базовой ставки
    table_info = select_tariff_table(
        wagon_category=wagon_type,
        shipment_type=shipment_type,
        is_empty_inventory=False,
        gng_code=clean_gng
    )
    table_num = table_info["table"]

    base_rate_chf = get_base_rate_from_table(table_num, calc_distance, weight_category, data_dir)

    # 4. Коэффициенты
    coeff_info = get_applicable_coefficients(
        shipment_type=shipment_type,
        gng_code=clean_gng,
        table_number=table_num,
        wagon_type=wagon_type,
        from_station=from_station,
        to_station=to_station,
        is_loaded=not is_empty_wagon,
        is_private_wagon=is_private_wagon
    )
    total_multiplier = coeff_info["total_multiplier"]

    # Математика расчета ставки за тонну
    base_rate_usd = base_rate_chf / fx_rate if fx_rate else base_rate_chf
    rate_usd_per_ton = base_rate_usd * total_multiplier
    total_usd = rate_usd_per_ton * chargeable_tons

    # Перевод наименования типа перевозки
    shipment_names = {
        "import": "İdxal daşınması",
        "export": "İxrac daşınması",
        "transit": "Tranzit daşınması"
    }
    shipment_title = shipment_names.get(shipment_type.lower(), "İdxal daşınması")

    # Формирование текстовой формулы расчета
    coeffs_list = coeff_info["coefficients_list"]
    coeff_str_elements = [str(c["value"]) for c in coeffs_list]
    coeff_formula_part = " * ".join(coeff_str_elements) if coeff_str_elements else "1.0"
    formula_text = f"{base_rate_chf:.2f} / {fx_rate:.2f} * {coeff_formula_part} = {rate_usd_per_ton:.2f} USD/t"

    # Сборка структур Part1, Part2, Part3 для генерации интерфейса
    return {
        "part1": {
            "route": f"{from_station} – {to_station}",
            "shipment_type": shipment_title,
            "distance": f"{calc_distance} km",
            "cargo_and_wagon": f"GNG {clean_gng} — Qapalı vaqonda yük, Universal vaqon ({'SPS' if is_private_wagon else 'MPS'})",
            "weight_info": f"{int(fact_weight)} t / {int(chargeable_tons)} t",
            "period": "2026-cı fraxt ili"
        },
        "part2": {
            "exchange_rate": f"{fx_rate:.2f} CHF/USD",
            "base_tariff": f"{base_rate_chf:.2f} CHF/t (Cədvəl {table_num} ({calc_distance} km, {int(chargeable_tons)} t))",
            "coefficients": coeffs_list
        },
        "part3": {
            "formula": formula_text,
            "net_ady_rate": f"{rate_usd_per_ton:.2f} USD/t",
            "express_rate": None,  # Временно отключено
            "guard_rate": None,
            "notes": [c.get("note", "") for c in coeffs_list if c.get("note")]
        },
        "total_usd": round(total_usd, 2)
    }

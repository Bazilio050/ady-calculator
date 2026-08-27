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
from core.distance_finder import get_route_info

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
    lang="AZ",
    **kwargs
):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    calculation_date = calculation_date or datetime.now().strftime("%Y-%m-%d")
    fact_weight_val = safe_float(fact_weight, 0.0)
    manual_dist_val = safe_float(manual_distance_km, 0.0)
    
    wagon_axles_val = int(safe_float(wagon_axles, 4))
    if wagon_axles_val <= 0:
        wagon_axles_val = 4

    is_empty_wagon = bool(is_empty_wagon)
    fx_rate = get_chf_usd_rate(calculation_date) or 1.0

    # 1. Расстояние и форматирование станций с кодами ADY
    if manual_dist_val > 0:
        raw_distance = manual_dist_val
        route_formatted = f"{from_station} – {to_station}"
    else:
        # Передаем словарь в get_route_info, как требует distance_finder.py
        dummy_nlu = {
            "from_station": from_station,
            "to_station": to_station,
            "shipment_type": shipment_type
        }
        route_data = get_route_info(dummy_nlu, lang=lang)
        raw_distance = route_data.get("distance_km", 300)
        route_formatted = route_data.get("route_formatted") or route_data.get("route_display", f"{from_station} – {to_station}")

    route_info = calculate_tariff_distance(raw_distance, shipment_type)
    calc_distance = route_info["calculated_distance_km"]

    clean_gng = re.sub(r'\D', '', str(gng_code or "")) if gng_code else ("99220000" if is_empty_wagon else "00000000")

    # 2. Расчет веса (с учетом минимальных норм со стр. 11-12)
    weight_info = calculate_chargeable_weight(fact_weight_val, clean_gng, wagon_type)
    chargeable_tons = weight_info["chargeable_tons"]
    min_norm = weight_info.get("min_weight_norm", 0)
    weight_category = weight_info["weight_category"]

    # Форматирование отображения веса
    if min_norm > 0 and fact_weight_val < min_norm:
        weight_str = f"{int(fact_weight_val)} t / min. {int(chargeable_tons)} t"
    else:
        weight_str = f"{int(chargeable_tons)} t"

    # 3. Выбор таблицы и базовой ставки
    table_info = select_tariff_table(
        wagon_category=wagon_type,
        shipment_type=shipment_type,
        is_empty_inventory=False,
        gng_code=clean_gng
    )
    table_num = table_info["table"]

    base_rate_chf = get_base_rate_from_table(table_num, calc_distance, weight_category, data_dir)

    # 4. Коэффициенты с учетом выбранного языка lang
    coeff_info = get_applicable_coefficients(
        shipment_type=shipment_type,
        gng_code=clean_gng,
        table_number=table_num,
        wagon_type=wagon_type,
        from_station=from_station,
        to_station=to_station,
        is_loaded=not is_empty_wagon,
        is_private_wagon=is_private_wagon,
        lang=lang
    )
    total_multiplier = coeff_info["total_multiplier"]

    # Математика расчета
    base_rate_usd = base_rate_chf / fx_rate
    rate_usd_per_ton = base_rate_usd * total_multiplier
    total_usd = rate_usd_per_ton * chargeable_tons

    lang_key = lang.upper() if lang in ["AZ", "RU", "EN"] else "AZ"

    shipment_names = {
        "AZ": {"import": "İdxal daşınması", "export": "İxrac daşınması", "transit": "Tranzit daşınması"},
        "RU": {"import": "Импортная перевозка", "export": "Экспортная перевозка", "transit": "Транзитная перевозка"},
        "EN": {"import": "Import shipment", "export": "Export shipment", "transit": "Transit shipment"}
    }
    shipment_title = shipment_names[lang_key].get(str(shipment_type).lower(), shipment_names[lang_key]["import"])

    period_names = {
        "AZ": "2026-cı fraxt ili",
        "RU": "2026 фрахтовый год",
        "EN": "2026 freight year"
    }
    period_title = period_names.get(lang_key, "2026-cı fraxt ili")

    table_word = {
        "AZ": "Cədvəl",
        "RU": "Таблица",
        "EN": "Table"
    }.get(lang_key, "Cədvəl")

    # Формула расчета
    coeffs_list = coeff_info["coefficients_list"]
    coeff_str_elements = [str(c["value"]) for c in coeffs_list]
    coeff_formula_part = " * ".join(coeff_str_elements) if coeff_str_elements else "1.0"
    formula_text = f"{base_rate_chf:.2f} / {fx_rate:.2f} * {coeff_formula_part} = {rate_usd_per_ton:.2f} USD/t"

    wagon_ownership = "SPS" if is_private_wagon else "MPS"
    gng_name = kwargs.get("gng_name", "")

    if gng_name:
        cargo_label = f"GNG {clean_gng} ({gng_name})"
    else:
        cargo_label = f"GNG {clean_gng}"

    if is_empty_wagon:
        empty_text = {"AZ": "Boş vaqon", "RU": "Порожний вагон", "EN": "Empty wagon"}.get(lang_key, "Boş vaqon")
        cargo_status = f"{cargo_label} — {empty_text}, {wagon_type.capitalize()} ({wagon_ownership})"
    else:
        cargo_status = f"{cargo_label}, {wagon_type.capitalize()} ({wagon_ownership})"

    return {
        "part1": {
            "route": route_formatted,
            "shipment_type": shipment_title,
            "distance": f"{calc_distance} km",
            "cargo_and_wagon": cargo_status,
            "weight_info": weight_str,
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
            "express_rate": None,
            "guard_rate": None,
            "notes": [c.get("note", "") for c in coeffs_list if c.get("note")]
        },
        "total_usd": round(total_usd, 2)
    }

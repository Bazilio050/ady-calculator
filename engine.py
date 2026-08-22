import os
import re
import math
from datetime import datetime
from utils import (
    get_distance_by_esr,
    get_calculation_distance,
    format_station_display_name,
    get_min_weight_by_gng,
    get_global_coefficients,
    is_border_esr,
    resolve_esr_by_station_name,
    get_exchange_rate_for_date,
    should_apply_150_coeff,
    get_transporter_min_weight,
    is_long_platform_scep
)

from tables.table_3 import calculate_table_3_base
from tables.table_4 import calculate_table_4_base
from tables.table_5 import calculate_table_5_base
from tables.table_6 import calculate_table_6_base
from tables.table_7 import calculate_table_7_base

try:
    from tables.table_8 import calculate_table_8_tariff
except ImportError:
    def calculate_table_8_tariff(*args, **kwargs): return {"base_chf": 0.0, "details_label": "Cədvəl 8"}

try:
    from tables.table_10 import calculate_table_10_tariff
except ImportError:
    def calculate_table_10_tariff(*args, **kwargs): return {"base_chf": 0.0, "details_label": "Cədvəl 10"}

try:
    from tables.table_11 import calculate_table_11_tariff
except ImportError:
    def calculate_table_11_tariff(*args, **kwargs): return {"base_chf": 0.0, "column_info": "", "rate_type": "per_ton"}

try:
    from tables.table_12 import calculate_table_12_base
except ImportError:
    def calculate_table_12_base(*args, **kwargs): return (0.0, "Cədvəl 12")

EMPTY_SPS_CODES = ["99210000", "99213000", "99220000", "99223000"]

def _safe_extract_base_chf(val) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, (tuple, list)) and len(val) > 0:
        return float(val[0])
    if isinstance(val, dict):
        return float(val.get("base_chf") or val.get("rate") or 0.0)
    return 0.0

def process_full_calculation(nlu_data: dict, user_input_raw: str = "", lang: str = "AZ", year: str = "2026", ui_t: dict = None, *args, **kwargs) -> dict:
    if ui_t is None:
        ui_t = {}

    user_input_raw = user_input_raw or nlu_data.get("user_input_raw", "")
    input_lower = user_input_raw.lower()
    lang_upper = str(lang or "AZ").upper()

    st_from_raw = str(nlu_data.get("origin_name") or nlu_data.get("route_from") or "")
    st_to_raw = str(nlu_data.get("dest_name") or nlu_data.get("route_to") or "")

    origin_esr = nlu_data.get("origin_esr") or resolve_esr_by_station_name(st_from_raw, user_input_raw)
    dest_esr = nlu_data.get("dest_esr") or resolve_esr_by_station_name(st_to_raw, user_input_raw)

    explicit_mode = nlu_data.get("explicit_mode")
    if explicit_mode in ["import", "export", "transit"]:
        shipment_type_code = explicit_mode
    else:
        if is_border_esr(origin_esr) and is_border_esr(dest_esr):
            shipment_type_code = "transit"
        elif is_border_esr(origin_esr):
            shipment_type_code = "import"
        elif is_border_esr(dest_esr):
            shipment_type_code = "export"
        else:
            shipment_type_code = "import"

    # Расчет расстояния
    explicit_dist = nlu_data.get("distance_km") or nlu_data.get("actual_dist_km")
    if not explicit_dist and user_input_raw:
        m = re.search(r'(\d+)\s*(?:km|км)', input_lower)
        if m: explicit_dist = int(m.group(1))

    raw_dist = get_distance_by_esr(origin_esr, dest_esr)
    actual_dist_km = int(explicit_dist) if explicit_dist else (raw_dist or 204)
    tariff_dist_km = get_calculation_distance(actual_dist_km, shipment_type_code)

    gng = str(nlu_data.get("gng_code") or nlu_data.get("cargo_gng_code") or "00000000").strip()
    clean_gng = re.sub(r'\D', '', gng)
    cargo_name = str(nlu_data.get("gng_name") or nlu_data.get("cargo_name") or "Aşırılan yük")

    act_weight = float(nlu_data.get("weight_tons") or nlu_data.get("actual_weight_tons") or 0.0)
    park_type = str(nlu_data.get("park_type", "SPS") or "SPS").upper()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    is_empty = bool(nlu_data.get("is_empty", False))
    axles_count = int(nlu_data.get("axles_count") or 4)

    billable_weight = get_min_weight_by_gng(clean_gng, act_weight)
    base_chf = 0.0
    table_num = 3.0

    if is_empty and clean_gng in EMPTY_SPS_CODES:
        table_num = 3.22
        base_chf = 0.10 * axles_count * tariff_dist_km
    elif wagon_type in ["cistern", "цистерна", "çən"]:
        table_num = 6.0
        base_chf = _safe_extract_base_chf(calculate_table_6_base(clean_gng, park_type, billable_weight, tariff_dist_km))
    elif wagon_type in ["ref", "реф", "изотерм"]:
        table_num = 5.0
        ref_wagons = int(nlu_data.get("ref_section_cargo_wagons") or 5)
        base_chf = _safe_extract_base_chf(calculate_table_5_base(billable_weight, tariff_dist_km, ref_wagons))
    elif wagon_type in ["container", "контейнер", "tank_container"]:
        c_size = int(nlu_data.get("container_size") or 20)
        if wagon_type == "tank_container":
            table_num = 10.0
            base_chf = _safe_extract_base_chf(calculate_table_10_tariff(distance_km=tariff_dist_km, feet_size=c_size))
        else:
            table_num = 8.0
            base_chf = _safe_extract_base_chf(calculate_table_8_tariff(distance_km=tariff_dist_km, feet_size=c_size, is_empty=is_empty, park_type=park_type))
    elif shipment_type_code == "transit":
        table_num = 4.0
        base_chf = _safe_extract_base_chf(calculate_table_4_base(tariff_dist_km, billable_weight))
    else:
        table_num = 3.0
        base_chf = _safe_extract_base_chf(calculate_table_3_base(tariff_dist_km, billable_weight))

    # Коэффициенты
    coeffs = [("İndeksasiya 1.015", 1.015)]
    if park_type == "SPS" and table_num not in [3.22, 3.9]:
        coeffs.append(("SPS güzəşt 0.85", 0.85))

    if should_apply_150_coeff(shipment_type_code, table_num, clean_gng, wagon_type, park_type):
        coeffs.append(("İdxal/İxrac baza 1.50", 1.50))

    if is_long_platform_scep(user_input_raw, wagon_type):
        coeffs.append(("Спецплатформа >19m 1.20", 1.20))

    total_coeff = 1.0
    for _, c_val in coeffs:
        total_coeff *= c_val

    rate_chf_usd, _ = get_exchange_rate_for_date(datetime.now())
    net_ady_usd = round((base_chf * total_coeff) / rate_chf_usd, 2)
    express_usd = round(net_ady_usd * 1.02, 2)

    guard_usd = round(0.024 * tariff_dist_km, 2) if clean_gng.startswith("72") or clean_gng.startswith("27") else 0.0
    ferry_usd = round(float(nlu_data.get("wagon_length_m") or 15.0) * 50.0, 2) if bool(nlu_data.get("is_asco_ferry")) or "паром" in input_lower or "bərə" in input_lower else 0.0

    st_from_display = format_station_display_name(st_from_raw, origin_esr, lang_upper)
    st_to_display = format_station_display_name(st_to_raw, dest_esr, lang_upper)

    return {
        "part1": {
            "route": f"{st_from_display} -> {st_to_display}",
            "mode": shipment_type_code.upper(),
            "distance_km": tariff_dist_km,
            "actual_dist_km": actual_dist_km,
            "cargo": f"{cargo_name} (GNG {clean_gng})",
            "weight": f"Faktiki: {act_weight}t | Hesablanan: {billable_weight}t",
            "wagon": f"Tipi: {wagon_type.upper()} | Park: {park_type}"
        },
        "part2": {
            "base_chf": round(base_chf, 2),
            "exchange_rate": f"1 USD = {rate_chf_usd} CHF",
            "coefficients": coeffs
        },
        "part3": {
            "net_ady_rate": net_ady_usd,
            "express_rate": express_usd,
            "guard_cost": guard_usd,
            "guard_rate": guard_usd,
            "asco_ferry": {"total_usd": ferry_usd} if ferry_usd > 0 else 0.0
        }
    }

# === [НАЧАЛО БЛОКА: FILE-ENGINE] Диспетчер расчетов и генератор отчетов ===
import re
from datetime import datetime
from utils import (
    resolve_esr_by_station_name,
    get_border_esr,
    get_distance_by_esr,
    get_calculation_distance,
    format_station_display_name,
    get_weight_column_index,
    extract_gng_digits,
    get_min_weight_by_gng,
    get_transporter_min_weight,
    is_long_platform_scep,
    should_apply_150_coeff,
    get_global_coefficients,
    get_exchange_rate_for_date,
    parse_date_from_string
)

from tables.table_3 import calculate_table_3_base
from tables.table_4 import calculate_table_4_base
from tables.table_5 import calculate_table_5_base
from tables.table_6 import calculate_table_6_base
from tables.table_7 import calculate_table_7_base
from tables.table_8 import calculate_table_8_tariff

try:
    from tables.table_10 import calculate_table_10_base
except ImportError:
    try:
        from tables.table_10 import calculate_table_10_tariff as calculate_table_10_base
    except ImportError:
        def calculate_table_10_base(*args, **kwargs): return 0.0

try:
    from tables.table_11 import calculate_table_11_base
except ImportError:
    def calculate_table_11_base(*args, **kwargs): return 0.0

try:
    from tables.table_12 import calculate_table_12_base
except ImportError:
    def calculate_table_12_base(*args, **kwargs): return 0.0

EMPTY_SPS_CODES = ["99210000", "99213000", "99220000", "99223000"]

def process_full_calculation(nlu_data: dict, user_input_raw: str = "", lang: str = "AZ", year: str = "2026", ui_t: dict = None, *args, **kwargs) -> dict:
    if ui_t is None:
        ui_t = {}

    # Нормализация позиционных аргументов
    if args:
        if len(args) >= 1 and isinstance(args[0], str) and not user_input_raw:
            user_input_raw = args[0]
        if len(args) >= 2 and isinstance(args[1], str):
            lang = args[1]
        if len(args) >= 3 and isinstance(args[2], str):
            year = args[2]

    user_input_raw = user_input_raw or nlu_data.get("user_input_raw", "") or (str(nlu_data.get("route_from", "")) + " " + str(nlu_data.get("route_to", "")))
    input_lower = user_input_raw.lower()
    lang_upper = str(lang or "AZ").upper()

    # === [НАЧАЛО БЛОКА: ENGINE-01] Определение флагов паромного сообщения и режима ===
    has_ferry_kw = any(k in input_lower for k in ["паром", "bərə", "kurik", "курык", "aktau", "актау", "trk", "трк", "туркменбаши"]) or bool(nlu_data.get("is_asco_ferry"))

    explicit_mode = nlu_data.get("explicit_mode")
    if explicit_mode in ["import", "export", "transit"]:
        shipment_type_code = explicit_mode
    else:
        if any(k in input_lower for k in ["экспорт", "ixrac", "export"]):
            shipment_type_code = "export"
        elif any(k in input_lower for k in ["импорт", "idxal", "import"]):
            shipment_type_code = "import"
        elif any(k in input_lower for k in ["транзит", "tranzit", "transit"]):
            shipment_type_code = "transit"
        else:
            shipment_type_code = "transit" if has_ferry_kw else "import"
    # === [КОНЕЦ БЛОКА: ENGINE-01] ================================================

    # === [НАЧАЛО БЛОКА: ENGINE-02] Определение станций и ЕСР-кодов ===
    st_from_raw = str(nlu_data.get("route_from") or nlu_data.get("origin_name") or "")
    st_to_raw = str(nlu_data.get("route_to") or nlu_data.get("dest_name") or "")

    origin_esr = nlu_data.get("origin_esr") or resolve_esr_by_station_name(st_from_raw, user_input_raw, position="origin", shipment_mode=shipment_type_code)
    dest_esr = nlu_data.get("dest_esr") or resolve_esr_by_station_name(st_to_raw, user_input_raw, position="dest", shipment_mode=shipment_type_code)
    # === [КОНЕЦ БЛОКА: ENGINE-02] ================================================

    # === [НАЧАЛО БЛОКА: ENGINE-DIST] Расчет и поиск расстояний ===
    explicit_dist = nlu_data.get("distance_km") or nlu_data.get("actual_dist_km")
    if not explicit_dist and user_input_raw:
        m = re.search(r'(\d+)\s*(?:km|км)', user_input_raw.lower())
        if m:
            explicit_dist = int(m.group(1))

    raw_dist = get_distance_by_esr(origin_esr, dest_esr)
    actual_dist_km = int(explicit_dist) if explicit_dist else (raw_dist or 0)

    # Фоллбэк поиска по пограничным стыкам при внутренних кодах
    if actual_dist_km <= 0:
        b_from = get_border_esr(st_from_raw) or origin_esr
        b_to = get_border_esr(st_to_raw) or dest_esr
        actual_dist_km = get_distance_by_esr(b_from, b_to) or 0

    if actual_dist_km <= 0:
        return {"error": "Marşrut məsafəsi tapılmadı", "route_error": True}

    tariff_dist_km = get_calculation_distance(actual_dist_km, shipment_type_code)
    # === [КОНЕЦ БЛОКА: ENGINE-DIST] ==============================================

    # === [НАЧАЛО БЛОКА: ENGINE-03] Подготовка параметров вагона и груза ===
    gng = str(nlu_data.get("cargo_gng_code") or nlu_data.get("gng_code") or "00000000").strip()
    clean_gng = extract_gng_digits(gng)
    cargo_name = nlu_data.get("cargo_name") or nlu_data.get("gng_name") or "Aşırılan yük"
    
    act_weight = float(nlu_data.get("actual_weight_tons") or nlu_data.get("weight_tons") or 0.0)
    wagon_type = str(nlu_data.get("wagon_type") or "universal").lower()
    park_type = str(nlu_data.get("park_type") or "SPS").upper()
    is_empty = bool(nlu_data.get("is_empty", False))
    axles_count = int(nlu_data.get("axles_count") or 4)

    billable_weight = get_min_weight_by_gng(clean_gng, act_weight)
    if wagon_type == "transporter":
        billable_weight = get_transporter_min_weight(axles_count, act_weight)
    elif is_empty and clean_gng in EMPTY_SPS_CODES:
        billable_weight = 0.0
    # === [КОНЕЦ БЛОКА: ENGINE-03] ================================================

    # === [НАЧАЛО БЛОКА: ENGINE-04] Расчет базового тарифа по таблицам ===
    base_chf = 0.0
    table_num = 3.0

    if clean_gng in EMPTY_SPS_CODES and is_empty:
        table_num = 3.22
        base_chf = 0.10 * axles_count * tariff_dist_km
    elif wagon_type in ["cistern", "цистерна", "çən"]:
        table_num = 6.0
        base_chf = calculate_table_6_base(clean_gng, park_type, billable_weight, tariff_dist_km)
    elif wagon_type in ["ref", "реф", "изотерм"]:
        table_num = 5.0
        ref_wagons = int(nlu_data.get("ref_section_cargo_wagons") or 5)
        base_chf = calculate_table_5_base(billable_weight, tariff_dist_km, ref_wagons)
    elif wagon_type in ["container", "контейнер", "tank_container"]:
        c_size = int(nlu_data.get("container_size") or 20)
        if wagon_type == "tank_container":
            table_num = 10.0
            res_t10 = calculate_table_10_base(c_size, tariff_dist_km)
            base_chf = res_t10.get("base_chf") if isinstance(res_t10, dict) else float(res_t10 or 0)
        else:
            table_num = 8.0
            res_t8 = calculate_table_8_tariff(
                distance_km=tariff_dist_km,
                feet_size=c_size,
                is_empty=is_empty,
                park_type=park_type,
                is_medium_tonnage=bool(nlu_data.get("is_medium_tonnage", False)),
                medium_tons=int(nlu_data.get("medium_tons") or 5)
            )
            base_chf = res_t8.get("base_chf") if isinstance(res_t8, dict) else float(res_t8 or 0)
    elif shipment_type_code == "transit":
        table_num = 4.0
        base_chf = calculate_table_4_base(billable_weight, tariff_dist_km)
    else:
        table_num = 3.0
        base_chf = calculate_table_3_base(billable_weight, tariff_dist_km)
    # === [КОНЕЦ БЛОКА: ENGINE-04] ================================================

    # === [НАЧАЛО БЛОКА: ENGINE-05] Применение коэффициентов и сборов ===
    coeffs = [("İndeksasiya 1.015", 1.015)]
    
    if park_type == "SPS" and table_num not in [3.22, 3.9]:
        coeffs.append(("SPS güzəşt 0.85", 0.85))

    if should_apply_150_coeff(shipment_type_code, table_num, clean_gng, wagon_type, park_type):
        coeffs.append(("İdxal/İxrac baza 1.50", 1.50))

    if is_long_platform_scep(user_input_raw, wagon_type):
        coeffs.append(("Длиннобазная спецплатформа >19m 1.20", 1.20))

    # Вычисление итогового мультипликатора
    total_coeff = 1.0
    for _, c_val in coeffs:
        total_coeff *= c_val

    rate_chf_usd, rate_period = get_exchange_rate_for_date(datetime.now())
    net_ady_usd = round((base_chf * total_coeff) / rate_chf_usd, 2)
    express_usd = round(net_ady_usd * 1.02, 2)

    # Охрана
    guard_usd = 0.0
    if clean_gng.startswith("72") or clean_gng.startswith("27"):
        guard_usd = round(0.024 * tariff_dist_km, 2)

    # Паром ASCO
    ferry_usd = 0.0
    if has_ferry_kw:
        w_len = float(nlu_data.get("wagon_length_m") or 15.0)
        ferry_usd = round(w_len * 50.0, 2)
    # === [КОНЕЦ БЛОКА: ENGINE-05] ================================================

    # === [НАЧАЛО БЛОКА: ENGINE-06] Сборка итогового отчета ===
    st_from_display = format_station_display_name(st_from_raw, origin_esr, lang_upper)
    st_to_display = format_station_display_name(st_to_raw, dest_esr, lang_upper)

    return {
        "part1": {
            "route": f"{st_from_display} ({origin_esr}) -> {st_to_display} ({dest_esr})",
            "mode": shipment_type_code.upper(),
            "distance_km": tariff_dist_km,
            "actual_dist_km": actual_dist_km,
            "cargo": f"{cargo_name} (GNG {clean_gng})",
            "weight": f"Faktiki: {act_weight}t | Hesablanan: {billable_weight}t",
            "wagon": f"Tipi: {wagon_type.upper()} | Park: {park_type}"
        },
        "part2": {
            "base_chf": round(base_chf, 2),
            "exchange_rate": f"1 USD = {rate_chf_usd} CHF ({rate_period})",
            "coefficients": coeffs
        },
        "part3": {
            "net_ady_rate": net_ady_usd,
            "express_rate": express_usd,
            "guard_cost": guard_usd,
            "asco_ferry": {"total_usd": ferry_usd} if ferry_usd > 0 else 0.0
        }
    }
# === [КОНЕЦ БЛОКА: FILE-ENGINE] ==============================================

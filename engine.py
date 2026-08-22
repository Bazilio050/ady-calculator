# ==============================================================================
# 1. ИМПОРТЫ И ИНИЦИАЛИЗАЦИЯ
# ==============================================================================
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
    is_long_platform_scep,
    get_weight_column_index
)

from tables.table_3 import calculate_table_3_base, get_table_3_coefficients
from tables.table_4 import calculate_table_4_base, get_table_4_coefficients
from tables.table_5 import calculate_table_5_base, get_table_5_coefficients
from tables.table_6 import calculate_table_6_base, get_table_6_coefficients
from tables.table_7 import calculate_table_7_base, get_table_7_coefficients
from tables.table_8 import calculate_table_8_tariff
from tables.table_10 import calculate_table_10_tariff
from tables.table_11 import calculate_table_11_tariff
from tables.table_12 import calculate_table_12_base

EMPTY_SPS_CODES = ["99210000", "99213000", "99220000", "99223000"]

# ==============================================================================
# 2. ДИСПЕТЧЕР И РАСЧЕТНАЯ ЛОГИКА
# ==============================================================================
def process_full_calculation(nlu_data: dict, user_input_raw: str = "", lang: str = "AZ", year: str = "2026", ui_t: dict = None, *args, **kwargs) -> dict:
    if ui_t is None:
        ui_t = {}

    user_input_raw = user_input_raw or nlu_data.get("user_input_raw", "")
    input_lower = user_input_raw.lower()
    lang_upper = str(lang or "AZ").upper()

    # --------------------------------------------------------------------------
    # 2.1 ОПРЕДЕЛЕНИЕ СТАНЦИЙ И РЕЖИМА ПЕРЕВОЗКИ
    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # 2.2 РАСЧЕТ ТАРИФНОГО И ФАКТИЧЕСКОГО РАССРОЯНИЯ
    # --------------------------------------------------------------------------
    explicit_dist = nlu_data.get("distance_km") or nlu_data.get("actual_dist_km")
    if not explicit_dist and user_input_raw:
        m = re.search(r'(\d+)\s*(?:km|км)', input_lower)
        if m: explicit_dist = int(m.group(1))

    raw_dist = get_distance_by_esr(origin_esr, dest_esr)
    actual_dist_km = int(explicit_dist) if explicit_dist else (raw_dist or 204)

    gng = str(nlu_data.get("gng_code") or nlu_data.get("cargo_gng_code") or "00000000").strip()
    clean_gng = re.sub(r'\D', '', gng)

    # Мин. плечо: 151 км для бензола/особых цистерн и импорта
    if clean_gng.startswith("27071") or clean_gng.startswith("2707"):
        tariff_dist_km = max(actual_dist_km, 151)
    else:
        tariff_dist_km = get_calculation_distance(actual_dist_km, shipment_type_code)

    # --------------------------------------------------------------------------
    # 2.3 ПОДГОТОВКА ВЕСА И ПАРАМЕТРОВ ПОДВИЖНОГО СОСТАВА
    # --------------------------------------------------------------------------
    cargo_name = str(nlu_data.get("gng_name") or nlu_data.get("cargo_name") or "Aşırılan yük")
    act_weight = float(nlu_data.get("weight_tons") or nlu_data.get("actual_weight_tons") or 0.0)
    park_type = str(nlu_data.get("park_type", "SPS") or "SPS").upper()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    is_empty = bool(nlu_data.get("is_empty", False))
    axles_count = int(nlu_data.get("axles_count") or 4)

    # Норма веса для сборных отправок (п. 3.8)
    if bool(nlu_data.get("is_consolidated")) or "yığma" in input_lower or "сборны" in input_lower:
        billable_weight = max(10.0, act_weight)
    else:
        billable_weight = get_min_weight_by_gng(clean_gng, act_weight)

    base_chf = 0.0
    table_num = 3.0

    escort_cnt = int(nlu_data.get("escort_count") or 0)
    has_teplushka = bool(nlu_data.get("has_teplushka")) or "teplu" in input_lower or "теплу" in input_lower
    is_cover_wagon = any(k in input_lower for k in ["прикрыт", "qoruyucu", "guard_wagon"])
    is_dangerous = "2927" in user_input_raw or bool(nlu_data.get("is_dangerous"))
    oversize_group = nlu_data.get("oversize_group")

    # --------------------------------------------------------------------------
    # 2.4 ВЫБОР ТАРИФНОЙ ТАБЛИЦЫ И ВЫЧИСЛЕНИЕ БАЗОВОЙ СТАВКИ
    # --------------------------------------------------------------------------
    # Вагон прикрытия (п. 3.6.3)
    if is_cover_wagon:
        table_num = 3.63
        base_chf = 0.20 * axles_count * tariff_dist_km

    # Проводники и Теплушки (п. 3.9)
    elif escort_cnt > 0 and act_weight == 0:
        table_num = 3.9
        base_chf = escort_cnt * math.ceil(tariff_dist_km / 100.0) * 12.00
    elif has_teplushka:
        table_num = 3.9
        base_chf = 0.20 * axles_count * tariff_dist_km

    # Перегонки и ремонт (п. 3.7.8 / 3.7.2)
    elif is_empty and wagon_type == "transporter":
        table_num = 3.78
        rate_per_axle = 0.23 if axles_count <= 8 else 0.35
        base_chf = rate_per_axle * axles_count * tariff_dist_km
    elif is_empty and nlu_data.get("is_in_repair"):
        table_num = 3.72
        base_chf = 0.10 * axles_count * tariff_dist_km

    # Порожний возврат вагона (п. 3.2.2)
    elif is_empty and (clean_gng in EMPTY_SPS_CODES or "возврат" in input_lower or "boş" in input_lower):
        if wagon_type not in ["ref", "реф", "изотерм"] and not any(k in input_lower for k in ["qoşqu", "kuzov", "avtoqatar"]):
            table_num = 3.22
            base_chf = 0.10 * axles_count * tariff_dist_km

    # Перевозимые на своих осях (п. 3.7.1)
    elif bool(nlu_data.get("is_own_axles")):
        table_num = 3.71
        bw = max(10.0, act_weight)
        if shipment_type_code == "transit":
            r_val, _ = calculate_table_4_base(tariff_dist_km, bw)
        else:
            r_val, _ = calculate_table_3_base(tariff_dist_km, bw)
        base_chf = (r_val or 0.0) * 0.50

    # Опасные грузы (Cədvəl 12)
    elif is_dangerous and "1230" not in clean_gng:
        table_num = 12.0
        r_val, _ = calculate_table_12_base(tariff_dist_km, billable_weight)
        base_chf = r_val or 0.0

    # Негабаритные грузы (Cədvəl 11)
    elif oversize_group:
        table_num = 11.0
        res = calculate_table_11_tariff(tariff_dist_km, billable_weight, oversize_group)
        base_chf = res.get("base_chf") or 0.0

    # Цистерны (Cədvəl 6)
    elif wagon_type in ["cistern", "цистерна", "çən"]:
        table_num = 6.0
        r_val, _ = calculate_table_6_base(tariff_dist_km, billable_weight, clean_gng, park_type)
        base_chf = r_val or 0.0

    # Спецплатформы / Рефрижераторы / Автопоезда (Cədvəl 5)
    elif wagon_type in ["ref", "реф", "изотерм"] or any(k in input_lower for k in ["avtoqatar", "автопоезд", "qoşqu", "kuzov", "inv", "anv"]):
        table_num = 5.0
        rate_val, _, is_per_wagon = calculate_table_5_base(tariff_dist_km, billable_weight, wagon_type, user_input_raw=user_input_raw, is_empty=is_empty)
        base_chf = rate_val if is_per_wagon else (rate_val or 0.0) * billable_weight

    # Контейнеры (Cədvəl 8 и 10)
    elif wagon_type in ["container", "контейнер", "tank_container"]:
        c_size = int(nlu_data.get("container_size") or 20)
        if wagon_type == "tank_container":
            table_num = 10.0
            res = calculate_table_10_tariff(distance_km=tariff_dist_km, container_type="tank_container", feet_size=c_size, is_empty=is_empty, gng_code=clean_gng)
        else:
            table_num = 8.0
            res = calculate_table_8_tariff(distance_km=tariff_dist_km, feet_size=c_size, is_empty=is_empty, park_type=park_type)
        base_chf = res.get("base_chf") or 0.0

    # Малотоннажные отправки, почта, пассажирские (Cədvəl 7)
    elif act_weight > 0 and act_weight <= 25.0 and (wagon_type == "transporter" or "passenger" in wagon_type or clean_gng.startswith("9991")):
        table_num = 7.0
        rate_val, _ = calculate_table_7_base(tariff_dist_km, billable_weight_tons=billable_weight, wagon_type=wagon_type, is_empty=is_empty, gng_code=clean_gng, user_input_raw=user_input_raw)
        base_chf = rate_val or 0.0

    # Универсальные вагоны (Cədvəl 3 и 4)
    elif shipment_type_code == "transit":
        table_num = 4.0
        r_val, _ = calculate_table_4_base(tariff_dist_km, billable_weight)
        base_chf = r_val or 0.0
    else:
        table_num = 3.0
        r_val, _ = calculate_table_3_base(tariff_dist_km, billable_weight)
        base_chf = r_val or 0.0

    # ==============================================================================
    # 3. ФОРМИРОВАНИЕ КОЭФФИЦИЕНТОВ И СБОРОВ
    # ==============================================================================
    coeffs = []
    if table_num not in [3.9, 3.72, 3.78]:
        coeffs.append(("İndeksasiya 1.015", 1.015))

    if park_type == "SPS" and table_num not in [3.22, 3.9, 3.72, 3.78]:
        coeffs.append(("SPS güzəşt 0.85", 0.85))

    # Для цистерн коэффициент 1.50 не применяется
    if table_num != 6.0 and should_apply_150_coeff(shipment_type_code, table_num, clean_gng, wagon_type, park_type):
        coeffs.append(("İdxal/İxrac baza 1.50", 1.50))

    if is_long_platform_scep(user_input_raw, wagon_type):
        coeffs.append(("Спецплатформа >19m 1.20", 1.20))

    if table_num == 12.0:
        coeffs.append(("1-ci sinif təhlükəli yük 2.00", 2.00))

    # Специфические коэффициенты из модулей таблиц
    if table_num == 3.0:
        t_coeffs, _ = get_table_3_coefficients(shipment_type_code=shipment_type_code, gng_code=clean_gng, lang=lang)
        coeffs.extend(t_coeffs)
    elif table_num == 5.0:
        t_coeffs, _ = get_table_5_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=clean_gng, ref_wagons_cnt=nlu_data.get("ref_section_cargo_wagons"), user_input_raw=user_input_raw, lang=lang)
        coeffs.extend(t_coeffs)
    elif table_num == 6.0:
        t_coeffs, _ = get_table_6_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=clean_gng, park_type=park_type, lang=lang)
        coeffs.extend(t_coeffs)

    total_coeff = 1.0
    for _, c_val in coeffs:
        total_coeff *= c_val

    rate_chf_usd, _ = get_exchange_rate_for_date(datetime.now())
    net_ady_usd = round((base_chf * total_coeff) / rate_chf_usd, 2)
    express_usd = round(net_ady_usd * 1.02, 2)

    # Охрана
    guard_usd = 0.0
    if shipment_type_code == "transit" and (clean_gng.startswith("72") or clean_gng.startswith("27")):
        guard_usd = round((tariff_dist_km * 0.10 / 1.70) * 1.02, 2)

    # Паром ASCO
    ferry_usd = 0.0
    if bool(nlu_data.get("is_asco_ferry")) or "паром" in input_lower or "bərə" in input_lower:
        w_len = float(nlu_data.get("wagon_length_m") or 15.0)
        rate_m = 65.0 if w_len > 15.0 else 50.0
        ferry_usd = round(w_len * rate_m, 2)

    # ==============================================================================
    # 4. СБОРКА ИТОГОВОГО СЛОВАРЯ ОТВЕТА
    # ==============================================================================
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

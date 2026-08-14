import os
import re
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
    parse_date_from_string,
    should_apply_150_coeff,
    get_transporter_min_weight,
    is_long_platform_scep
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


def check_dangerous_goods_rule(gng_code: str, user_input_raw: str, wagon_type: str) -> tuple:
    """
    Проверяет, относится ли груз к опасным (п. 3.6.1, Cədvəl 13).
    Возвращает: (is_dangerous, apply_double_coeff, rule_note)
    """
    clean_gng = re.sub(r'\D', '', str(gng_code or "")).zfill(8)
    inp = str(user_input_raw or "").lower()
    w_type = str(wagon_type or "").lower()
    
    # Прямое указание тега опасности в запросе
    is_danger_flag = any(k in inp for k in ["опасный", "təhlükəli", "dangerous", "bmt", "un_code", "класс 1", "класс 5", "класс 6", "класс 7"])

    file_path = "Table_13_Tariffs.txt" if os.path.exists("Table_13_Tariffs.txt") else None
    matched_entry = None

    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" not in line or "Təhlükəli" in line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 5:
                        cargo_name, bmt_no, bdys_name, sinif, tətbiq_tipi = parts[0], parts[1], parts[2], parts[3], parts[4]
                        if (bmt_no != "0000" and bmt_no in inp) or (clean_gng != "00000000" and bmt_no in clean_gng):
                            matched_entry = (bmt_no, tətbiq_tipi)
                            break
        except Exception as e:
            print(f"Error checking Table 13: {e}")

    if matched_entry or is_danger_flag:
        apply_double = False
        t_type = matched_entry[1] if matched_entry else "hamisi"

        if t_type == "hamisi":
            apply_double = True
        elif t_type == "cen" and any(k in w_type for k in ["cistern", "цистерн", "tank", "çən", "bunker"]):
            # Исключение: метанол в цистернах (BMT 1230) рассчитывается по базовому тарифу без 2.0
            if "1230" not in clean_gng and "1230" not in inp:
                apply_double = True
        elif t_type == "ortulu_konteyner" and any(k in w_type for k in ["container", "крыт", "örtülü", "universal", "платфор"]):
            apply_double = True

        return True, apply_double, f"Təhlükəli yük (bənd 3.6.1, Cədvəl 13, BMT {matched_entry[0] if matched_entry else 'spesifik'})"

    return False, False, ""


def detect_oversize_group(nlu_data: dict, user_input_raw: str) -> str:
    """
    Определяет группу негабаритности на основе JSON от Gemini или текста запроса.
    """
    group = str(nlu_data.get("oversize_group") or "").strip().lower()
    if group in ["deg3_upper", "deg3_5_lowside", "small_deg", "degree_6"]:
        return group
    
    inp = user_input_raw.lower()
    if any(k in inp for k in ["3-yuxarı", "3 yuxarı", "3 верхняя", "3 верх", "3 yuxari", "3 deg upper"]):
        return "deg3_upper"
    elif any(k in inp for k in ["3-5 aşağı", "3-5 asagi", "4-5 yan", "3-5 нижняя", "4-5 боковая", "3-5 low", "4-5 side"]):
        return "deg3_5_lowside"
    elif any(k in inp for k in ["6-cı dərəcə", "6 dərəcə", "6 степень", "6-ci derece", "сверхнегабарит"]):
        return "degree_6"
    elif any(k in inp for k in ["kiçik dərəcə", "малая степень", "1-2 aşağı", "1-3 yan", "1-2 yuxarı"]):
        return "small_deg"
    
    return ""


def get_currency_rate(requested_period: str = None, lang: str = "AZ") -> tuple:
    target_dt = parse_date_from_string(requested_period)
    rate, period_str = get_exchange_rate_for_date(target_dt)
    
    label = f"**{rate:.2f} CHF/USD** ({period_str})"
    return rate, label


def apply_special_exceptions(
    nlu_data: dict, 
    shipment_type_code: str, 
    table_num: float, 
    is_ref_type: bool, 
    act_weight: float, 
    billable_weight: float, 
    dist_km: int, 
    user_input_raw: str, 
    lang: str, 
    ui_t: dict, 
    ref_wagons_cnt: int,
    origin_esr: str = "",
    dest_esr: str = ""
) -> tuple:
    coeffs = []
    notes = []

    park_type = str(nlu_data.get("park_type", "SPS") or "SPS").upper()
    gng = str(nlu_data.get("gng_code") or nlu_data.get("cargo_gng_code") or "").strip()
    clean_gng = re.sub(r'\D', '', gng).zfill(8)
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    
    if not origin_esr:
        st_from_raw = str(nlu_data.get("origin_name") or nlu_data.get("route_from") or "")
        origin_esr = resolve_esr_by_station_name(st_from_raw) or str(nlu_data.get("origin_esr") or "")
    if not dest_esr:
        st_to_raw = str(nlu_data.get("dest_name") or nlu_data.get("route_to") or "")
        dest_esr = resolve_esr_by_station_name(st_to_raw) or str(nlu_data.get("dest_esr") or "")

    input_lower = user_input_raw.lower()
    is_empty = nlu_data.get("is_empty", False) or any(k in input_lower for k in ["boş", "порожн", "empty"])

    # 1. ИНДЕКСАЦИЯ 1.015
    req_period = nlu_data.get("requested_period")
    target_dt = parse_date_from_string(req_period) if req_period else None
    if not target_dt:
        target_dt = datetime.now()

    is_after_april_2026 = target_dt >= datetime(2026, 4, 1)

    if not is_empty and is_after_april_2026:
        ind_label = "Əlavə əmsal" if lang == "AZ" else ("Индексация" if lang == "RU" else "Indexation")
        coeffs.append((ind_label, 1.015))
        
        ind_note = (
            "Yüklü vaqonların daşınmasına 1.015 əlavə əmsalı (indeksasiya) tətbiq olunmuşdur."
            if lang == "AZ" else
            ("К перевозке гружёных вагонов применён дополнительный коэффициент (индексация) 1.015."
             if lang == "RU" else
             "Additional indexation factor 1.015 applied for loaded wagon movement.")
        )
        notes.append(ind_note)
        
    # 2. ГЛОБАЛЬНЫЙ КОЭФФИЦИЕНТ 1.50
    if is_empty and clean_gng in EMPTY_SPS_CODES:
        if shipment_type_code in ["import", "export"]:
            lbl_150 = "İdxal/İxrac baza" if lang == "AZ" else ("Импорт/Экспорт база" if lang == "RU" else "Import/Export base")
            coeffs.append((lbl_150, 1.50))
            notes.append("Boş vaqonların İdxal/İxrac daşınmasına 1.50 əmsalı tətbiq olunmuşdur.")
    else:
        if should_apply_150_coeff(shipment_type_code, table_num, gng, wagon_type, park_type):
            lbl_150 = "İdxal/İxrac baza" if lang == "AZ" else ("Импорт/Экспорт база" if lang == "RU" else "Import/Export base")
            coeffs.append((lbl_150, 1.50))
            notes.append("Baza tarifinə İdxal/İxrac üzrə 1.50 əmsalı tətbiq olunmuşdur.")

    # 3. Специфические коэффициенты конкретных таблиц
    if table_num == 3:
        tbl_coeffs, tbl_notes = get_table_3_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 4:
        tbl_coeffs, tbl_notes = get_table_4_coefficients(shipment_type=shipment_type_code, wagon_type=wagon_type, gng_code=gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 5:
        tbl_coeffs, tbl_notes = get_table_5_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=gng, ref_wagons_cnt=ref_wagons_cnt, lang=lang, ui_t=ui_t, user_input_raw=user_input_raw)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 6:
        tbl_coeffs, tbl_notes = get_table_6_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=gng, park_type=park_type, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 7:
        tbl_coeffs, tbl_notes = get_table_7_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)

    # 3.1. ТАБЛИЦА 11 И ПРАВИЛА НЕГАБАРИТА (Пункт 3.5.1)
    oversize_grp = detect_oversize_group(nlu_data, user_input_raw)
    if table_num == 11:
        note_t11 = (
            "Əndazəsiz yüklərin daşınma haqqı Cədvəl 11 dərəcələri ilə hesablanmışdır (bənd 3.5.1.2)."
            if lang == "AZ" else
            ("Перевозка негабаритного груза рассчитана по ставкам Таблицы 11 (п. 3.5.1.2)."
             if lang == "RU" else
             "Oversized cargo movement calculated according to Table 11 rates (clause 3.5.1.2).")
        )
        notes.append(note_t11)

    elif table_num == 7 and any(k in input_lower for k in ["транспортер", "transportyor", "transporter"]):
        if oversize_grp == "degree_6" or "5 aşağı" in input_lower or "5 yan" in input_lower:
            coeffs.append(("Əndazəsizlik (6-cı dərəcə / 5 aşağı-yan)", 3.00))
            notes.append("Транспортерdə 6-cı dərəcəli və ya 5 aşağı/yan əndazəsiz yükə 3.00 əmsalı tətbiq olunmuşdur (bənd 3.5.1.3 / 3.5.1.5).")
        elif oversize_grp == "deg3_5_lowside":
            coeffs.append(("Əndazəsizlik (3-4 aşağı, 4 yan)", 2.00))
            notes.append("Транспортерdə 3-4 aşağı və ya 4 yan dərəcəli əndazəsiz yükə 2.00 əmsalı tətbiq olunmuşdur (bənd 3.5.1.3).")
        elif oversize_grp == "deg3_upper":
            coeffs.append(("Əndazəsizlik (3 yuxarı)", 1.50))
            notes.append("Транспортерdə 3-cü yuxarı dərəcəli əndazəsiz yükə 1.50 əmsalı tətbiq olunmuşdur (bənd 3.5.1.3).")

    # 3.1.2.7 — Спецплатформы длиннее 19 м (НЕ применяется к Таблице 5 и Таблице 11)
    if table_num not in [5, 11] and is_long_platform_scep(user_input_raw, wagon_type):
        if not is_empty:
            lbl_19m = "Sintez platforma >19m" if lang == "AZ" else ("Спецплатформа >19м" if lang == "RU" else "Special platform >19m")
            coeffs.append((lbl_19m, 1.20))
            notes.append("Qoşqu oxları 19m-dən artıq olan platformalar üçün 1.20 əmsalı tətbiq edilmişdir.")
        elif park_type == "SPS":
            lbl_empty_19m = "Boş platforma >19m" if lang == "AZ" else ("Скидка порожн. >19м" if lang == "RU" else "Empty platform >19m")
            coeffs.append((lbl_empty_19m, 0.60))
            
    # 4. Общие глобальные коэффициенты
    g_coeffs, g_notes = get_global_coefficients(shipment_type_code, gng, origin_esr, dest_esr, lang)
    coeffs.extend(g_coeffs)
    notes.extend(g_notes)

    # 5. СКИДКА СПС (0.85 или 0.70 согласно п. 3.2.5)
    if park_type == "SPS":
        sps_val = 0.85
        apply_sps = False

        if table_num in [3, 4, 5, 7, 8, 10, 11, 12]:
            apply_sps = True
        elif table_num == 6:
            from tables.table_6 import determine_table_6_column
            col_idx = determine_table_6_column(clean_gng, park_type)
            if col_idx == 6:
                sps_val = 0.70
                apply_sps = True
            else:
                apply_sps = True

        if apply_sps:
            sps_label = "SPS güzəşti" if lang == "AZ" else ("Скидка СПС" if lang == "RU" else "SPS Discount")
            coeffs.append((sps_label, sps_val))
            
            if sps_val == 0.70:
                sps_note = (
                    "Cədvəl 6 (sütun 8): 2707 və 2902 YHN kodlu yüklər üçün özəl çənlərə 0.85 əvəzinə 0.70 güzəşt əmsalı tətbiq olunmuşdur (bənd 3.2.5)."
                    if lang == "AZ" else
                    ("Таблица 6 (ст. 8): Для грузов ГНГ 2707 и 2902 в приватных цистернах применён скидочный коэффициент 0.70 вместо 0.85 (п. 3.2.5)."
                     if lang == "RU" else
                     "Table 6 (col 8): SPS discount factor 0.70 applied instead of 0.85 for GNG 2707 and 2902 (clause 3.2.5).")
                )
            else:
                sps_note = (
                    "Xüsusi mülkiyyətdə olan (SPS) vaqonlara 0.85 güzəşt əmsalı tətbiq edilmişdir."
                    if lang == "AZ" else
                    ("К приватным вагонам (СПС) применён скидочный коэффициент 0.85."
                     if lang == "RU" else
                     "SPS discount factor 0.85 applied for private wagons.")
                )
            notes.append(sps_note)

    # 6. ОПАСНЫЕ ГРУЗЫ И ВАГОНЫ ПРИКРЫТИЯ (Пункт 3.6)
    is_danger, apply_double, danger_note = check_dangerous_goods_rule(gng, user_input_raw, wagon_type)
    if is_danger and apply_double:
        coeffs.append(("Təhlükəli yük əmsalı (x2.00)", 2.00))
        notes.append("Təhlükəli yüklərin daşınmasına görə tarif dərəcələrinə 2.00 əmsalı tətbiq olunmuşdur (bənd 3.6.1).")

    # Вагон прикрытия / Qoruyucu vaqon (п. 3.6.3)
    if any(k in input_lower for k in ["прикрытие", "qoruyucu", "daldalanacaq", "guard_wagon"]):
        cover_rate = 0.30 if park_type == "SPS" else 0.35
        axles = float(nlu_data.get("axles_count") or 4)
        match_axle = re.search(r'(\d+)\s*(?:oxlu|осн|axle|осей)', input_lower)
        if match_axle:
            axles = int(match_axle.group(1))
        cover_chf = cover_rate * axles * dist_km
        notes.append(f"Qoruyucu (daldalanacaq) vaqonunun daşınma haqqı bənd 3.6.3-ə əsasən ({cover_rate} CHF × {int(axles)} ox × {dist_km} km = {cover_chf:.2f} CHF) əlavə olunmuşdur.")

    return coeffs, notes


def process_full_calculation(nlu_data: dict, user_input_raw: str, lang: str, year: str, ui_t: dict) -> dict:
    lang_upper = str(lang or "AZ").upper()
    
    st_from_raw = str(nlu_data.get("origin_name") or nlu_data.get("route_from") or "")
    st_to_raw = str(nlu_data.get("dest_name") or nlu_data.get("route_to") or "")

    origin_esr = resolve_esr_by_station_name(st_from_raw) or str(nlu_data.get("origin_esr") or "")
    dest_esr = resolve_esr_by_station_name(st_to_raw) or str(nlu_data.get("dest_esr") or "")

    gng = str(nlu_data.get("gng_code") or nlu_data.get("cargo_gng_code") or "").strip()
    clean_gng = re.sub(r'\D', '', gng).zfill(8)
    cargo_name_nlu = str(nlu_data.get("gng_name") or nlu_data.get("cargo_name") or "").strip()

    act_weight = float(nlu_data.get("weight_tons") or nlu_data.get("actual_weight_tons") or 0.0)
    park_type = str(nlu_data.get("park_type", "SPS") or "SPS").upper()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    shipment_kind = str(nlu_data.get("shipment_kind") or "").lower()

    ref_wagons_cnt = nlu_data.get("ref_section_cargo_wagons")
    if ref_wagons_cnt is None:
        match_plus = re.search(r'(\d+)\s*\+\s*1|1\s*\+\s*(\d+)', user_input_raw)
        if match_plus:
            ref_wagons_cnt = int(match_plus.group(1) or match_plus.group(2))

    explicit_mode = nlu_data.get("explicit_mode")

    display_from = format_station_display_name(st_from_raw, origin_esr, lang_upper)
    display_to = format_station_display_name(st_to_raw, dest_esr, lang_upper)
    route_display = f"{display_from} – {display_to}"

    if explicit_mode in ["import", "export", "transit"]:
        shipment_type_code = explicit_mode
        shipment_type_display = ui_t.get(f"type_{explicit_mode}", explicit_mode.capitalize())
    else:
        if is_border_esr(origin_esr) and is_border_esr(dest_esr):
            shipment_type_code, shipment_type_display = "transit", ui_t["type_transit"]
        elif is_border_esr(origin_esr):
            shipment_type_code, shipment_type_display = "import", ui_t["type_import"]
        elif is_border_esr(dest_esr):
            shipment_type_code, shipment_type_display = "export", ui_t["type_export"]
        else:
            shipment_type_code = "local"
            shipment_type_display = "Daxili daşınma" if lang_upper == "AZ" else ("Внутренняя перевозка" if lang_upper == "RU" else "Domestic shipment")

    raw_dist = get_distance_by_esr(origin_esr, dest_esr)
    try:
        actual_dist_km = int(raw_dist) if raw_dist is not None else 0
    except (ValueError, TypeError):
        actual_dist_km = 0

    if actual_dist_km <= 0 or actual_dist_km > 5000:
        actual_dist_km = 300

    tariff_dist_km = get_calculation_distance(actual_dist_km, shipment_type_code)
    
    if tariff_dist_km != actual_dist_km:
        dist_display = f"{actual_dist_km} km (min. {tariff_dist_km} km)"
    else:
        dist_display = f"{actual_dist_km} km"

    input_lower = user_input_raw.lower()
    is_empty_wagon = nlu_data.get("is_empty", False) or any(k in input_lower for k in ["boş", "порожн", "empty"])

    # Проверка на вагон прикрытия (п. 3.6.3 / 3.5.3)
    is_cover_wagon = any(k in input_lower for k in ["прикрытие", "qoruyucu", "daldalanacaq", "guard_wagon"])

    # Определение спецплатформ, автопоездов и прицепов (Таблица 5, п. 3.2.6)
    table_5_keywords = ["ref", "реф", "thermos", "термос", "изотерм", "auto", "авто", "avtoqatar", "автопоезд", "qoşqu", "прицеп", "semitrailer", "yarımqoşqu", "kuzov", "кузов", "inv", "anv"]
    is_table_5_object = any(k in wagon_type for k in table_5_keywords) or (ref_wagons_cnt is not None) or any(k in input_lower for k in table_5_keywords)

    # Инвентарный порожний вагон МПС -> Бесплатно (п. 3.1.1)
    if is_empty_wagon and park_type == "MPS" and not is_cover_wagon:
        empty_note = {
            "AZ": "İnventar parka mənsub olan boş vaqonlar boşaldıqdan sonra mensub olduqları ölkələrə qaytarıldıqları zaman daşıma haqqı hesablanmır (bənd 3.1.1).",
            "RU": "Возврат порожних инвентарных вагонов (МПС) к месту приписки осуществляется бесплатно (п. 3.1.1).",
            "EN": "Return of empty inventory wagons (MPS) to owner countries is free of charge (clause 3.1.1)."
        }
        return {
            "part1": {
                "route": route_display, "shipment_type": shipment_type_display, "distance": dist_display,
                "cargo_and_wagon": "Boş MPS vaqon / Порожний вагон МПС", "weight_info": "0 t", "period": f"{year}"
            },
            "part2": {
                "exchange_rate": "0.79 CHF/USD", "base_tariff": "0.00 CHF", "coefficients": []
            },
            "part3": {
                "formula": "0.00 CHF / USD", "net_ady_rate": "0.00 USD",
                "express_rate": "0.00 USD", "notes": [empty_note.get(lang_upper, empty_note["AZ"])]
            }
        }

    # ---------------------------------------------------------
    # ВАГОН ПРИКРЫТИЯ (п. 3.6.3 / 3.5.3)
    # ---------------------------------------------------------
    if is_cover_wagon:
        table_num = 3.63
        is_per_wagon = True
        axles = float(nlu_data.get("axles_count") or 4)
        match_axle = re.search(r'(\d+)\s*(?:oxlu|осн|axle|осей)', input_lower)
        if match_axle:
            axles = int(match_axle.group(1))
        
        cover_rate = 0.30 if park_type == "SPS" else 0.35
        base_chf = cover_rate * axles * actual_dist_km
        table_details = f"bənd 3.6.3 ({cover_rate} CHF × {int(axles)} ox × {actual_dist_km} km)" if lang_upper == "AZ" else (
            f"п. 3.6.3 ({cover_rate} CHF × {int(axles)} осей × {actual_dist_km} км)" if lang_upper == "RU" else
            f"clause 3.6.3 ({cover_rate} CHF × {int(axles)} axles × {actual_dist_km} km)"
        )
        weight_display = "0 t (qoruyucu)" if lang_upper == "AZ" else ("0 т (прикрытие)" if lang_upper == "RU" else "0 t (cover)")
        billable_weight = 0.0

    # ---------------------------------------------------------
    # ПУНКТ 3.2.2: Порожний приватный вагон СПС (0.10 CHF/ось-км)
    # ---------------------------------------------------------
    elif is_empty_wagon and clean_gng in EMPTY_SPS_CODES and not is_table_5_object and "container" not in wagon_type:
        table_num = 3.22
        is_per_wagon = True
        axles = float(nlu_data.get("axles_count") or 4)
        
        base_chf = 0.10 * axles * tariff_dist_km
        table_details = f"bənd 3.2.2 (0.10 CHF × {int(axles)} ox × {tariff_dist_km} km)" if lang_upper == "AZ" else (
            f"п. 3.2.2 (0.10 CHF × {int(axles)} осей × {tariff_dist_km} км)" if lang_upper == "RU" else
            f"clause 3.2.2 (0.10 CHF × {int(axles)} axles × {tariff_dist_km} km)"
        )
        weight_display = "0 t (boş)" if lang_upper == "AZ" else ("0 т (порожний)" if lang_upper == "RU" else "0 t (empty)")
        billable_weight = 0.0

    else:
        # ---------------------------------------------------------
        # РАСЧЁТ ОПАСНЫХ ГРУЗОВ (Cədvəl 12) ИЛИ ДРУГИХ ТАБЛИЦ
        # ---------------------------------------------------------
        is_danger, _, _ = check_dangerous_goods_rule(gng, user_input_raw, wagon_type)
        is_tanker_type = any(k in wagon_type for k in ["cistern", "цистерн", "tank", "çən", "bunker", "бункер"]) and "container" not in wagon_type

        oversize_group = detect_oversize_group(nlu_data, user_input_raw)

        if oversize_group in ["deg3_upper", "deg3_5_lowside"]:
            table_num = 11
            billable_weight = max(10.0, act_weight)
            res_t11 = calculate_table_11_tariff(tariff_dist_km, billable_weight, oversize_group)
            base_chf = res_t11["base_chf"]
            table_details = f"Cədvəl 11 ({res_t11['column_info']})"
            is_per_wagon = (res_t11["rate_type"] == "per_wagon")

        else:
            if oversize_group == "small_deg":
                billable_weight = max(25.0, act_weight)
            else:
                billable_weight = get_min_weight_by_gng(gng, act_weight)

            match_axle = re.search(r'(\d+)\s*(?:oxlu|осн|axle|осей)', input_lower)
            if match_axle:
                axles = int(match_axle.group(1))
                billable_weight = get_transporter_min_weight(axles, billable_weight)

            is_transporter = any(k in input_lower for k in ["транспортер", "transportyor", "transporter"])
            feet_size = int(nlu_data.get("container_size") or 20)
            is_tank_container = any(k in wagon_type for k in ["tank_container", "tank_konteyner"]) or ("container" in wagon_type and "tank" in input_lower)
            is_ref_container = any(k in wagon_type for k in ["ref_container", "ref_konteyner"]) or ("container" in wagon_type and "ref" in input_lower)
            is_universal_container = ("container" in wagon_type or "konteyner" in wagon_type or "контейнер" in wagon_type) and not (is_tank_container or is_ref_container)

            is_table_7_type = (
                "small_chunk" in wagon_type or "small_chunk" in shipment_kind or
                "passenger" in wagon_type or "sərnişin" in wagon_type or "baggage" in wagon_type or
                clean_gng.startswith("99910000") or
                is_transporter or "transporter" in wagon_type
            )

            # --- МАРШРУТИЗАЦИЯ ТАБЛИЦ ---
            if is_danger and not is_tanker_type and not is_universal_container:
                # Опасные грузы в универсальных и специализированных вагонах (кроме цистерн и контейнеров) -> Cədvəl 12
                table_num = 12
                is_per_wagon = False
                base_chf, table_details = calculate_table_12_base(tariff_dist_km, billable_weight)

            elif is_tank_container or is_ref_container:
                table_num = 10
                is_per_wagon = True
                res_t10 = calculate_table_10_tariff(
                    distance_km=tariff_dist_km, container_type=wagon_type, feet_size=feet_size,
                    is_empty=is_empty_wagon, gng_code=clean_gng
                )
                base_chf = res_t10["base_chf"]
                table_details = res_t10["details_label"]

            elif is_universal_container:
                table_num = 8
                is_per_wagon = True
                is_mid = bool(nlu_data.get("is_medium_tonnage", False)) or act_weight <= 5.0
                mid_tons = int(nlu_data.get("medium_tons") or (3 if act_weight <= 3.0 else 5))
                res_t8 = calculate_table_8_tariff(
                    distance_km=tariff_dist_km, feet_size=feet_size, is_empty=is_empty_wagon,
                    park_type=park_type, is_medium_tonnage=is_mid, medium_tons=mid_tons
                )
                base_chf = res_t8["base_chf"]
                table_details = res_t8["details_label"]

            elif is_table_7_type:
                table_num = 7
                is_per_wagon = False
                base_chf, table_details = calculate_table_7_base(
                    distance_km=tariff_dist_km, billable_weight_tons=billable_weight, wagon_type=wagon_type,
                    container_type=nlu_data.get("container_type"), is_empty=is_empty_wagon,
                    gng_code=clean_gng, lang=lang_upper, user_input_raw=user_input_raw
                )
            elif is_tanker_type:
                table_num = 6
                is_per_wagon = False
                base_chf, table_details = calculate_table_6_base(tariff_dist_km, billable_weight, gng, park_type, {}, lang_upper)
            elif is_table_5_object:
                table_num = 5
                base_chf, table_details, is_per_wagon = calculate_table_5_base(
                    tariff_dist_km, billable_weight, wagon_type, lang=lang_upper, user_input_raw=user_input_raw, is_empty=is_empty_wagon
                )
            elif shipment_type_code == "transit":
                table_num = 4
                is_per_wagon = False
                base_chf, table_details = calculate_table_4_base(tariff_dist_km, billable_weight, {}, lang_upper)
            else:
                table_num = 3
                is_per_wagon = False
                base_chf, table_details = calculate_table_3_base(tariff_dist_km, billable_weight, {}, lang_upper)

        act_w_str = f"{int(act_weight) if act_weight.is_integer() else act_weight}"
        bill_w_str = f"{int(billable_weight) if billable_weight.is_integer() else billable_weight}"

        if act_weight < billable_weight:
            weight_display = f"{act_w_str} t (min. {bill_w_str} t)"
        else:
            weight_display = f"{act_w_str} t"

        if base_chf is None:
            base_chf = 1200.0
            table_details = "Таблица 3 (базовая)"

    unit_str = ui_t.get("unit_wagon", "USD/vaqon") if is_per_wagon else ui_t.get("unit_ton", "USD/t")
    chf_unit = "CHF/вагон" if (is_per_wagon and lang_upper == "RU") else ("CHF/vaqon" if is_per_wagon else ("CHF/т" if lang_upper == "RU" else "CHF/t"))

    base_tariff_display = f"**{base_chf:.2f} {chf_unit}** ({table_details})"
    usd_rate, exchange_display = get_currency_rate(nlu_data.get("requested_period"), lang_upper)

    is_ref_type_check = (table_num == 5)
    
    coeffs, notes = apply_special_exceptions(
        nlu_data, shipment_type_code, table_num, is_ref_type_check, act_weight, 
        billable_weight, actual_dist_km, user_input_raw, lang_upper, ui_t, ref_wagons_cnt,
        origin_esr, dest_esr
    )

    if not is_empty_wagon and act_weight > 0 and act_weight < billable_weight:
        weight_note = (
            f"Minimum hesablama çəkisi norması {int(billable_weight)} ton tətbiq olunmuşdur."
            if lang_upper == "AZ" else
            (f"Применена минимальная норма расчётного веса {int(billable_weight)} тонн."
             if lang_upper == "RU" else
             f"Minimum billable weight norm of {int(billable_weight)} tons applied.")
        )
        notes.insert(0, weight_note)

    if is_cover_wagon:
        cover_sps_note = (
            "Qoruyucu vaqonun daşınma haqqı bənd 3.6.3-ə əsasən hesablanmışdır."
            if lang_upper == "AZ" else
            ("Плата за перевозку вагона прикрытия рассчитана согласно п. 3.6.3."
             if lang_upper == "RU" else
             "Cover wagon charge calculated according to clause 3.6.3.")
        )
        notes.insert(0, cover_sps_note)

    final_rate = base_chf / usd_rate
    formula_parts = [f"{base_chf:.2f} / {usd_rate:.2f}"]
    for _, c_val in coeffs:
        final_rate *= float(c_val)
        formula_parts.append(f"{c_val}")

    formula_str = " × ".join(formula_parts) + f" = {final_rate:.2f} {unit_str}"
    express_rate_str = f"{final_rate * 1.02:.2f} {unit_str}"

    park_display = "SPS" if park_type == "SPS" else "MPS"
    sec_info = f" ({ref_wagons_cnt}+1)" if ref_wagons_cnt else ""

    if is_cover_wagon:
        wagon_disp_name = "Qoruyucu vaqon" if lang_upper == "AZ" else ("Вагон прикрытия" if lang_upper == "RU" else "Cover wagon")
    elif is_empty_wagon and clean_gng in EMPTY_SPS_CODES and not is_table_5_object and table_num == 3.22:
        wagon_disp_name = "Boş vaqon" if lang_upper == "AZ" else ("Порожний вагон" if lang_upper == "RU" else "Empty wagon")
    elif table_num == 12:
        wagon_disp_name = "Təhlükəli yük vaqonu (Cədvəl 12)" if lang_upper == "AZ" else ("Вагон с опасным грузом (Таблица 12)" if lang_upper == "RU" else "Dangerous cargo wagon (Table 12)")
    elif table_num == 10:
        wagon_disp_name = "Xüsusi/Tank/Ref konteyner (Cədvəl 10)" if lang_upper == "AZ" else ("Спец/Танк/Реф контейнер (Таблица 10)" if lang_upper == "RU" else "Special/Tank/Ref container (Table 10)")
    elif table_num == 8:
        wagon_disp_name = "Konteyner (Cədvəl 8)" if lang_upper == "AZ" else ("Контейнер (Таблица 8)" if lang_upper == "RU" else "Container (Table 8)")
    elif table_num == 11:
        wagon_disp_name = "Əndazəsiz yük (Cədvəl 11)" if lang_upper == "AZ" else ("Негабаритный груз (Таблица 11)" if lang_upper == "RU" else "Oversized cargo (Table 11)")
    elif table_num == 7:
        if any(k in input_lower for k in ["транспортер", "transportyor", "transporter"]) or "transporter" in wagon_type:
            wagon_disp_name = "Transportyor" if lang_upper == "AZ" else ("Транспортер" if lang_upper == "RU" else "Transporter")
        elif "passenger" in wagon_type or "sərnişin" in wagon_type:
            wagon_disp_name = "Sərnişin vaqonu" if lang_upper == "AZ" else ("Пассажирский вагон" if lang_upper == "RU" else "Passenger wagon")
        else:
            wagon_disp_name = "Xırda göndərmə" if lang_upper == "AZ" else ("Малотоннажная отправка" if lang_upper == "RU" else "Small chunk shipment")
    elif table_num == 6:
        wagon_disp_name = "Çən vaqonu" if lang_upper == "AZ" else ("Вагон-цистерна" if lang_upper == "RU" else "Tank wagon")
    elif table_num == 5:
        if any(k in input_lower or k in wagon_type for k in ["avtoqatar", "автопоезд", "qoşqu", "прицеп", "semitrailer", "yarımqoşqu", "kuzov", "кузов"]):
            wagon_disp_name = "Xüsusi platforma (avtoqatar/qoşqu)" if lang_upper == "AZ" else ("Спецплатформа (автопоезд/прицеп)" if lang_upper == "RU" else "Special platform (road train/trailer)")
        else:
            wagon_disp_name = f"İzotermik vaqon{sec_info}" if lang_upper == "AZ" else (f"Изотермический вагон{sec_info}" if lang_upper == "RU" else f"Isothermal wagon{sec_info}")
    else:
        wagon_disp_name = "Universal vaqon" if lang_upper == "AZ" else ("Универсальный вагон" if lang_upper == "RU" else "Universal wagon")

    gng_label = "GNG" if lang_upper != "EN" else "NHM"
    cargo_wagon_display = f"{gng_label} {gng} - {cargo_name_nlu}, {wagon_disp_name} ({park_display})" if (cargo_name_nlu and cargo_name_nlu != gng) else (f"{gng_label} {gng}, {wagon_disp_name} ({park_display})" if gng else f"{wagon_disp_name} ({park_display})")
    period_str = f"{year}-cı fraxt ili" if lang_upper == "AZ" else (f"{year} фрахтовый год" if lang_upper == "RU" else f"{year} freight year")

    return {
        "part1": {
            "route": route_display, 
            "shipment_type": shipment_type_display, 
            "distance": dist_display,
            "cargo_and_wagon": cargo_wagon_display, 
            "weight_info": weight_display, 
            "period": period_str
        },
        "part2": {
            "exchange_rate": exchange_display, 
            "base_tariff": base_tariff_display,
            "coefficients": [{"name": c_name, "value": str(c_val)} for c_name, c_val in coeffs]
        },
        "part3": {
            "formula": formula_str, 
            "net_ady_rate": f"{final_rate:.2f} {unit_str}",
            "express_rate": express_rate_str, 
            "notes": notes
        }
    }

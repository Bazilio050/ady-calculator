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
    parse_date_from_string,
    should_apply_150_coeff,
    get_transporter_min_weight,
    is_long_platform_scep,
    is_asco_ferry_route,
    calculate_asco_ferry_tariff
)

from tables.table_3 import calculate_table_3_base, get_table_3_coefficients
from tables.table_4 import calculate_table_4_base, get_table_4_coefficients
from tables.table_5 import calculate_table_5_base, get_table_5_coefficients
from tables.table_6 import calculate_table_6_base, get_table_6_coefficients
from tables.table_7 import calculate_table_7_base, get_table_7_coefficients
from guarded_codes import is_cargo_guarded
from tables.table_8 import calculate_table_8_tariff
from tables.table_10 import calculate_table_10_tariff
from tables.table_11 import calculate_table_11_tariff
from tables.table_12 import calculate_table_12_base

EMPTY_SPS_CODES = ["99210000", "99213000", "99220000", "99223000"]
OWN_AXLE_GNG_CODES = ["8601", "8602", "8603", "8604", "8605", "8606", "99211000", "99212000", "99214000", "99221000", "99222000", "99224000"]


def format_clean_gng(gng_code: str) -> str:
    """Корректно форматирует код ГНГ: дополняет нулями СПРАВА до 8 цифр."""
    digits = re.sub(r'\D', '', str(gng_code or ""))
    if not digits:
        return ""
    if len(digits) < 8:
        return digits.ljust(8, '0')
    return digits[:8]


def check_dangerous_goods_rule(gng_code: str, user_input_raw: str, wagon_type: str, lang: str = "AZ") -> tuple:
    clean_gng = format_clean_gng(gng_code)
    inp = str(user_input_raw or "").lower()
    w_type = str(wagon_type or "").lower()
    lang_upper = str(lang or "AZ").upper()
    
    is_danger_flag = any(k in inp for k in ["опасный", "təhlükəli", "dangerous", "un_code", "класс 1", "класс 5", "класс 6", "класс 7"])

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
                        if bmt_no and bmt_no != "0000" and bmt_no in inp:
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
            if "1230" not in clean_gng and "1230" not in inp:
                apply_double = True
        elif t_type == "ortulu_konteyner" and any(k in w_type for k in ["container", "крыт", "örtülü", "universal", "платфор"]):
            apply_double = True

        sec_word = "bənd" if lang_upper == "AZ" else ("п." if lang_upper == "RU" else "cl.")
        tbl_word = "Cədvəl" if lang_upper == "AZ" else ("Таблица" if lang_upper == "RU" else "Table")
        bmt_str = matched_entry[0] if matched_entry else ('spesifik' if lang_upper == "AZ" else ('специфический' if lang_upper == "RU" else 'specific'))

        note_text = (
            f"Təhlükəli yük ({sec_word} 3.6.1, {tbl_word} 13, BMT {bmt_str})" if lang_upper == "AZ" else
            (f"Опасный груз ({sec_word} 3.6.1, {tbl_word} 13, ООН {bmt_str})" if lang_upper == "RU" else
             f"Dangerous cargo ({sec_word} 3.6.1, {tbl_word} 13, UN {bmt_str})")
        )

        return True, apply_double, note_text

    return False, False, ""


def detect_oversize_group(nlu_data: dict, user_input_raw: str) -> str:
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
    raw_gng = str(nlu_data.get("gng_code") or nlu_data.get("cargo_gng_code") or "").strip()
    gng = re.sub(r'\D', '', raw_gng)
    clean_gng = format_clean_gng(gng)
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    
    if not origin_esr:
        st_from_raw = str(nlu_data.get("origin_name") or nlu_data.get("route_from") or "")
        origin_esr = resolve_esr_by_station_name(st_from_raw, user_input_raw) or str(nlu_data.get("origin_esr") or "")
    if not dest_esr:
        st_to_raw = str(nlu_data.get("dest_name") or nlu_data.get("route_to") or "")
        dest_esr = resolve_esr_by_station_name(st_to_raw, user_input_raw) or str(nlu_data.get("dest_esr") or "")

    input_lower = user_input_raw.lower()
    is_empty = nlu_data.get("is_empty", False) or any(k in input_lower for k in ["boş", "порожн", "empty"])

    req_period = nlu_data.get("requested_period")
    target_dt = parse_date_from_string(req_period) if req_period else None
    if not target_dt:
        target_dt = datetime.now()

    is_valid_index_period = datetime(2026, 3, 1) <= target_dt <= datetime(2026, 12, 31)

    if not is_empty and is_valid_index_period and table_num not in [3.72, 3.78, 3.9, 3.91]:
        ind_label = "Əlavə əmsal" if lang == "AZ" else ("Индексация" if lang == "RU" else "Indexation")
        coeffs.append((ind_label, 1.015))
        
        ind_note = (
            "Yüklü vaqonların daşınmasına 1.015 əlavə əmsalı (indeksasiya) tətbiq olunmuşdur (01.03.2026 - 31.12.2026)."
            if lang == "AZ" else
            ("К перевозке гружёных вагонов применён дополнительный коэффициент (индексация) 1.015 (01.03.2026 - 31.12.2026)."
             if lang == "RU" else
             "Additional indexation factor 1.015 applied for loaded wagon movement (01.03.2026 - 31.12.2026).")
        )
        notes.append(ind_note)
        
    if is_empty and clean_gng in EMPTY_SPS_CODES and table_num not in [3.71, 3.72, 3.78]:
        if shipment_type_code in ["import", "export"]:
            lbl_150 = "İdxal/İxrac baza" if lang == "AZ" else ("Импорт/Экспорт база" if lang == "RU" else "Import/Export base")
            coeffs.append((lbl_150, 1.50))
            note_150 = (
                "Boş vaqonların İdxal/İxrac daşınmasına 1.50 əmsalı tətbiq olunmuşdur." if lang == "AZ" else
                ("К перевозке порожних вагонов на импорт/экспорт применён коэффициент 1.50." if lang == "RU" else
                 "Base factor 1.50 applied for empty wagon import/export movement.")
            )
            notes.append(note_150)
    else:
        if table_num not in [3.71, 3.72, 3.78] and should_apply_150_coeff(shipment_type_code, table_num, gng, wagon_type, park_type):
            lbl_150 = "İdxal/İxrac baza" if lang == "AZ" else ("Импорт/Экспорт база" if lang == "RU" else "Import/Export base")
            coeffs.append((lbl_150, 1.50))
            note_base150 = (
                "Baza tarifinə İdxal/İxrac üzrə 1.50 əmsalı tətbiq olunmuşdur." if lang == "AZ" else
                ("К базовому тарифу применён коэффициент импорта/экспорта 1.50." if lang == "RU" else
                 "Base tariff factor 1.50 applied for import/export movement.")
            )
            notes.append(note_base150)

    if table_num == 3:
        tbl_coeffs, tbl_notes = get_table_3_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 4:
        tbl_coeffs, tbl_notes = get_table_4_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=gng, lang=lang, ui_t=ui_t)
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

    if nlu_data.get("is_passenger_train") or "пассажирский поезд" in input_lower or "sərnişin qatarı" in input_lower:
        pass_lbl = "Sərnişin qatarı əmsalı (bənd 3.7.3)" if lang == "AZ" else ("Пассажирский поезд (п. 3.7.3)" if lang == "RU" else "Passenger train (cl. 3.7.3)")
        coeffs.append((pass_lbl, 2.00))
        pass_note = (
            "Hərəkət tərkibinin sərnişin qatarı tərkibində daşınmasına 2.00 əmsalı tətbiq edilmişdir (bənd 3.7.3)." if lang == "AZ" else
            ("К перевозке подвижного состава в составе пассажирского поезда применён коэффициент 2.00 (п. 3.7.3)." if lang == "RU" else
             "Factor 2.00 applied for movement within passenger train (clause 3.7.3).")
        )
        notes.append(pass_note)

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
            ov_lbl = "Əndazəsizlik (6-cı dərəcə / 5 aşağı-yan)" if lang == "AZ" else ("Негабаритность (6-я степень / 5 нижн-боков)" if lang == "RU" else "Oversize (degree 6 / 5 low-side)")
            coeffs.append((ov_lbl, 3.00))
            ov_note = (
                "Транспортерdə 6-cı dərəcəli və ya 5 aşağı/yan əndazəsiz yükə 3.00 əmsalı tətbiq olunmuşdur (bənd 3.5.1.3 / 3.5.1.5)." if lang == "AZ" else
                ("На транспортере для 6-й степени или 5 нижней/боковой негабаритности применён коэффициент 3.00 (п. 3.5.1.3 / 3.5.1.5)." if lang == "RU" else
                 "Factor 3.00 applied for degree 6 or 5 low/side oversize on transporter (clause 3.5.1.3 / 3.5.1.5).")
            )
            notes.append(ov_note)
        elif oversize_grp == "deg3_5_lowside":
            ov_lbl = "Əndazəsizlik (3-4 aşağı, 4 yan)" if lang == "AZ" else ("Негабаритность (3-4 нижн, 4 боков)" if lang == "RU" else "Oversize (3-4 lower, 4 side)")
            coeffs.append((ov_lbl, 2.00))
            ov_note = (
                "Транспортерdə 3-4 aşağı və ya 4 yan dərəcəli əndazəsiz yükə 2.00 əmsalı tətbiq olunmuşdur (bənd 3.5.1.3)." if lang == "AZ" else
                ("На транспортере для 3-4 нижней или 4 боковой негабаритности применён коэффициент 2.00 (п. 3.5.1.3)." if lang == "RU" else
                 "Factor 2.00 applied for 3-4 lower or 4 side oversize on transporter (clause 3.5.1.3).")
            )
            notes.append(ov_note)
        elif oversize_grp == "deg3_upper":
            ov_lbl = "Əndazəsizlik (3 yuxarı)" if lang == "AZ" else ("Негабаритность (3 верхняя)" if lang == "RU" else "Oversize (3rd upper)")
            coeffs.append((ov_lbl, 1.50))
            ov_note = (
                "Транспортерdə 3-cü yuxarı dərəcəli əndazəsiz yükə 1.50 əmsalı tətbiq olunmuşdur (bənd 3.5.1.3)." if lang == "AZ" else
                ("На транспортере для 3-й верхней негабаритности применён коэффициент 1.50 (п. 3.5.1.3)." if lang == "RU" else
                 "Factor 1.50 applied for 3rd upper oversize on transporter (clause 3.5.1.3).")
            )
            notes.append(ov_note)

    if table_num not in [5, 11, 3.71, 3.72, 3.78, 3.9, 3.91] and is_long_platform_scep(user_input_raw, wagon_type):
        if not is_empty:
            lbl_19m = "Sintez platforma >19m" if lang == "AZ" else ("Спецплатформа >19м" if lang == "RU" else "Special platform >19m")
            coeffs.append((lbl_19m, 1.20))
            note_19m = (
                "Qoşqu oxları 19m-dən artıq olan platformalar üçün 1.20 əmsalı tətbiq edilmişdir." if lang == "AZ" else
                ("Для платформ с базой осей более 19м применён коэффициент 1.20." if lang == "RU" else
                 "Factor 1.20 applied for platforms with axle distance exceeding 19m.")
            )
            notes.append(note_19m)
        elif park_type == "SPS":
            lbl_empty_19m = "Boş platforma >19m" if lang == "AZ" else ("Скидка порожн. >19м" if lang == "RU" else "Empty platform >19m")
            coeffs.append((lbl_empty_19m, 0.60))
            
    g_coeffs, g_notes = get_global_coefficients(shipment_type_code, gng, origin_esr, dest_esr, lang)
    coeffs.extend(g_coeffs)
    notes.extend(g_notes)

    if park_type == "SPS" and table_num not in [3.72, 3.78, 3.9, 3.91]:
        sps_val = 0.85
        apply_sps = False

        if table_num in [3, 4, 5, 7, 8, 10, 11, 12, 3.71, 3.8]:
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

    is_danger, apply_double, danger_note = check_dangerous_goods_rule(gng, user_input_raw, wagon_type, lang)
    if is_danger and apply_double:
        danger_lbl = "Təhlükəli yük əmsalı (x2.00)" if lang == "AZ" else ("Опасный груз (x2.00)" if lang == "RU" else "Dangerous goods (x2.00)")
        coeffs.append((danger_lbl, 2.00))
        danger_note_str = (
            "Təhlükəli yüklərin daşınmasına görə tarif dərəcələrinə 2.00 əmsalı tətbiq olunmuşdur (bənd 3.6.1)." if lang == "AZ" else
            ("К тарифным ставкам за перевозку опасных грузов применён коэффициент 2.00 (п. 3.6.1)." if lang == "RU" else
             "Factor 2.00 applied to tariff rates for dangerous cargo movement (clause 3.6.1).")
        )
        notes.append(danger_note_str)

    if any(k in input_lower for k in ["прикрытие", "qoruyucu", "daldalanacaq", "guard_wagon"]):
        cover_rate = 0.30 if park_type == "SPS" else 0.35
        axles = float(nlu_data.get("axles_count") or 4)
        match_axle = re.search(r'(\d+)\s*(?:oxlu|осн|axle|осей)', input_lower)
        if match_axle:
            axles = int(match_axle.group(1))
        cover_chf = cover_rate * axles * dist_km
        
        sec_w = "bənd" if lang == "AZ" else ("п." if lang == "RU" else "cl.")
        ox_w = "ox" if lang == "AZ" else ("ось" if lang == "RU" else "axle")
        
        c_note = (
            f"Qoruyucu (daldalanacaq) vaqonunun daşınma haqqı {sec_w} 3.6.3-ə əsasən ({cover_rate} CHF × {int(axles)} {ox_w} × {dist_km} km = {cover_chf:.2f} CHF) əlavə olunmuşdur." if lang == "AZ" else
            (f"Плата за вагон прикрытия начислена согласно {sec_w} 3.6.3 ({cover_rate} CHF × {int(axles)} {ox_w} × {dist_km} км = {cover_chf:.2f} CHF)." if lang == "RU" else
             f"Guard wagon fee added according to {sec_w} 3.6.3 ({cover_rate} CHF × {int(axles)} {ox_w} × {dist_km} km = {cover_chf:.2f} CHF).")
        )
        notes.append(c_note)

    return coeffs, notes


def process_full_calculation(nlu_data: dict, user_input_raw: str, lang: str, year: str, ui_t: dict) -> dict:
    lang_upper = str(lang or "AZ").upper()
    input_lower = str(user_input_raw or "").lower()
    
    # 1. Позиционное определение станций строго по порядку ввода в тексте
    station_patterns = [
        (r'б[её]юк\s*к[аяе]сик|beyuk\s*kasik|boyuk\s*kesik', "Böyük Kəsik", "558701"),
        (r'ялама|yalama', "Yalama", "545006"),
        (r'астара|astara', "Astara", "554109"),
        (r'курык|kuryk|kurik|quruq', "Ələt eksport-Kurik", "553002"),
        (r'актау|aktau|aqtau', "Ələt eksport-Aktau", "549204"),
        (r'туркменбаши|turkmenbashi|türkmenbaşı|\bтрк\b|\btrk\b', "Ələt eksport-Türk.", "548803"),
        (r'баку|baku|bakı', "Bakı", "547001"),
        (r'абшерон|апшерон|absheron', "Abşeron", "548004"),
        (r'алят|alat|ələt', "Ələt", "548502")
    ]

    found_matches = []
    for pattern, s_name, s_esr in station_patterns:
        m = re.search(pattern, input_lower)
        if m:
            found_matches.append((m.start(), s_name, s_esr))

    found_matches.sort(key=lambda x: x[0])

    if len(found_matches) >= 2:
        st_from_raw, origin_esr = found_matches[0][1], found_matches[0][2]
        st_to_raw, dest_esr = found_matches[1][1], found_matches[1][2]
    elif len(found_matches) == 1:
        st_from_raw, origin_esr = found_matches[0][1], found_matches[0][2]
        st_to_raw = str(nlu_data.get("dest_name") or nlu_data.get("route_to") or "")
        dest_esr = resolve_esr_by_station_name(st_to_raw, user_input_raw) or str(nlu_data.get("dest_esr") or "")
    else:
        st_from_raw = str(nlu_data.get("origin_name") or nlu_data.get("route_from") or "")
        st_to_raw = str(nlu_data.get("dest_name") or nlu_data.get("route_to") or "")
        origin_esr = resolve_esr_by_station_name(st_from_raw, user_input_raw) or str(nlu_data.get("origin_esr") or "")
        dest_esr = resolve_esr_by_station_name(st_to_raw, user_input_raw) or str(nlu_data.get("dest_esr") or "")

    ferry_ports = ["553002", "549204", "548803"]
    if origin_esr in ferry_ports or dest_esr in ferry_ports:
        nlu_data["is_asco_ferry"] = True

    raw_gng = str(nlu_data.get("gng_code") or nlu_data.get("cargo_gng_code") or "").strip()
    gng = re.sub(r'\D', '', raw_gng)
    clean_gng = format_clean_gng(gng)
    cargo_name_nlu = str(nlu_data.get("gng_name") or nlu_data.get("cargo_name") or "").strip()

    if any(w in cargo_name_nlu.lower() for w in ["qapalı vaqon", "крытый вагон", "полувагон", "платформа"]):
        cargo_name_nlu = "Buğda" if gng == "1001" else ""

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

    if origin_esr in ferry_ports or dest_esr in ferry_ports:
        shipment_type_code = explicit_mode or "transit"
        shipment_type_display = ui_t.get("type_transit", "Tranzit daşınması" if lang_upper == "AZ" else ("Транзитная перевозка" if lang_upper == "RU" else "Transit shipment"))
    elif explicit_mode in ["import", "export", "transit"]:
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
    dist_display = f"{actual_dist_km} km (min. {tariff_dist_km} km)" if tariff_dist_km != actual_dist_km else f"{actual_dist_km} km"

    is_empty_wagon = nlu_data.get("is_empty", False) or any(k in input_lower for k in ["boş", "порожн", "empty"])
    is_cover_wagon = any(k in input_lower for k in ["прикрытие", "qoruyucu", "daldalanacaq", "guard_wagon"])

    is_own_axles = bool(nlu_data.get("is_own_axles")) or any(k in input_lower for k in ["öz ox", "на своих осях", "локомотив", "кран"]) or (clean_gng[:4] in ["8601", "8602", "8603", "8604", "8605", "8606"])
    is_in_repair = bool(nlu_data.get("is_in_repair")) or any(k in input_lower for k in ["təmir", "ремонт", "repair"])
    is_consolidated = bool(nlu_data.get("is_consolidated")) or any(k in input_lower for k in ["yığma", "сборный", "сборная"])

    escort_count = int(nlu_data.get("escort_count") or 0)
    match_escort = re.search(r'(\d+)\s*(?:bələdçi|проводник|проводника|водител)', input_lower)
    if match_escort and escort_count == 0:
        escort_count = int(match_escort.group(1))

    has_teplushka = bool(nlu_data.get("has_teplushka")) or any(k in input_lower for k in ["tepluşka", "теплушка", "вагон сопровождения"])
    teplushka_type = str(nlu_data.get("teplushka_type") or "freight_sps").lower()

    table_5_keywords = ["ref", "реф", "thermos", "термос", "изотерм", "auto", "авто", "avtoqatar", "автопоезд", "qoşqu", "прицеп", "semitrailer", "yarımqoşqu", "kuzov", "кузов", "inv", "anv"]
    is_table_5_object = any(k in wagon_type for k in table_5_keywords) or (ref_wagons_cnt is not None) or any(k in input_lower for k in table_5_keywords)

    sec_word = "bənd" if lang_upper == "AZ" else ("п." if lang_upper == "RU" else "cl.")
    axle_word = "ox" if lang_upper == "AZ" else ("ось" if lang_upper == "RU" else "axle")

    if has_teplushka:
        table_num = 3.9
        is_per_wagon = True
        axles = float(nlu_data.get("axles_count") or 4)
        match_axle = re.search(r'(\d+)\s*(?:oxlu|осн|axle|осей)', input_lower)
        if match_axle:
            axles = int(match_axle.group(1))

        teplushka_rates = {
            "freight_mps": 0.23,
            "freight_sps": 0.20,
            "passenger_mps": 0.35,
            "passenger_sps": 0.30
        }
        rate_per_axle_km = teplushka_rates.get(teplushka_type, 0.20)
        base_chf = rate_per_axle_km * axles * tariff_dist_km
        table_details = f"{sec_word} 3.9 ({rate_per_axle_km:.2f} CHF × {int(axles)} {axle_word} × {tariff_dist_km} km)"
        weight_display = "0 t (tepluşka)" if lang_upper == "AZ" else ("0 т (теплушка)" if lang_upper == "RU" else "0 t (escort wagon)")
        billable_weight = 0.0

    elif escort_count > 0 and act_weight == 0:
        table_num = 3.91
        is_per_wagon = True
        units_100km = math.ceil(tariff_dist_km / 100.0)
        base_chf = escort_count * units_100km * 12.00
        
        escort_word = "bələdçi" if lang_upper == "AZ" else ("проводник" if lang_upper == "RU" else "attendant")
        table_details = f"{sec_word} 3.9 ({escort_count} {escort_word} × {units_100km} × 100km × 12.00 CHF)"
        weight_display = f"{escort_count} bələdçi" if lang_upper == "AZ" else (f"{escort_count} проводник(ов)" if lang_upper == "RU" else f"{escort_count} attendant(s)")
        billable_weight = 0.0

    elif is_own_axles and is_in_repair and park_type == "MPS":
        table_num = 3.72
        is_per_wagon = True
        axles = float(nlu_data.get("axles_count") or 4)
        match_axle = re.search(r'(\d+)\s*(?:oxlu|осн|axle|осей)', input_lower)
        if match_axle:
            axles = int(match_axle.group(1))
        
        base_chf = 0.10 * axles * tariff_dist_km
        table_details = f"{sec_word} 3.7.2 (0.10 CHF × {int(axles)} {axle_word} × {tariff_dist_km} km)"
        weight_display = "0 t (təmirə/təmirdən)" if lang_upper == "AZ" else ("0 т (в/из ремонта)" if lang_upper == "RU" else "0 t (to/from repair)")
        billable_weight = 0.0

    elif is_empty_wagon and ("transporter" in wagon_type or "транспортер" in input_lower or "transportyor" in input_lower):
        table_num = 3.78
        is_per_wagon = True
        axles = int(nlu_data.get("axles_count") or 4)
        match_axle = re.search(r'(\d+)[-\s]*(?:oxlu|ox|осн|осей|оси|axle|осный)', input_lower)
        if match_axle:
            axles = int(match_axle.group(1))

        if axles <= 4:
            rate_per_axle_km = 0.12
        elif axles <= 8:
            rate_per_axle_km = 0.23
        elif axles <= 20:
            rate_per_axle_km = 0.35
        else:
            rate_per_axle_km = 0.40

        base_chf = rate_per_axle_km * axles * tariff_dist_km
        table_details = f"{sec_word} 3.7.8 ({rate_per_axle_km:.2f} CHF × {int(axles)} {axle_word} × {tariff_dist_km} km)"
        weight_display = f"0 t (boş {int(axles)}-oxlu transportyor)" if lang_upper == "AZ" else (f"0 т (порожний {int(axles)}-осный транспортер)" if lang_upper == "RU" else f"0 t (empty {int(axles)}-axle transporter)")
        billable_weight = 0.0

    elif is_own_axles:
        table_num = 3.71
        is_per_wagon = False
        billable_weight = max(10.0, act_weight)
        
        if shipment_type_code == "transit":
            base_chf, table_details = calculate_table_4_base(tariff_dist_km, billable_weight, {}, lang_upper)
        else:
            base_chf, table_details = calculate_table_3_base(tariff_dist_km, billable_weight, {}, lang_upper)

        base_chf *= 0.50
        u_wagon_str = "universal vaqon" if lang_upper == "AZ" else ("универсальный вагон" if lang_upper == "RU" else "universal wagon")
        table_details = f"{sec_word} 3.7.1 ({u_wagon_str} × 0.50)"
        weight_display = f"{int(act_weight if act_weight > 0 else 10)} t (öz oxları üzərində)" if lang_upper == "AZ" else (f"{int(act_weight if act_weight > 0 else 10)} т (на своих осях)" if lang_upper == "RU" else f"{int(act_weight if act_weight > 0 else 10)} t (on own axles)")

    elif is_empty_wagon and park_type == "MPS" and not is_cover_wagon:
        empty_note = {
            "AZ": "İnventar parka mənsub olan boş vaqonlar boşaldıqdan sonra mensub olduqları ölkələrə qaytarıldıqları zaman daşıma haqqı hesablanmır (bənd 3.1.1).",
            "RU": "Возврат порожних инвентарных вагонов (МПС) к месту приписки осуществляется бесплатно (п. 3.1.1).",
            "EN": "Return of empty inventory wagons (MPS) to owner countries is free of charge (clause 3.1.1)."
        }
        return {
            "part1": {
                "route": route_display, "shipment_type": shipment_type_display, "distance": dist_display,
                "cargo_and_wagon": "Boş MPS vaqon / Порожний вагон МПС" if lang_upper != "EN" else "Empty MPS wagon",
                "weight_info": "0 t", "period": f"{year}"
            },
            "part2": {
                "exchange_rate": "0.79 CHF/USD", "base_tariff": "0.00 CHF", "coefficients": []
            },
            "part3": {
                "formula": "0.00 CHF / USD", "net_ady_rate": "0.00 USD",
                "express_rate": "0.00 USD", "guard_rate": None, "notes": [empty_note.get(lang_upper, empty_note["AZ"])]
            }
        }

    elif is_cover_wagon:
        table_num = 3.63
        is_per_wagon = True
        axles = float(nlu_data.get("axles_count") or 4)
        match_axle = re.search(r'(\d+)\s*(?:oxlu|осн|axle|осей)', input_lower)
        if match_axle:
            axles = int(match_axle.group(1))
        
        cover_rate = 0.30 if park_type == "SPS" else 0.35
        base_chf = cover_rate * axles * actual_dist_km
        table_details = f"{sec_word} 3.6.3 ({cover_rate} CHF × {int(axles)} {axle_word} × {actual_dist_km} km)"
        weight_display = "0 t (qoruyucu)" if lang_upper == "AZ" else ("0 т (прикрытие)" if lang_upper == "RU" else "0 t (guard wagon)")
        billable_weight = 0.0

    elif is_empty_wagon and clean_gng in EMPTY_SPS_CODES and not is_table_5_object and "container" not in wagon_type:
        table_num = 3.22
        is_per_wagon = True
        axles = float(nlu_data.get("axles_count") or 4)
        base_chf = 0.10 * axles * tariff_dist_km
        table_details = f"{sec_word} 3.2.2 (0.10 CHF × {int(axles)} {axle_word} × {tariff_dist_km} km)"
        weight_display = "0 t (boş)" if lang_upper == "AZ" else ("0 т (порожний)" if lang_upper == "RU" else "0 t (empty)")
        billable_weight = 0.0

    else:
        is_danger, _, _ = check_dangerous_goods_rule(gng, user_input_raw, wagon_type, lang_upper)
        is_tanker_type = any(k in wagon_type for k in ["cistern", "цистерн", "tank", "çən", "bunker", "бункер"]) and "container" not in wagon_type
        oversize_group = detect_oversize_group(nlu_data, user_input_raw)

        if oversize_group in ["deg3_upper", "deg3_5_lowside"]:
            table_num = 11
            billable_weight = max(10.0, act_weight)
            res_t11 = calculate_table_11_tariff(tariff_dist_km, billable_weight, oversize_group)
            base_chf = res_t11["base_chf"]
            tbl_word = "Cədvəl" if lang_upper == "AZ" else ("Таблица" if lang_upper == "RU" else "Table")
            table_details = f"{tbl_word} 11 ({res_t11['column_info']})"
            is_per_wagon = (res_t11["rate_type"] == "per_wagon")

        else:
            if is_consolidated:
                min_cons_weight = 25.0 if is_table_5_object else 10.0
                billable_weight = max(min_cons_weight, act_weight)
            elif oversize_group == "small_deg":
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

            if is_consolidated:
                table_num = 3.8
                is_per_wagon = False
                if shipment_type_code == "transit":
                    base_chf, table_details = calculate_table_4_base(tariff_dist_km, billable_weight, {}, lang_upper)
                else:
                    base_chf, table_details = calculate_table_3_base(tariff_dist_km, billable_weight, {}, lang_upper)

            elif is_danger and not is_tanker_type and not is_universal_container:
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
            weight_display = f"{act_w_str} t (min. {bill_w_str} t)" if lang_upper != "RU" else f"{act_w_str} т (мин. {bill_w_str} т)"
        else:
            weight_display = f"{act_w_str} t" if lang_upper != "RU" else f"{act_w_str} т"

        if base_chf is None:
            base_chf = 1200.0
            tbl_word = "Cədvəl" if lang_upper == "AZ" else ("Таблица" if lang_upper == "RU" else "Table")
            table_details = f"{tbl_word} 3 (baza)" if lang_upper == "AZ" else (f"{tbl_word} 3 (базовая)" if lang_upper == "RU" else f"{tbl_word} 3 (base)")

    unit_str = ui_t.get("unit_wagon", "USD/vaqon") if is_per_wagon else ui_t.get("unit_ton", "USD/t")
    chf_unit = "CHF/вагон" if (is_per_wagon and lang_upper == "RU") else ("CHF/vaqon" if is_per_wagon else ("CHF/т" if lang_upper == "RU" else ("CHF/wagon" if is_per_wagon else "CHF/t")))

    base_tariff_display = f"**{base_chf:.2f} {chf_unit}** ({table_details})"
    usd_rate, exchange_display = get_currency_rate(nlu_data.get("requested_period"), lang_upper)

    is_ref_type_check = (table_num == 5)
    
    coeffs, notes = apply_special_exceptions(
        nlu_data=nlu_data, 
        shipment_type_code=shipment_type_code, 
        table_num=table_num, 
        is_ref_type=is_ref_type_check, 
        act_weight=act_weight, 
        billable_weight=billable_weight, 
        dist_km=actual_dist_km, 
        user_input_raw=user_input_raw, 
        lang=lang_upper, 
        ui_t=ui_t, 
        ref_wagons_cnt=ref_wagons_cnt,
        origin_esr=origin_esr, 
        dest_esr=dest_esr
    )

    if is_consolidated:
        cons_note = (
            "Yığma göndərmə üçün minimum hesablaşma çəkisi norması tətbiq olunmuşdur (bənd 3.8)."
            if lang_upper == "AZ" else
            ("Для сборной отправки применена минимальная норма расчётного веса (п. 3.8)." if lang_upper == "RU" else
             "Minimum billable weight norm applied for consolidated shipment (clause 3.8).")
        )
        notes.insert(0, cons_note)

    if not is_empty_wagon and act_weight > 0 and act_weight < billable_weight and not is_consolidated:
        weight_note = (
            f"Minimum hesablama çəkisi norması {int(billable_weight)} ton tətbiq olunmuşdur."
            if lang_upper == "AZ" else
            (f"Применена минимальная норма расчётного веса {int(billable_weight)} тонн." if lang_upper == "RU" else
             f"Minimum billable weight norm {int(billable_weight)} tons applied.")
        )
        notes.insert(0, weight_note)

    final_rate = base_chf / usd_rate
    formula_parts = [f"{base_chf:.2f} / {usd_rate:.2f}"]
    for _, c_val in coeffs:
        final_rate *= float(c_val)
        formula_parts.append(f"{c_val}")

    formula_str = " × ".join(formula_parts) + f" = {final_rate:.2f} {unit_str}"
    express_rate_str = f"{final_rate * 1.02:.2f} {unit_str}"

    gng_digits = re.sub(r'\D', '', str(gng or ""))
    gng_4 = gng_digits[:4] if len(gng_digits) >= 4 else gng_digits
    gng_8_right = gng_digits.ljust(8, '0')[:8] if gng_digits else ""
    gng_8_left = gng_digits.zfill(8) if gng_digits else ""

    cargo_is_guarded = (
        is_cargo_guarded(gng) 
        or is_cargo_guarded(clean_gng) 
        or is_cargo_guarded(gng_digits) 
        or is_cargo_guarded(gng_4)
        or is_cargo_guarded(gng_8_right)
        or is_cargo_guarded(gng_8_left)
    )
    guard_fee_express_usd = 0.0

    if cargo_is_guarded and shipment_type_code == "transit":
        base_guard = (actual_dist_km * 0.1) / 1.7
        guard_fee_express_usd = round(base_guard * 1.02, 2)
        
        guard_note_text = (
            "Yük ADY-nin siyahısına əsasən mühafizəyə tabedir (Tranzit: km * 0.1 AZN / 1.7 + 2%)." 
            if lang_upper == "AZ" else 
            ("Груз подлежит охране согласно списку ADY (Транзит: км * 0.1 AZN / 1.7 + 2%)."
             if lang_upper == "RU" else
             "Cargo is subject to guard according to ADY list (Transit: km * 0.1 AZN / 1.7 + 2%).")
        )
        notes.append(guard_note_text)

    asco_result_display = None
    if nlu_data.get("is_asco_ferry") or is_asco_ferry_route(origin_esr, dest_esr, st_from_raw, st_to_raw, user_input_raw):
        asco_data = calculate_asco_ferry_tariff(nlu_data, user_input_raw)
        if asco_data:
            ferry_usd = asco_data.get("ferry_rate_usd", 1200.0)
            unit_str_asco = "USD/vaqon" if lang_upper == "AZ" else ("USD/вагон" if lang_upper == "RU" else "USD/wagon")
            
            # app.py ожидает именно словарь с ключами line_title и rate:
            asco_result_display = {
                "line_title": "ASCO Bərə daşıma haqqı" if lang_upper == "AZ" else ("Морской фрахт ASCO" if lang_upper == "RU" else "ASCO Ferry rate"),
                "rate": f"{ferry_usd:.2f} {unit_str_asco}",
                "value": ferry_usd
            }
            if asco_data.get("note"):
                notes.append(asco_data["note"])

    park_display = "SPS" if park_type == "SPS" else "MPS"
    sec_info = f" ({ref_wagons_cnt}+1)" if ref_wagons_cnt else ""

    if table_num == 3.9:
        wagon_disp_name = "Tepluşka (vaqon müşayiəti)" if lang_upper == "AZ" else ("Теплушка (вагон сопровождения)" if lang_upper == "RU" else "Teplushka (escort wagon)")
    elif table_num == 3.91:
        wagon_disp_name = "Yük müşayiəti (bələdçi)" if lang_upper == "AZ" else ("Сопровождение груза (проводники)" if lang_upper == "RU" else "Cargo escort (attendants)")
    elif is_own_axles:
        wagon_disp_name = "Öz oxları üzərində" if lang_upper == "AZ" else ("На своих осях" if lang_upper == "RU" else "On own axles")
    elif is_cover_wagon:
        wagon_disp_name = "Qoruyucu vaqon" if lang_upper == "AZ" else ("Вагон прикрытия" if lang_upper == "RU" else "Guard wagon")
    elif is_empty_wagon and clean_gng in EMPTY_SPS_CODES and not is_table_5_object and table_num == 3.22:
        wagon_disp_name = "Boş vaqon" if lang_upper == "AZ" else ("Порожний вагон" if lang_upper == "RU" else "Empty wagon")
    elif table_num == 12:
        wagon_disp_name = "Təhlükəli yük vaqonu (Cədvəl 12)" if lang_upper == "AZ" else ("Вагон с опасным грузом (Таблица 12)" if lang_upper == "RU" else "Dangerous cargo wagon (Table 12)")
    elif table_num == 10:
        wagon_disp_name = "Xüsusi/Tank/Ref konteyner (Cədvəl 10)" if lang_upper == "AZ" else ("Спец/Танк/Ref контейнер (Таблица 10)" if lang_upper == "RU" else "Special/Tank/Ref container (Table 10)")
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

    gng_label = "GNG" if lang_upper == "AZ" else ("ГНГ" if lang_upper == "RU" else "NHM")

    if cargo_name_nlu and cargo_name_nlu.lower() != wagon_disp_name.lower():
        cargo_wagon_display = f"{gng_label} {gng} - {cargo_name_nlu}, {wagon_disp_name} ({park_display})"
    else:
        cargo_wagon_display = f"{gng_label} {gng}, {wagon_disp_name} ({park_display})" if gng else f"{wagon_disp_name} ({park_display})"

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
            "guard_rate": f"{guard_fee_express_usd:.2f} USD" if guard_fee_express_usd > 0 else None,
            "asco_ferry": asco_result_display,
            "notes": notes
        }
    }

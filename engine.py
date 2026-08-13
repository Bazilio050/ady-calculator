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

EMPTY_SPS_CODES = ["99210000", "99213000", "99220000", "99223000"]


def get_currency_rate(requested_period: str = None, lang: str = "AZ") -> tuple:
    target_dt = parse_date_from_string(requested_period)
    rate, period_str = get_exchange_rate_for_date(target_dt)
    
    label = f"**{rate:.2f} CHF/USD** ({period_str})"
    return rate, label


apply_special_exceptions в engine.py на эту версию:

Python
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

    # 1. ИНДЕКСАЦИЯ 1.015 (С 01.04.2026 СТРОГО для всех ГРУЖЁНЫХ вагонов)
    req_period = nlu_data.get("requested_period")
    target_dt = parse_date_from_string(req_period) if req_period else None
    if not target_dt:
        target_dt = datetime.now()

    is_after_april_2026 = target_dt >= datetime(2026, 4, 1)

    if not is_empty and is_after_april_2026:
        ind_label = "Əlavə əmsal 1.015" if lang == "AZ" else ("Индексация 1.015" if lang == "RU" else "Indexation 1.015")
        coeffs.append((ind_label, 1.015))
        
    # 2. ГЛОБАЛЬНЫЙ КОЭФФИЦИЕНТ 1.50
    if is_empty and clean_gng in EMPTY_SPS_CODES:
        if shipment_type_code in ["import", "export"]:
            lbl_150 = "İdxal/İxrac baza 1.50" if lang == "AZ" else ("Импорт/Экспорт база 1.50" if lang == "RU" else "Import/Export base 1.50")
            coeffs.append((lbl_150, 1.50))
            notes.append("Boş vaqonların İdxal/İxrac daşınmasına 1.50 əmsalı tətbiq olunmuşdur.")
    else:
        if should_apply_150_coeff(shipment_type_code, table_num, gng, wagon_type, park_type):
            lbl_150 = "İdxal/İxrac baza 1.50" if lang == "AZ" else ("Импорт/Экспорт база 1.50" if lang == "RU" else "Import/Export base 1.50")
            coeffs.append((lbl_150, 1.50))
            notes.append("Baza tarifinə İdxal/İxrac üzrə 1.50 əmsalı tətbiq olunmuşdur.")

    # 3. Специфические коэффициенты конкретных таблиц
    if table_num == 3:
        tbl_coeffs, tbl_notes = get_table_3_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 4:
        tbl_coeffs, tbl_notes = get_table_4_coefficients(shipment_type=shipment_type_code, wagon_type=wagon_type, gng=gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 5:
        tbl_coeffs, tbl_notes = get_table_5_coefficients(shipment_type=shipment_type_code, wagon_type=wagon_type, gng=gng, ref_wagons_cnt=ref_wagons_cnt, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 6:
        tbl_coeffs, tbl_notes = get_table_6_coefficients(shipment_type=shipment_type_code, wagon_type=wagon_type, gng=gng, park_type=park_type, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 7:
        tbl_coeffs, tbl_notes = get_table_7_coefficients(shipment_type_code=shipment_type_code, wagon_type=wagon_type, gng_code=gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)

    # 3.1.2.7 — Спецплатформы длиннее 19 м
    if is_long_platform_scep(user_input_raw, wagon_type):
        if not is_empty:
            lbl_19m = "Sintez platforma >19m 1.20" if lang == "AZ" else ("Спецплатформа >19м 1.20" if lang == "RU" else "Special platform >19m 1.20")
            coeffs.append((lbl_19m, 1.20))
            notes.append("Qoşqu oxları 19m-dən artıq olan platformalar üçün 1.20 əmsalı tətbiq edilmişdir.")
        elif park_type == "SPS":
            lbl_empty_19m = "Boş platforma >19m 0.60" if lang == "AZ" else ("Скидка порожн. >19м 0.60" if lang == "RU" else "Empty platform >19m 0.60")
            coeffs.append((lbl_empty_19m, 0.60))

    # 4. Общие глобальные коэффициенты
    g_coeffs, g_notes = get_global_coefficients(shipment_type_code, gng, origin_esr, dest_esr, lang)
    coeffs.extend(g_coeffs)
    notes.extend(g_notes)

    # 5. СКИДКА СПС (0.85) + ПРИМЕЧАНИЕ
    if park_type == "SPS" and not (is_empty and clean_gng in EMPTY_SPS_CODES):
        should_apply_sps = False
        
        if table_num in [3, 4, 5, 7]:
            should_apply_sps = True
        elif table_num == 6:
            from tables.table_6 import determine_table_6_column
            col_idx = determine_table_6_column(clean_gng, park_type)
            if col_idx != 6:
                should_apply_sps = True

        if should_apply_sps:
            sps_label = "SPS güzəşti 0.85" if lang == "AZ" else ("Скидка СПС 0.85" if lang == "RU" else "SPS Discount 0.85")
            coeffs.append((sps_label, 0.85))
            
            # 💡 ТЕПЕРЬ ТЕКСТ ПРИМЕЧАНИЯ ДОБАВЛЯЕТСЯ 100%
            sps_note = (
                "Xüsusi mülkiyyətdə olan (SPS) vaqonlara 0.85 güzəşt əmsalı tətbiq edilmişdir."
                if lang == "AZ" else
                ("К приватным вагонам (СПС) применён скидочный коэффициент 0.85."
                 if lang == "RU" else
                 "SPS discount factor 0.85 applied for private wagons.")
            )
            notes.append(sps_note)

    return coeffs, notes

    return coeffs, notes


def nlu_res_data_esr(nlu_data: dict) -> str:
    return str(nlu_data.get("dest_esr") or "")


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

    # Инвентарный порожний вагон МПС -> Бесплатно (п. 3.1.1)
    if is_empty_wagon and park_type == "MPS":
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
    # ПУНКТ 3.2.2: Порожний приватный вагон СПС (0.10 CHF/ось-км)
    # ---------------------------------------------------------
    if is_empty_wagon and clean_gng in EMPTY_SPS_CODES:
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
        # Расчёт веса для гружёных вагонов
        billable_weight = get_min_weight_by_gng(gng, act_weight)

        match_axle = re.search(r'(\d+)\s*(?:oxlu|осн|axle|осей)', input_lower)
        if match_axle:
            axles = int(match_axle.group(1))
            billable_weight = get_transporter_min_weight(axles, billable_weight)

        act_w_str = f"{int(act_weight) if act_weight.is_integer() else act_weight}"
        bill_w_str = f"{int(billable_weight) if billable_weight.is_integer() else billable_weight}"

        if act_weight < billable_weight:
            weight_display = f"{act_w_str} t (min. {bill_w_str} t)"
        else:
            weight_display = f"{act_w_str} t"

        is_ref_type = any(k in wagon_type for k in ["ref", "реф", "thermos", "термос", "изотерм"]) or (ref_wagons_cnt is not None)
        is_tanker_type = any(k in wagon_type for k in ["cistern", "цистерн", "tank", "çən", "bunker", "бункер"])
        is_transporter = any(k in input_lower for k in ["транспортер", "transportyor", "transporter"])

        is_table_7_type = (
            "small_chunk" in wagon_type or "small_chunk" in shipment_kind or
            "passenger" in wagon_type or "sərnişin" in wagon_type or "baggage" in wagon_type or
            clean_gng.startswith("99910000") or
            ("container" in wagon_type and act_weight <= 5.0) or
            is_transporter or "transporter" in wagon_type
        )

        if is_table_7_type:
            table_num = 7
            is_per_wagon = False
            base_chf, table_details = calculate_table_7_base(
                distance_km=tariff_dist_km,
                billable_weight_tons=billable_weight,
                wagon_type=wagon_type,
                container_type=nlu_data.get("container_type"),
                is_empty=is_empty_wagon,
                gng_code=clean_gng,
                lang=lang_upper,
                user_input_raw=user_input_raw
            )
        elif is_tanker_type:
            table_num = 6
            is_per_wagon = False
            base_chf, table_details = calculate_table_6_base(tariff_dist_km, billable_weight, gng, park_type, {}, lang_upper)
        elif is_ref_type:
            table_num = 5
            base_chf, table_details, is_per_wagon = calculate_table_5_base(tariff_dist_km, billable_weight, wagon_type, {}, lang_upper)
        elif shipment_type_code == "transit":
            table_num = 4
            is_per_wagon = False
            base_chf, table_details = calculate_table_4_base(tariff_dist_km, billable_weight, {}, lang_upper)
        else:
            table_num = 3
            is_per_wagon = False
            base_chf, table_details = calculate_table_3_base(tariff_dist_km, billable_weight, {}, lang_upper)

        if base_chf is None:
            base_chf = 1200.0
            table_details = "Таблица 3 (базовая)"

    unit_str = ui_t.get("unit_wagon", "USD/vaqon") if is_per_wagon else ui_t.get("unit_ton", "USD/t")
    chf_unit = "CHF/вагон" if (is_per_wagon and lang_upper == "RU") else ("CHF/vaqon" if is_per_wagon else ("CHF/т" if lang_upper == "RU" else "CHF/t"))

    base_tariff_display = f"**{base_chf:.2f} {chf_unit}** ({table_details})"
    usd_rate, exchange_display = get_currency_rate(nlu_data.get("requested_period"), lang_upper)

    is_ref_type_check = any(k in wagon_type for k in ["ref", "реф", "thermos", "термос", "изотерм"]) or (ref_wagons_cnt is not None)
    
    # ПЕРЕДАЕМ origin_esr и dest_esr ДЛЯ ТОЧНОГО ОПРЕДЕЛЕНИЯ ГЛОБАЛЬНЫХ КОЭФФИЦИЕНТОВ
    coeffs, notes = apply_special_exceptions(
        nlu_data, shipment_type_code, table_num, is_ref_type_check, act_weight, 
        billable_weight, actual_dist_km, user_input_raw, lang_upper, ui_t, ref_wagons_cnt,
        origin_esr, dest_esr
    )

    # 💡 ДОБАВЛЯЕМ ПРИМЕЧАНИЕ О МИНИМАЛЬНОЙ НОРМЕ ВЕСА ПО ГНГ (ЕСЛИ ФАКТ < НОРМЫ)
    if not is_empty_wagon and act_weight > 0 and act_weight < billable_weight:
        weight_note = (
            f"YHN (GNG) {gng} kodlu yük üçün minimum hesablama çəkisi norması {int(billable_weight)} ton tətbiq olunmuşdur."
            if lang_upper == "AZ" else
            (f"Для груза ГНГ {gng} применена минимальная норма расчётного веса {int(billable_weight)} тонн."
             if lang_upper == "RU" else
             f"Minimum billable weight norm of {int(billable_weight)} tons applied for GNG {gng}.")
        )
        notes.insert(0, weight_note)

    # 💡 ДОБАВЛЯЕМ ПРИМЕЧАНИЕ О ПУНКТЕ 3.2.2 СТРОГО ПРИ ПОРОЖНЕМ ПРОБЕГЕ СПС
    if is_empty_wagon and clean_gng in EMPTY_SPS_CODES:
        empty_sps_note = (
            "Xüsusi mülkiyyətdə olan (icarəyə verilmiş) boş vaqonların daşınması tarif siyasətinin 3.2.2 bəndinə əsasən (0.10 CHF/ox-km) hesablanmışdır."
            if lang_upper == "AZ" else
            ("Перевозка порожних приватных (арендованных) вагонов рассчитана согласно п. 3.2.2 Тарифной политики (0.10 CHF/ось-км)."
             if lang_upper == "RU" else
             "Empty private/leased wagon movement is calculated according to clause 3.2.2 of the Tariff Policy (0.10 CHF/axle-km).")
        )
        notes.insert(0, empty_sps_note)

    final_rate = base_chf / usd_rate
    formula_parts = [f"{base_chf:.2f} / {usd_rate:.2f}"]
    for _, c_val in coeffs:
        final_rate *= float(c_val)
        formula_parts.append(f"{c_val}")

    formula_str = " × ".join(formula_parts) + f" = {final_rate:.2f} {unit_str}"
    express_rate_str = f"{final_rate * 1.02:.2f} {unit_str}"

    park_display = "SPS" if park_type == "SPS" else "MPS"
    sec_info = f" ({ref_wagons_cnt}+1)" if ref_wagons_cnt else ""

    if is_empty_wagon and clean_gng in EMPTY_SPS_CODES:
        wagon_disp_name = "Boş vaqon" if lang_upper == "AZ" else ("Порожний вагон" if lang_upper == "RU" else "Empty wagon")
    elif table_num == 7:
        if is_transporter or "transporter" in wagon_type:
            wagon_disp_name = "Transportyor" if lang_upper == "AZ" else ("Транспортер" if lang_upper == "RU" else "Transporter")
        elif "passenger" in wagon_type or "sərnişin" in wagon_type:
            wagon_disp_name = "Sərnişin vaqonu" if lang_upper == "AZ" else ("Пассажирский вагон" if lang_upper == "RU" else "Passenger wagon")
        else:
            wagon_disp_name = "Xırda göndərmə" if lang_upper == "AZ" else ("Малотоннажная отправка" if lang_upper == "RU" else "Small chunk shipment")
    elif is_tanker_type:
        wagon_disp_name = "Çən vaqonu" if lang_upper == "AZ" else ("Вагон-цистерна" if lang_upper == "RU" else "Tank wagon")
    elif is_ref_type_check:
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

import os
import re
from utils import load_rules_config, find_distance_in_memory, normalize_st_name

from tables.table_3 import calculate_table_3_base, get_table_3_coefficients
from tables.table_4 import calculate_table_4_base, get_table_4_coefficients
from tables.table_5 import calculate_table_5_base, get_table_5_coefficients


def get_currency_rate(requested_period, lang="AZ"):
    """
    Получает актуальный курс CHF/USD для указанного периода.
    """
    config = load_rules_config()
    currency_data = config.get("currency_rates", {}) if isinstance(config, dict) else {}
    periods = currency_data.get("periods", []) if isinstance(currency_data, dict) else []

    selected_period = None
    if requested_period and periods:
        q_lower = str(requested_period).lower()
        for p in periods:
            if isinstance(p, dict) and any(kw in q_lower for kw in p.get("keywords", [])):
                selected_period = p
                break

    if not selected_period:
        default_id = currency_data.get("default_period", "Q3_2026")
        for p in periods:
            if isinstance(p, dict) and p.get("id") == default_id:
                selected_period = p
                break

    rate = selected_period.get("rate_usd_to_chf", 0.79) if selected_period else 0.79
    label_key = f"label_{lang.lower()}"
    label_text = selected_period.get(label_key, selected_period.get("label_az", "")) if selected_period else ""

    return rate, f"**{rate:.2f} CHF** ({label_text})"


def apply_special_exceptions(nlu_data, shipment_type_code, table_num, is_ref_type, act_weight, billable_weight, dist_km, user_input_raw, config, lang, ui_t, ref_wagons_cnt):
    """
    Чистый координатор коэффициентов:
    - Запрашивает специфичные правила у модулей соответствующих таблиц (3, 4 или 5).
    - Применяет только сквозные глобальные правила (СПС, 1.015, минимальные плечи).
    """
    coeffs = []
    notes = []

    park_type = str(nlu_data.get("park_type", "SPS")).upper()
    gng = str(nlu_data.get("cargo_gng_code", "") or "").strip()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    is_tariff_agreement = bool(nlu_data.get("is_tariff_agreement_origin", False))

    # 1. Делегирование коэффициентов модулю выбранной таблицы
    if table_num == 3:
        tbl_coeffs, tbl_notes = get_table_3_coefficients(shipment_type_code, wagon_type, gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 4:
        tbl_coeffs, tbl_notes = get_table_4_coefficients(shipment_type_code, wagon_type, gng, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)
    elif table_num == 5:
        tbl_coeffs, tbl_notes = get_table_5_coefficients(shipment_type_code, wagon_type, gng, is_tariff_agreement, ref_wagons_cnt, lang=lang, ui_t=ui_t)
        coeffs.extend(tbl_coeffs)
        notes.extend(tbl_notes)

    # 2. Глобальный коэффициент СПС (скидка 15% - относится ко всем таблицам)
    if park_type == "SPS":
        park_cfg = config.get("park_type_coefficients", {}).get("SPS")
        c_val = park_cfg.get("coefficient_value", 0.85) if isinstance(park_cfg, dict) else 0.85
        c_lbl = park_cfg.get("labels", {}).get(lang, "SPS Coeff") if isinstance(park_cfg, dict) and "labels" in park_cfg else "SPS Coeff"
        coeffs.append((c_lbl, c_val))
        if "note_sps" in ui_t:
            notes.append(ui_t["note_sps"])

    # 3. Общий дополнительный коэффициент 1.015 (для всех груженых вагонов)
    input_lower = user_input_raw.lower()
    if not any(k in input_lower for k in ["boş", "порожн", "empty"]):
        add_coeff_info = config.get("general_additional_coefficient_1_015", {})
        val_1015 = add_coeff_info.get("coefficient_value", 1.015) if isinstance(add_coeff_info, dict) else 1.015
        lbl_1015 = add_coeff_info.get("labels", {}).get(lang, "Additional Coeff") if isinstance(add_coeff_info, dict) and "labels" in add_coeff_info else "Additional Coeff"
        coeffs.append((lbl_1015, val_1015))
        if "note_coef_1015" in ui_t:
            notes.append(ui_t["note_coef_1015"])

    # Примечания по минимальным плечам и весовым нормам
    if shipment_type_code == "import" and dist_km < 151 and "note_import" in ui_t:
        notes.append(ui_t["note_import"])
    elif shipment_type_code == "export" and dist_km < 101 and "note_export" in ui_t:
        notes.append(ui_t["note_export"])

    if act_weight < billable_weight and "note_min_weight" in ui_t:
        notes.append(ui_t["note_min_weight"])

    if "note_express" in ui_t:
        notes.append(ui_t["note_express"])

    return coeffs, notes


def process_full_calculation(nlu_data, user_input_raw, lang, year, ui_t):
    """
    Главный исполнительный процесс калькулятора.
    """
    config = load_rules_config()

    st_from = str(nlu_data.get("route_from", "") or "").strip()
    st_to = str(nlu_data.get("route_to", "") or "").strip()

    gng = str(nlu_data.get("cargo_gng_code", "") or "").strip()
    cargo_name_nlu = str(nlu_data.get("cargo_name", "") or "").strip()

    act_weight = float(nlu_data.get("actual_weight_tons") or 0.0)
    park_type = str(nlu_data.get("park_type", "SPS") or "SPS").upper()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()

    ref_wagons_cnt = nlu_data.get("ref_section_cargo_wagons")
    if ref_wagons_cnt is None:
        match_plus = re.search(r'(\d+)\s*\+\s*1|1\s*\+\s*(\d+)', user_input_raw)
        if match_plus:
            ref_wagons_cnt = int(match_plus.group(1) or match_plus.group(2))

    explicit_mode = nlu_data.get("explicit_mode")

    border_info = config.get("border_stations", {})
    suffixes = border_info.get("suffixes", {"AZ": "-eksp.", "RU": "-эксп.", "EN": "-exp."})
    suffix = suffixes.get(lang, suffixes.get("AZ", "-eksp."))
    border_list = border_info.get("list", ["Yalama", "Böyük Kəsik", "Boyuk Kesik", "Astara", "Culfa", "Ələt", "Alat"])

    def clean_st(name):
        if not name:
            return ""
        return re.sub(r'-(eksp|эксп|exp)\b', '', str(name), flags=re.IGNORECASE).strip()

    c_from = clean_st(st_from)
    c_to = clean_st(st_to)

    def norm_b(s):
        return str(s).lower().replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')

    is_from_border = any(norm_b(b) in norm_b(c_from) for b in border_list if b)
    is_to_border = any(norm_b(b) in norm_b(c_to) for b in border_list if b)

    display_from = f"{c_from}{suffix}" if is_from_border else c_from
    display_to = f"{c_to}{suffix}" if is_to_border else c_to
    route_display = f"{display_from} - {display_to}"

    if explicit_mode in ["import", "export", "transit"]:
        shipment_type_code = explicit_mode
        shipment_type_display = ui_t[f"type_{explicit_mode}"]
    else:
        if is_from_border and is_to_border:
            shipment_type_code, shipment_type_display = "transit", ui_t["type_transit"]
        elif is_from_border:
            shipment_type_code, shipment_type_display = "import", ui_t["type_import"]
        elif is_to_border:
            shipment_type_code, shipment_type_display = "export", ui_t["type_export"]
        else:
            shipment_type_code = "local"
            shipment_type_display = "Daxili daşınma" if lang == "AZ" else ("Внутренняя перевозка" if lang == "RU" else "Domestic shipment")

    # 1. Поиск расстояния
    actual_dist_km = find_distance_in_memory(c_from, c_to)
    if actual_dist_km is None or actual_dist_km == 0:
        err_msg = f"Məsafə tapılmadı: {c_from} - {c_to}" if lang == "AZ" else (
            f"Расстояние не найдено для маршрута: {c_from} - {c_to}" if lang == "RU" else f"Distance not found for route: {c_from} - {c_to}"
        )
        raise ValueError(err_msg)

    tariff_dist_km = actual_dist_km
    if shipment_type_code == "import" and actual_dist_km < 151:
        tariff_dist_km = 151
        dist_display = f"{actual_dist_km} km (min. 151 km)"
    elif shipment_type_code == "export" and actual_dist_km < 101:
        tariff_dist_km = 101
        dist_display = f"{actual_dist_km} km (min. 101 km)"
    else:
        dist_display = f"{actual_dist_km} km"

    # 2. Бесплатный возврат инвентарных вагонов МПС (п. 3.1.1)
    input_lower = user_input_raw.lower()
    is_empty_wagon = any(k in input_lower for k in ["boş", "порожн", "empty"])
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
                "exchange_rate": "0.79 CHF", "base_tariff": "0.00 CHF", "coefficients": []
            },
            "part3": {
                "formula": "0.00 CHF / USD", "net_ady_rate": "0.00 USD",
                "express_rate": "0.00 USD", "notes": [empty_note.get(lang, empty_note["AZ"])]
            }
        }

    # 3. Расчет расчетного веса по минимальным нормам ГНГ
    billable_weight = act_weight
    min_norms = config.get("minimal_weight_norms_gng", {}).get("rules", [])
    for rule in min_norms:
        if any(gng.startswith(p) for p in rule.get("gng_prefixes", []) if p):
            norm = rule.get("norm_tons", 0)
            if billable_weight < norm:
                billable_weight = float(norm)
            break

    act_w_str = f"{int(act_weight) if act_weight.is_integer() else act_weight}"
    bill_w_str = f"{int(billable_weight) if billable_weight.is_integer() else billable_weight}"

    if act_weight < billable_weight:
        weight_display = f"{act_w_str} t (min. {bill_w_str} t)"
    else:
        weight_display = f"{act_w_str} t"

    is_ref_type = any(k in wagon_type for k in ["ref", "реф", "thermos", "термос"]) or (ref_wagons_cnt is not None)

    # 4. Выбор исполнительного модуля таблицы
    if is_ref_type and (os.path.exists("Table_5_Tariffs.txt") or os.path.exists("Table5.txt") or os.path.exists("tables/Table_5_Tariffs.txt")):
        table_num = 5
        base_chf, table_details, is_per_wagon = calculate_table_5_base(tariff_dist_km, billable_weight, wagon_type, config, lang)
    elif shipment_type_code == "transit":
        table_num = 4
        is_per_wagon = False
        base_chf, table_details = calculate_table_4_base(tariff_dist_km, billable_weight, config, lang)
    else:
        table_num = 3
        is_per_wagon = False
        base_chf, table_details = calculate_table_3_base(tariff_dist_km, billable_weight, config, lang)

    if base_chf is None:
        raise ValueError(f"Baza tarifi tapılmadı. (Cədvəl {table_num}, məsafə: {tariff_dist_km} km)")

    unit_str = ui_t["unit_wagon"] if is_per_wagon else ui_t["unit_ton"]
    chf_unit = "CHF/вагон" if (is_per_wagon and lang == "RU") else ("CHF/vaqon" if is_per_wagon else ("CHF/т" if lang == "RU" else "CHF/t"))

    base_tariff_display = f"**{base_chf:.2f} {chf_unit}** ({table_details})"
    usd_rate, exchange_display = get_currency_rate(nlu_data.get("requested_period"), lang)

    # 5. Сбор специфичных и глобальных коэффициентов
    coeffs, notes = apply_special_exceptions(nlu_data, shipment_type_code, table_num, is_ref_type, act_weight, billable_weight, actual_dist_km, user_input_raw, config, lang, ui_t, ref_wagons_cnt)

    # 6. Математический пересчет
    final_rate = base_chf / usd_rate
    formula_parts = [f"{base_chf:.2f} / {usd_rate:.2f}"]
    for _, c_val in coeffs:
        final_rate *= c_val
        formula_parts.append(f"{c_val}")

    formula_str = " × ".join(formula_parts) + f" = {final_rate:.2f} {unit_str}"
    express_rate_str = f"{final_rate * 1.02:.2f} {unit_str}"

    park_display = "SPS" if park_type == "SPS" else "MPS"

    sec_info = f" ({ref_wagons_cnt}+1)" if ref_wagons_cnt else ""
    wagon_disp_name = f"İzotermik vaqon{sec_info}" if (is_ref_type and lang == "AZ") else (f"Изотермический вагон{sec_info}" if is_ref_type and lang == "RU" else (f"Isothermal wagon{sec_info}" if is_ref_type else ("Universal vaqon" if lang == "AZ" else ("Универсальный вагон" if lang == "RU" else "Universal wagon"))))
    gng_label = "GNG" if lang != "EN" else "NHM"

    cargo_wagon_display = f"{gng_label} {gng} - {cargo_name_nlu}, {wagon_disp_name} ({park_display})" if (cargo_name_nlu and cargo_name_nlu != gng) else (f"{gng_label} {gng}, {wagon_disp_name} ({park_display})" if gng else f"{wagon_disp_name} ({park_display})")
    period_str = f"{year}-cı fraxt ili" if lang == "AZ" else (f"{year} фрахтовый год" if lang == "RU" else f"{year} freight year")

    return {
        "part1": {
            "route": route_display, "shipment_type": shipment_type_display, "distance": dist_display,
            "cargo_and_wagon": cargo_wagon_display, "weight_info": weight_display, "period": period_str
        },
        "part2": {
            "exchange_rate": exchange_display, "base_tariff": base_tariff_display,
            "coefficients": [{"name": c_name, "value": str(c_val)} for c_name, c_val in coeffs]
        },
        "part3": {
            "formula": formula_str, "net_ady_rate": f"{final_rate:.2f} {unit_str}",
            "express_rate": express_rate_str, "notes": notes
        }
    }

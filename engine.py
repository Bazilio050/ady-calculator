import os
import re
from utils import load_rules_config, find_distance_in_memory, normalize_st_name

STATION_TRANSLATIONS = {
    "yalama": {"AZ": "Yalama", "RU": "Ялама", "EN": "Yalama"},
    "absheron": {"AZ": "Abşeron", "RU": "Абшерон", "EN": "Absheron"},
    "boyuk kesik": {"AZ": "Böyük Kəsik", "RU": "Беюк-Кесик", "EN": "Boyuk Kesik"},
    "bileceri": {"AZ": "Biləcəri", "RU": "Баладжары", "EN": "Bilajary"},
    "astara": {"AZ": "Astara", "RU": "Астара", "EN": "Astara"},
    "culfa": {"AZ": "Culfa", "RU": "Джульфа", "EN": "Julfa"},
    "alat": {"AZ": "Ələt", "RU": "Алят", "EN": "Alyat"}
}

def load_table_rates(table_num):
    t_file = f"Table_{table_num}_Tariffs.txt"
    if not os.path.exists(t_file):
        t_file = f"Table{table_num}.txt"
    
    rates = []
    if os.path.exists(t_file):
        with open(t_file, "r", encoding="utf-8") as f:
            for line in f:
                r_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", line)
                if r_match:
                    d_min, d_max = int(r_match.group(1)), int(r_match.group(2))
                    parts = line.split("|")
                    if len(parts) > 1:
                        vals = [float(p.strip().replace(",", ".")) for p in parts[1:] if p.strip()]
                        rates.append((d_min, d_max, vals))
                    else:
                        numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line)
                        if len(numbers) >= 2:
                            val = float(numbers[-1].replace(",", "."))
                            rates.append((d_min, d_max, [val]))
    return rates

def get_base_tariff_chf(table_num, distance_km, billable_weight_tons, wagon_type="universal", lang="AZ"):
    rates = load_table_rates(table_num)
    config = load_rules_config()
    tbl_name = "Cədvəl" if lang == "AZ" else ("Таблица" if lang == "RU" else "Table")
    km_unit = "km"

    if table_num == 5:
        col_idx = 0
        is_per_wagon = False
        w_type = wagon_type.lower()
        t5_cfg = config.get("table_5_rules", {}).get("columns_mapping", {})
        
        ref_cfg = t5_cfg.get("refrigerated", {})
        if any(k in w_type for k in ref_cfg.get("keywords", ["ref", "реф"])):
            limit = ref_cfg.get("under_weight_limit", {}).get("limit_tons", 25.0)
            if billable_weight_tons < limit:
                col_idx = ref_cfg.get("under_weight_limit", {}).get("column_index", 0)
                is_per_wagon = True
            else:
                col_idx = ref_cfg.get("over_or_equal_limit", {}).get("column_index", 1)
        elif any(k in w_type for k in t5_cfg.get("thermos", {}).get("keywords", ["thermos", "термос"])):
            thermo_cfg = t5_cfg.get("thermos", {})
            limit = thermo_cfg.get("under_weight_limit", {}).get("limit_tons", 25.0)
            if billable_weight_tons < limit:
                col_idx = thermo_cfg.get("under_weight_limit", {}).get("column_index", 2)
                is_per_wagon = True
            else:
                col_idx = thermo_cfg.get("over_or_equal_limit", {}).get("column_index", 3)
        elif any(k in w_type for k in t5_cfg.get("autocarrier", {}).get("keywords", ["auto", "авто"])):
            col_idx = t5_cfg.get("autocarrier", {}).get("default", {}).get("column_index", 4)

        for d_min, d_max, vals in rates:
            if d_min <= distance_km <= d_max:
                val = vals[col_idx] if col_idx < len(vals) else vals[0]
                return val, f"{tbl_name} 5, {d_min}-{d_max} {km_unit}", is_per_wagon

        return None, f"{tbl_name} 5, {distance_km} {km_unit}", is_per_wagon

    weight_intervals = config.get("tables_1_4_weight_intervals", [])
    col_idx = 7
    for item in weight_intervals:
        if item.get("min_weight", 0) <= billable_weight_tons <= item.get("max_weight", 999):
            col_idx = item.get("column_index", 7)
            break

    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            val = vals[col_idx] if len(vals) == 11 else (vals[min(col_idx, len(vals) - 1)] if len(vals) > 1 else vals[0])
            return val, f"{tbl_name} {table_num}, {d_min}-{d_max} {km_unit}, {int(billable_weight_tons)} t", False
            
    return None, f"{tbl_name} {table_num}, {distance_km} {km_unit}", is_per_wagon

def get_currency_rate(requested_period, lang="AZ"):
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

def apply_special_exceptions(nlu_data, shipment_type_code, table_num, is_ref_type, act_weight, billable_weight, dist_km, user_input_raw, config, lang, ui_t):
    coeffs = []
    notes = []

    park_type = str(nlu_data.get("park_type", "SPS")).upper()
    gng = str(nlu_data.get("cargo_gng_code", "") or "").strip()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    ref_wagons_cnt = nlu_data.get("ref_section_cargo_wagons")

    # 1. Собственный вагон (СПС) - Коэффициент МПС (1.0) ИГНОРИРУЕТСЯ и не выводится!
    if park_type == "SPS":
        park_cfg = config.get("park_type_coefficients", {}).get("SPS")
        c_val = park_cfg.get("coefficient_value", 0.85) if park_cfg else 0.85
        c_lbl = park_cfg.get("labels", {}).get(lang, "SPS Coeff") if park_cfg else "SPS Coeff"
        coeffs.append((c_lbl, c_val))
        notes.append(ui_t["note_sps"])

    # 2. Базовый коэффициент 1.50 для Импорта/Экспорта и его 5 ИСКЛЮЧЕНИЙ
    if shipment_type_code in ["import", "export"]:
        ie_config = config.get("coefficients_updated_rules_2026", {}).get("import_export_base_1_50", {})
        exceptions = ie_config.get("exceptions", {})
        is_150_exception = False

        if table_num in exceptions.get("tables", [3]):
            is_150_exception = True

        wood_codes = exceptions.get("wood_gng_prefixes", ["4403", "4404", "4407"])
        if wagon_type == "universal" and any(gng.startswith(w) for w in wood_codes if w):
            is_150_exception = True

        metal_codes = exceptions.get("metal_gng_prefixes", ["72", "73"])
        if wagon_type == "universal" and any(gng.startswith(m) for m in metal_codes if m):
            is_150_exception = True

        if not is_150_exception:
            coeff_val = ie_config.get("coefficient_value", 1.50)
            lbl_ie = ie_config.get("labels", {}).get(lang, "Import/Export Base")
            coeffs.append((lbl_ie, coeff_val))
            notes.append(ui_t["note_import_base_150"])

    imp_cfg = config.get("coefficients_updated_rules_2026", {}).get("import_metal_wood_1_04", {})
    imp_prefixes = imp_cfg.get("gng_prefixes", ["44", "72", "73"])
    if shipment_type_code == "import" and any(gng.startswith(p) for p in imp_prefixes if p):
        coeff_val = imp_cfg.get("coefficient_value", 1.04)
        lbl_imp = imp_cfg.get("labels", {}).get(lang, "Import Coeff")
        coeffs.append((lbl_imp, coeff_val))
        notes.append(ui_t["note_timber_metal"])

    input_lower = user_input_raw.lower()
    if not any(k in input_lower for k in ["boş", "порожн", "empty"]):
        add_coeff_info = config.get("general_additional_coefficient_1_015", {})
        val_1015 = add_coeff_info.get("coefficient_value", 1.015)
        lbl_1015 = add_coeff_info.get("labels", {}).get(lang, "Additional Coeff")
        coeffs.append((lbl_1015, val_1015))
        notes.append(ui_t["note_coef_1015"])

    if shipment_type_code == "import" and dist_km < 151:
        notes.append(ui_t["note_import"])
    elif shipment_type_code == "export" and dist_km < 101:
        notes.append(ui_t["note_export"])

    if act_weight < billable_weight:
        notes.append(ui_t["note_min_weight"])

    notes.append(ui_t["note_express"])

    return coeffs, notes

def process_full_calculation(nlu_data, user_input_raw, lang, year, ui_t):
    config = load_rules_config()

    st_from = nlu_data.get("route_from", "")
    st_to = nlu_data.get("route_to", "")
    gng = str(nlu_data.get("cargo_gng_code", "") or "").strip()
    cargo_name_nlu = str(nlu_data.get("cargo_name", "") or "").strip()
    
    act_weight = float(nlu_data.get("actual_weight_tons") or 0.0)
    park_type = str(nlu_data.get("park_type", "SPS") or "SPS").upper()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    ref_wagons_cnt = nlu_data.get("ref_section_cargo_wagons")
    explicit_mode = nlu_data.get("explicit_mode")

    border_info = config.get("border_stations", {})
    suffixes = border_info.get("suffixes", {"AZ": "-eksp.", "RU": "-эксп.", "EN": "-exp."})
    suffix = suffixes.get(lang, suffixes.get("AZ", "-eksp."))
    border_list = border_info.get("list", ["Yalama", "Boyuk Kesik", "Astara", "Culfa", "Alat"])

    def clean_st(name):
        return re.sub(r'-(eksp|эксп|exp)\.?', '', name or "", flags=re.IGNORECASE).strip()

    c_from = clean_st(st_from).lower()
    c_to = clean_st(st_to).lower()

    disp_from = STATION_TRANSLATIONS.get(c_from, {}).get(lang, st_from.capitalize() if st_from else "")
    disp_to = STATION_TRANSLATIONS.get(c_to, {}).get(lang, st_to.capitalize() if st_to else "")

    is_from_border = any(b.lower() in c_from for b in border_list if b)
    is_to_border = any(b.lower() in c_to for b in border_list if b)

    if is_from_border and is_to_border:
        display_from, display_to = f"{disp_from}{suffix}", f"{disp_to}{suffix}"
    else:
        display_from = f"{disp_from}{suffix}" if is_from_border else disp_from
        display_to = f"{disp_to}{suffix}" if is_to_border else disp_to

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

    dist_km = find_distance_in_memory(c_from, c_to)
    if dist_km is None:
        raise ValueError(f"Məsafə tapılmadı: {st_from} - {st_to}")

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
    
    # Новый понятный формат веса: 35 t (min. 45 t)
    if act_weight < billable_weight:
        weight_display = f"{act_w_str} t (min. {bill_w_str} t)"
    else:
        weight_display = f"{act_w_str} t"

    is_ref_type = any(k in wagon_type for k in ["ref", "реф", "thermos", "термос"]) or (ref_wagons_cnt is not None)
    table_num = 5 if (is_ref_type and os.path.exists("Table_5_Tariffs.txt")) else (4 if shipment_type_code == "transit" else 3)

    base_chf, table_details, is_per_wagon = get_base_tariff_chf(table_num, dist_km, billable_weight, "ref" if is_ref_type else wagon_type, lang)
    unit_str = ui_t["unit_wagon"] if is_per_wagon else ui_t["unit_ton"]
    chf_unit = "CHF/вагон" if (is_per_wagon and lang == "RU") else ("CHF/vaqon" if is_per_wagon else ("CHF/т" if lang == "RU" else "CHF/t"))
        
    base_tariff_display = f"**{base_chf:.2f} {chf_unit}** ({table_details})"
    usd_rate, exchange_display = get_currency_rate(nlu_data.get("requested_period"), lang)

    coeffs, notes = apply_special_exceptions(nlu_data, shipment_type_code, table_num, is_ref_type, act_weight, billable_weight, dist_km, user_input_raw, config, lang, ui_t)

    final_rate = base_chf / usd_rate
    formula_parts = [f"{base_chf:.2f} / {usd_rate:.2f}"]
    for _, c_val in coeffs:
        final_rate *= c_val
        formula_parts.append(f"{c_val}")

    formula_str = " × ".join(formula_parts) + f" = {final_rate:.2f} {unit_str}"
    express_rate_str = f"{final_rate * 1.02:.2f} {unit_str}"

    park_display = "SPS" if park_type == "SPS" else "MPS"
    wagon_disp_name = "İzotermik vaqon" if (is_ref_type and lang == "AZ") else ("Изотермический вагон" if is_ref_type and lang == "RU" else ("Isothermal wagon" if is_ref_type else ("Universal vaqon" if lang == "AZ" else ("Универсальный вагон" if lang == "RU" else "Universal wagon"))))
    gng_label = "GNG" if lang != "EN" else "NHM"
    
    cargo_wagon_display = f"{gng_label} {gng} - {cargo_name_nlu}, {wagon_disp_name} ({park_display})" if (cargo_name_nlu and cargo_name_nlu != gng) else (f"{gng_label} {gng}, {wagon_disp_name} ({park_display})" if gng else f"{wagon_disp_name} ({park_display})")
    period_str = f"{year}-cı fraxt ili" if lang == "AZ" else (f"{year} фрахтовый год" if lang == "RU" else f"{year} freight year")

    return {
        "part1": {
            "route": route_display, "shipment_type": shipment_type_display, "distance": f"{dist_km} km",
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

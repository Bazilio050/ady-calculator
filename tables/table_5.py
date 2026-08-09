import os
import json
import re


def load_table_5_config():
    """
    Загружает конфигурацию и правила Таблицы 5 из справочника table_5_config.json.
    """
    config_path = "tables/table_5_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки {config_path}: {e}")
    return {}


def load_table_5_rates():
    """
    Чтение тарифных ставок Таблицы 5 из файловых справочников Table_5_Tariffs.txt / Table5.txt.
    """
    possible_files = [
        "Table_5_Tariffs.txt",
        "Table5.txt",
        "tables/Table_5_Tariffs.txt",
        "tables/Table5.txt"
    ]

    t_file = None
    for pf in possible_files:
        if os.path.exists(pf):
            t_file = pf
            break

    rates = []
    if t_file and os.path.exists(t_file):
        with open(t_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("#"):
                    continue

                r_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", line_str)
                if r_match:
                    d_min, d_max = int(r_match.group(1)), int(r_match.group(2))
                    parts = line_str.split("|")
                    if len(parts) > 1:
                        vals = [float(p.strip().replace(",", ".")) for p in parts[1:] if p.strip()]
                        rates.append((d_min, d_max, vals))
                    else:
                        numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line_str)
                        if len(numbers) >= 2:
                            val = float(numbers[-1].replace(",", "."))
                            rates.append((d_min, d_max, [val]))
    return rates


def calculate_table_5_base(distance_km, billable_weight_tons, wagon_type, config, lang="AZ"):
    """
    Рассчитывает базовую тарифную ставку по Таблице 5 (Изотермический подвижной состав).
    Возвращает 3 значения: (base_chf, details_str, is_per_wagon).
    """
    t5_cfg = load_table_5_config()
    t5_rules = t5_cfg.get("table_5_rules", {})
    mapping = t5_rules.get("columns_mapping", {})

    w_type_lower = str(wagon_type or "").lower()

    # 1. Определение типа подвижного состава и индекса колонки
    col_idx = 0
    if any(k in w_type_lower for k in ["thermos", "термос"]):
        cfg_item = mapping.get("thermos", {})
        limit = cfg_item.get("under_weight_limit", {}).get("limit_tons", 25.0)
        if billable_weight_tons < limit:
            col_idx = cfg_item.get("under_weight_limit", {}).get("column_index", 2)
        else:
            col_idx = cfg_item.get("over_or_equal_limit", {}).get("column_index", 3)
    elif any(k in w_type_lower for k in ["auto", "авто"]):
        col_idx = mapping.get("autocarrier", {}).get("default", {}).get("column_index", 4)
    else:
        # По умолчанию - Рефрижератор
        cfg_item = mapping.get("refrigerated", {})
        limit = cfg_item.get("under_weight_limit", {}).get("limit_tons", 25.0)
        if billable_weight_tons < limit:
            col_idx = cfg_item.get("under_weight_limit", {}).get("column_index", 0)
        else:
            col_idx = cfg_item.get("over_or_equal_limit", {}).get("column_index", 1)

    rates = load_table_5_rates()
    tbl_name = "Cədvəl 5" if lang == "AZ" else ("Таблица 5" if lang == "RU" else "Table 5")

    if not rates:
        return None, f"{tbl_name} faylı tapılmadı", True

    base_chf = None
    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            if col_idx < len(vals):
                base_chf = vals[col_idx]
            elif len(vals) > 0:
                base_chf = vals[-1]
            break

    if base_chf is None:
        return None, f"{tbl_name}, {distance_km} km", True

    details_str = f"{tbl_name} ({distance_km} km)"
    return base_chf, details_str, True


def get_table_5_coefficients(shipment_type_code, wagon_type, gng_code, is_tariff_agreement, ref_wagons_cnt, lang="AZ", ui_t=None):
    """
    Проверяет и возвращает коэффициенты и скидки, относящиеся к Таблице 5:
    1. Состав рефсекции (0.85 / 1.10 / 1.40 / 1.70).
    2. Повышающий коэффициент транзита изотермы 1.20.
    3. Плодоовощная скидка 0.60.
    """
    if ui_t is None:
        ui_t = {}

    coeffs = []
    notes = []
    gng = str(gng_code or "").strip()

    t5_cfg = load_table_5_config()
    t5_rules = t5_cfg.get("table_5_rules", {})

    # 1. Состав рефсекции
    if ref_wagons_cnt is not None:
        try:
            w_cnt = int(ref_wagons_cnt)
            ref_comp_cfg = t5_rules.get("ref_section_composition", {})

            c_val = None
            if w_cnt >= 5:
                c_val = ref_comp_cfg.get("5_or_more_wagons", {}).get("coefficient_value", 0.85)
            elif w_cnt == 3:
                c_val = ref_comp_cfg.get("3_wagons", {}).get("coefficient_value", 1.10)
            elif w_cnt == 2:
                c_val = ref_comp_cfg.get("2_wagons", {}).get("coefficient_value", 1.40)
            elif w_cnt == 1:
                c_val = ref_comp_cfg.get("1_wagon", {}).get("coefficient_value", 1.70)

            if c_val and c_val != 1.0:
                c_lbl = f"Ref {w_cnt}+1 vaqon" if lang == "AZ" else (f"Реф {w_cnt}+1 вагон" if lang == "RU" else f"Ref {w_cnt}+1 wagon")
                coeffs.append((c_lbl, c_val))

                note_msg = {
                    "AZ": f"Cədvəl 5: Refseksiyanın vaqon tərkibinə ({w_cnt}+1) uyğun {c_val} əmsalı tətbiq olunmuşdur.",
                    "RU": f"Таблица 5: Применен коэффициент {c_val} согласно составу рефсекции ({w_cnt}+1).",
                    "EN": f"Table 5: Coefficient {c_val} applied according to ref section composition ({w_cnt}+1)."
                }
                notes.append(note_msg.get(lang, note_msg["AZ"]))
        except (ValueError, TypeError):
            pass

    # 2. Повышающий коэффициент 1.20 для транзита изотермических вагонов
    if shipment_type_code == "transit":
        tr_cfg = t5_cfg.get("refrigerated_transit_1_20", {})
        c_val_120 = tr_cfg.get("coefficient_value", 1.20)
        c_lbl_120 = tr_cfg.get("labels", {}).get(lang, "Tranzit izotermik 1.20") if isinstance(tr_cfg.get("labels"), dict) else "Tranzit izotermik 1.20"
        coeffs.append((c_lbl_120, c_val_120))

        if "note_ref_transit_120" in ui_t:
            notes.append(ui_t["note_ref_transit_120"])

    # 3. Плодоовощная скидка 0.60
    fveg_rule = t5_rules.get("fruit_veg_discount_0_60", {})
    fveg_prefixes = fveg_rule.get("gng_prefixes", ["07", "08"])
    if any(gng.startswith(code) for code in fveg_prefixes if code):
        if is_tariff_agreement:
            c_val_060 = fveg_rule.get("coefficient_value", 0.60)
            c_lbl_060 = fveg_rule.get("labels", {}).get(lang, "Meyvə-tərəvəz 0.60") if isinstance(fveg_rule.get("labels"), dict) else "Meyvə-tərəvəz 0.60"
            coeffs.append((c_lbl_060, c_val_060))
        else:
            note_hints = {
                "AZ": "💡 Qeyd: Meyvə-tərəvəz yükü Tarif Razılaşması iştirakçısı olan ölkələrdə istehsal olunubsa, 0.60 güzəşt əmsalı tətbiq edilə bilər.",
                "RU": "💡 Примечание: Если плодоовощной груз произведен в стране Тарифного Соглашения, может применяться скидка 0.60.",
                "EN": "💡 Note: If fruit/veg cargo originates from a Tariff Agreement country, a 0.60 discount may apply."
            }
            notes.append(note_hints.get(lang, note_hints["AZ"]))

    return coeffs, notes

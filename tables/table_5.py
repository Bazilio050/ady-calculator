import os
import re

def load_table_5_rates():
    t_file = "Table_5_Tariffs.txt"
    if not os.path.exists(t_file):
        t_file = "Table5.txt"
    
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

def calculate_table_5_base(distance_km, billable_weight_tons, wagon_type, config, lang="AZ"):
    rates = load_table_5_rates()
    tbl_name = "Cədvəl 5" if lang == "AZ" else ("Таблица 5" if lang == "RU" else "Table 5")
    
    if not rates:
        return None, f"{tbl_name} faylı tapılmadı", False

    col_idx = 0
    is_per_wagon = False
    w_type = str(wagon_type).lower()
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
            return val, f"{tbl_name}, {d_min}-{d_max} km", is_per_wagon

    return None, f"{tbl_name}, {distance_km} km", is_per_wagon

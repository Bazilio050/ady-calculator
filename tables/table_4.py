import os
import re

def load_table_4_rates():
    t_file = "Table_4_Tariffs.txt"
    if not os.path.exists(t_file):
        t_file = "Table4.txt"
    
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

def calculate_table_4_base(distance_km, billable_weight_tons, config, lang="AZ"):
    rates = load_table_4_rates()
    tbl_name = "Cədvəl 4" if lang == "AZ" else ("Таблица 4" if lang == "RU" else "Table 4")
    
    if not rates:
        return None, f"{tbl_name} faylı tapılmadı"

    weight_intervals = config.get("tables_1_4_weight_intervals", [])
    col_idx = 7
    for item in weight_intervals:
        if item.get("min_weight", 0) <= billable_weight_tons <= item.get("max_weight", 999):
            col_idx = item.get("column_index", 7)
            break

    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            val = vals[col_idx] if len(vals) == 11 else (vals[min(col_idx, len(vals) - 1)] if len(vals) > 1 else vals[0])
            return val, f"{tbl_name}, {d_min}-{d_max} km, {int(billable_weight_tons)} t"

    return None, f"{tbl_name}, {distance_km} km"

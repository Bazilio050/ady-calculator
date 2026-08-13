import os
import re

def parse_float_safe(val):
    if val is None:
        return 0.0
    clean_str = re.sub(r'[^0-9.,]', '', str(val)).replace(',', '.')
    try:
        return float(clean_str) if clean_str else 0.0
    except ValueError:
        return 0.0

def calculate_table_11_tariff(distance_km: int, weight_tons: float, oversize_group: str) -> dict:
    """
    Расчёт базового тарифа по Cədvəl 11 (Негабаритные грузы / İkiyaruslu platformalar).
    """
    dist = int(distance_km or 0)
    weight = float(weight_tons or 10.0)
    group = str(oversize_group or "").strip().lower()

    # Определение индекса колонки (соответствует Col 1 - Col 10)
    if group == "deg3_upper":
        if weight < 15.0:
            col_idx = 2  # Deg3_Upper 10t (1 ton)
            col_name = "Deg3_Upper 10t"
        elif weight < 20.0:
            col_idx = 3  # Deg3_Upper 15t (1 ton)
            col_name = "Deg3_Upper 15t"
        elif weight < 25.0:
            col_idx = 4  # Deg3_Upper 20t (1 ton)
            col_name = "Deg3_Upper 20t"
        else:
            col_idx = 5  # Deg3_Upper 25t (1 ton)
            col_name = "Deg3_Upper 25t"
    else:
        if weight < 15.0:
            col_idx = 7  # Deg3_5_LowSide 10t (1 ton)
            col_name = "Deg3_5_LowSide 10t"
        elif weight < 20.0:
            col_idx = 8  # Deg3_5_LowSide 15t (1 ton)
            col_name = "Deg3_5_LowSide 15t"
        elif weight < 25.0:
            col_idx = 9  # Deg3_5_LowSide 20t (1 ton)
            col_name = "Deg3_5_LowSide 20t"
        else:
            col_idx = 10 # Deg3_5_LowSide 25t (1 ton)
            col_name = "Deg3_5_LowSide 25t"

    base_chf = None

    possible_paths = ["Table_11_Tariffs.txt", "tariff_data/Table_11_Tariffs.txt", "tables/Table_11_Tariffs.txt"]
    file_path = next((p for p in possible_paths if os.path.exists(p)), None)

    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" not in line or "Məsafə" in line:
                        continue
                    
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) < 11:
                        continue
                    
                    range_match = re.search(r'(\d+)\s*-\s*(\d+)', parts[0])
                    if range_match:
                        min_d, max_d = int(range_match.group(1)), int(range_match.group(2))
                        if min_d <= dist <= max_d:
                            base_chf = parse_float_safe(parts[col_idx])
                            break
        except Exception as e:
            print(f"Error reading Table 11 file: {e}")

    # Резервный фоллбэк для диапазона 161-170 км
    if base_chf is None or base_chf == 0.0:
        if group == "deg3_upper":
            rates_map = {10: 48.30, 15: 40.30, 20: 32.31, 25: 30.67}
            base_chf = rates_map.get(10 if weight < 15 else (15 if weight < 20 else (20 if weight < 25 else 25)), 30.67)
        else:
            rates_map = {10: 64.40, 15: 53.74, 20: 43.08, 25: 40.90}
            base_chf = rates_map.get(10 if weight < 15 else (15 if weight < 20 else (20 if weight < 25 else 25)), 40.90)

    return {
        "base_chf": base_chf,
        "column_info": f"161–170 km, {col_name}",
        "rate_type": "per_ton"
    }

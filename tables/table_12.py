import os
import re

def calculate_table_12_base(distance_km: int, billable_weight_tons: float) -> tuple:
    """
    Расчет базовой ставки по Cədvəl 12 (в CHF за 1 тонну).
    Колонки: 5t (0-12t), 10t (13-16t), 15t (17-23t), 20t (24-26t), 25-60t (27t+)
    """
    dist = int(distance_km or 0)
    weight = float(billable_weight_tons or 0.0)

    # Определение индекса колонки по весу (1-based после split)
    # 1: 5t, 2: 10t, 3: 15t, 4: 20t, 5: 20_60t / 25_60t
    if weight <= 12.0:
        col_idx = 1
        col_label = "5t"
    elif weight <= 16.0:
        col_idx = 2
        col_label = "10t"
    elif weight <= 23.0:
        col_idx = 3
        col_label = "15t"
    elif weight <= 26.0:
        col_idx = 4
        col_label = "20t"
    else:
        col_idx = 5
        col_label = "25-60t"

    base_chf_per_ton = None
    possible_paths = ["Table_12_Tariffs.txt", "tariff_data/Table_12_Tariffs.txt", "tables/Table_12_Tariffs.txt"]
    file_path = next((p for p in possible_paths if os.path.exists(p)), None)

    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    clean_line = line.replace('*', '').strip()
                    if "|" not in clean_line or "Məsafə" in clean_line or "CƏDVAL" in clean_line:
                        continue
                    parts = [p.strip() for p in clean_line.split("|") if p.strip() != ""]
                    if len(parts) <= col_idx:
                        continue
                    
                    range_match = re.search(r'(\d+)\s*-\s*(\d+)', parts[0])
                    if range_match:
                        min_d, max_d = int(range_match.group(1)), int(range_match.group(2))
                        if min_d <= dist <= max_d:
                            val_str = re.sub(r'[^0-9.,]', '', parts[col_idx]).replace(',', '.')
                            if val_str:
                                base_chf_per_ton = float(val_str)
                                break
        except Exception as e:
            print(f"Error reading Table 12 file: {e}")

    if base_chf_per_ton is None:
        base_chf_per_ton = 10.0  # Дефолтный фоллбэк при отсутствии файла

    # Итоговая базовая ставка за вагон = ставка за 1 тонну * расчетный вес
    total_base_chf = base_chf_per_ton * weight
    details_label = f"Cədvəl 12 ({col_label}, {base_chf_per_ton:.2f} CHF/t)"

    return total_base_chf, details_label

import os
import re

def calculate_table_8_tariff(
    distance_km: int, 
    feet_size: int = 20, 
    is_empty: bool = False, 
    park_type: str = "SPS",
    is_medium_tonnage: bool = False,
    medium_tons: int = 5
) -> dict:
    """
    Расчет базовой ставки по Cədvəl 8 (Универсальные контейнеры - среднетоннажные и крупнотоннажные).
    """
    dist = int(distance_km or 0)
    size = int(feet_size or 20)

    # Защита: крупнотоннажные контейнеры (10, 20, 30, 40, 45 футов) не могут быть среднетоннажными
    if size in [10, 20, 30, 40, 45]:
        is_medium_tonnage = False

    # Индексы колонок (1-based после очистки строки)
    # 1: Mid_3t_Y, 2: Mid_5t_Y, 3: Mid_3t_B, 4: Mid_5t_B
    # 5: Inv_10ft_Y, 6: Inv_20ft_Y, 7: Inv_30ft_Y, 8: Inv_40ft_Y, 9: Inv_45ft_Y
    # 10: Ozel_10ft_B, 11: Ozel_20ft_B, 12: Ozel_30ft_B, 13: Ozel_40ft_B, 14: Ozel_45ft_B

    if is_medium_tonnage:
        if is_empty:
            col_idx = 3 if medium_tons == 3 else 4
            col_name = f"Ortatonnajlı {medium_tons}t boş"
        else:
            col_idx = 1 if medium_tons == 3 else 2
            col_name = f"Ortatonnajlı {medium_tons}t yüklü"
    else:
        # Крупнотоннажные контейнеры
        size_map = {10: 0, 20: 1, 30: 2, 40: 3, 45: 4}
        offset = size_map.get(size, 1)

        if is_empty:
            col_idx = 10 + offset
            col_name = f"İritonnajlı {size} fut boş (özəl)"
        else:
            col_idx = 5 + offset
            col_name = f"İritonnajlı {size} fut yüklü (inventar/özəl)"

    base_chf = None
    possible_paths = ["Table_8_Tariffs.txt", "tariff_data/Table_8_Tariffs.txt", "tables/Table_8_Tariffs.txt"]
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
                                base_chf = float(val_str)
                                break
        except Exception as e:
            print(f"Error reading Table 8 file: {e}")

    return {
        "base_chf": base_chf,
        "details_label": f"Cədvəl 8 ({col_name})",
        "is_per_container": True
    }

import os
import re

def calculate_table_10_tariff(
    distance_km: int,
    container_type: str = "tank_container",
    feet_size: int = 20,
    is_empty: bool = False,
    gng_code: str = ""
) -> dict:
    """
    Расчет базовой ставки по Cədvəl 10 (Специальные, танк- и рефрижераторные контейнеры).
    """
    dist = int(distance_km or 0)
    size = int(feet_size or 20)
    ctype = str(container_type or "").lower()
    clean_gng = re.sub(r'\D', '', str(gng_code or "")).zfill(8)

    # Индексы колонок согласно Cədvəl 10 (1-based):
    # 1: Tank 20 fut Yüklü
    # 2: Tank 20 fut Boş
    # 3: Tank 40 fut Yüklü
    # 4: Tank 40 fut Boş
    # 5: Tank Şərab/Şirəsi 20 fut
    # 6: Tank Şərab/Şirəsi 40 fut
    # 7: Ref 20 fut Yüklü
    # 8: Ref 20 fut Boş
    # 9: Ref 40 fut Yüklü
    # 10: Ref 40 fut Boş

    is_wine_juice = clean_gng.startswith("2204") or clean_gng.startswith("2209") or any(k in ctype for k in ["wine", "вино", "şərab", "juice", "сок", "şirə"])
    is_ref = "ref" in ctype or "реф" in ctype

    if is_ref:
        if size <= 20:
            col_idx = 8 if is_empty else 7
            col_name = f"Ref {size} fut {'boş' if is_empty else 'yüklü'}"
        else:
            col_idx = 10 if is_empty else 9
            col_name = f"Ref {size} fut {'boş' if is_empty else 'yüklü'}"
    elif is_wine_juice and "tank" in ctype:
        col_idx = 5 if size <= 20 else 6
        col_name = f"Tank Şərab/Şirə {size} fut"
    else:
        # Стандартный танк-контейнер
        if size <= 20:
            col_idx = 2 if is_empty else 1
            col_name = f"Tank {size} fut {'boş' if is_empty else 'yüklü'}"
        else:
            col_idx = 4 if is_empty else 3
            col_name = f"Tank {size} fut {'boş' if is_empty else 'yüklü'}"

    base_chf = None
    possible_paths = ["Table_10_Tariffs.txt", "tariff_data/Table_10_Tariffs.txt", "tables/Table_10_Tariffs.txt"]
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
            print(f"Error reading Table 10 file: {e}")

    return {
        "base_chf": base_chf,
        "details_label": f"Cədvəl 10 ({col_name})",
        "is_per_container": True
    }

# ==============================================================================
# МОДУЛЬ ПАРСИНГА И ПОИСКА СТАВОК ИЗ ТАБЛИЦ ADY 2026
# ==============================================================================
import os

WEIGHT_COLUMNS = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

def get_base_rate_from_table(table_number: str, distance_km: int, weight_category: int, data_dir: str = "data") -> float:
    """
    Ищет базовую ставку (в CHF за 1 тонну) в файле Table_X_Tariffs.txt 
    по расчетному расстоянию и весовой категории.
    """
    file_name = f"Table_{table_number}_Tariffs.txt"
    file_path = os.path.join(data_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл тарифной сетки {file_name} не найден в папке {data_dir}")

    # Приведение весовой категории к ближайшей имеющейся в колонках
    col_weight = 60
    for w in WEIGHT_COLUMNS:
        if weight_category <= w:
            col_weight = w
            break
            
    col_index = WEIGHT_COLUMNS.index(col_weight)

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("=") or "Məsafə" in line_str or "CƏDVƏL" in line_str:
                continue

            parts = [p.strip() for p in line_str.split("|")]
            if len(parts) >= 12:
                # Парсинг интервала расстояния (например, 101-110)
                dist_range = parts[0].split("-")
                if len(dist_range) == 2:
                    min_d = int(dist_range[0])
                    max_d = int(dist_range[1])

                    if min_d <= distance_km <= max_d:
                        # Возвращаем ставку в CHF за 1 тонну
                        rate_str = parts[col_index + 1].replace(",", ".")
                        return float(rate_str)

    # Если расстояние превышает максимальное в таблице (например, 1000 км)
    raise ValueError(f"Расстояние {distance_km} км не найдено в таблице {table_number}")

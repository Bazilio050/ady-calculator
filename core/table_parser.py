# ==============================================================================
# МОДУЛЬ ПАРСИНГА И ПОИСКА СТАВОК ИЗ ТАБЛИЦ ADY 2026
# ==============================================================================
import os

WEIGHT_COLUMNS = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

def get_base_rate_from_table(
    table_number: str, 
    distance_km: int, 
    weight_category: int = 60,
    column_number: int = 1,
    data_dir: str = "data"
) -> float:
    """
    Ищет базовую ставку (в CHF) в файлах Table_X_Tariffs.txt.
    Поддерживает как весовые колонки (Таблицы 3, 4), так и мульти-колонки (Таблицы 5, 6, 7).
    """
    file_name = f"Table_{table_number}_Tariffs.txt"
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, data_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл тарифной сетки {file_name} не найден по пути {file_path}")

    # Индекс 0 в parts — это всегда диапазон расстояний ("min-max").
# Соответственно, первая колонка со ставкой всегда находится по индексу 1.

if str(table_number) in ["5", "6", "7"]:
    # Если column_number передается как 1-based номер тарифной колонки (1, 2, 3...):
    target_col_idx = column_number  # parts[1] станет 1-й тарифной колонкой
else:
    # Защита диапазона веса [10; 60]
    safe_weight = max(10, min(60, weight_category))
    col_weight = 60
    for w in WEIGHT_COLUMNS:
        if safe_weight <= w:
            col_weight = w
            break
    # 10 тонн -> index 0 -> parts[1]
    target_col_idx = WEIGHT_COLUMNS.index(col_weight) + 1

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("=") or "Məsafə" in line_str or "CƏDVƏL" in line_str or "Колонки:" in line_str:
                continue

            parts = [p.strip() for p in line_str.split("|")]
            if len(parts) >= 2:
                dist_range = parts[0].split("-")
                if len(dist_range) == 2:
                    try:
                        min_d = int(dist_range[0])
                        max_d = int(dist_range[1])

                        if min_d <= distance_km <= max_d:
                            if target_col_idx < len(parts):
                                rate_str = parts[target_col_idx].replace(",", ".")
                                return float(rate_str)
                    except ValueError:
                        continue

    raise ValueError(f"Расстояние {distance_km} км не найдено в таблице {table_number}")

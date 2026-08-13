import os

# Кэш для ленивой загрузки тарифной сетки Таблицы 11
_TABLE_11_DATA = None

def load_table_11_tariffs():
    """
    Загружает тарифную сетку Таблицы 11 из файла Table_11_Tariffs.txt.
    Файл ищется в папке 'tariff_data/' или в корне проекта.
    """
    global _TABLE_11_DATA
    if _TABLE_11_DATA is not None:
        return _TABLE_11_DATA

    possible_paths = [
        os.path.join("tariff_data", "Table_11_Tariffs.txt"),
        "Table_11_Tariffs.txt"
    ]

    target_path = None
    for p in possible_paths:
        if os.path.exists(p):
            target_path = p
            break

    if not target_path:
        raise FileNotFoundError("Файл Table_11_Tariffs.txt не найден ни в 'tariff_data/', ни в корне проекта!")

    records = []
    with open(target_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("| Məsafə"):
                continue

            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 11:
                # Извлекаем дистанцию "1-10 km" -> min_km, max_km
                dist_str = parts[0].replace("**", "").replace("km", "").strip()
                if "-" in dist_str:
                    min_km, max_km = map(int, dist_str.split("-"))
                else:
                    min_km = max_km = int(dist_str)

                rates = [float(p) for p in parts[1:11]]
                records.append({
                    "min_km": min_km,
                    "max_km": max_km,
                    # 3 yuxarı dərəcəli
                    "deg3_upper_10t_wagon": rates[0],
                    "deg3_upper_10t_ton": rates[1],
                    "deg3_upper_15t_ton": rates[2],
                    "deg3_upper_20t_ton": rates[3],
                    "deg3_upper_25t_ton": rates[4],
                    # 3-5 aşağı, 4-5 yan dərəcəli
                    "deg3_5_lowside_10t_wagon": rates[5],
                    "deg3_5_lowside_10t_ton": rates[6],
                    "deg3_5_lowside_15t_ton": rates[7],
                    "deg3_5_lowside_20t_ton": rates[8],
                    "deg3_5_lowside_25t_ton": rates[9],
                })

    _TABLE_11_DATA = records
    return _TABLE_11_DATA


def calculate_table_11_tariff(distance_km: int, weight_tons: float, oversize_group: str) -> dict:
    """
    Расчёт базового тарифа по Таблице 11 (Cədvəl 11).

    :param distance_km: Расчётное расстояние в км
    :param weight_tons: Фактический вес груза в тоннах
    :param oversize_group: Группа негабаритности:
                           - 'deg3_upper' (3-я верхняя степень)
                           - 'deg3_5_lowside' (3-5 нижняя, 4-5 боковая)
    :return: Словарь с результатами расчета (базовый тариф CHF, тип расчёта, столбец)
    """
    tariffs = load_table_11_tariffs()

    # 1. Поиск строки по расстоянию
    row = None
    for r in tariffs:
        if r["min_km"] <= distance_km <= r["max_km"]:
            row = r
            break

    if not row:
        # Если расстояние больше максимального в таблице (например, > 1000 км)
        row = tariffs[-1]

    is_deg3_upper = (oversize_group == "deg3_upper")

    # 2. Логика весовых категорий
    if weight_tons < 10.0:
        # Вес до 10 тонн -> фиксированная ставка за 1 вагон
        if is_deg3_upper:
            base_chf = row["deg3_upper_10t_wagon"]
            col_name = "3 yuxarı (10 tonadək 1 vaqon - Col 2)"
        else:
            base_chf = row["deg3_5_lowside_10t_wagon"]
            col_name = "3-5 aşağı / 4-5 yan (10 tonadək 1 vaqon - Col 7)"

        billable_weight = weight_tons
        rate_type = "per_wagon"

    else:
        # Вес >= 10 тонн -> потонная ставка умножается на фактический расчётный вес
        rate_type = "per_ton"
        billable_weight = max(10.0, weight_tons)

        # Определение весовой категории для подбора удельной ставки (за 1 т)
        if billable_weight <= 12.0:
            category_key = "10t_ton"
            col_num = 3 if is_deg3_upper else 8
        elif billable_weight <= 17.0:
            category_key = "15t_ton"
            col_num = 4 if is_deg3_upper else 9
        elif billable_weight <= 22.0:
            category_key = "20t_ton"
            col_num = 5 if is_deg3_upper else 10
        else:
            category_key = "25t_ton"
            col_num = 6 if is_deg3_upper else 11

        field_name = f"deg3_upper_{category_key}" if is_deg3_upper else f"deg3_5_lowside_{category_key}"
        rate_per_ton = row[field_name]

        # Базовый тариф = удельная ставка * фактический расчетный вес
        base_chf = round(rate_per_ton * billable_weight, 2)
        group_label = "3 yuxarı" if is_deg3_upper else "3-5 aşağı / 4-5 yan"
        col_name = f"{group_label} (Col {col_num}, {category_key[:-4]}t)"

    return {
        "base_chf": base_chf,
        "billable_weight": billable_weight,
        "rate_type": rate_type,
        "column_info": col_name,
        "table_name": "Cədvəl 11"
    }

import os
import re

def load_table_4_rates():
    """
    Чтение тарифных ставок Таблицы 4 из файла Table_4_Tariffs.txt / Table4.txt.
    """
    possible_files = [
        "Table_4_Tariffs.txt",
        "Table4.txt",
        "tables/Table_4_Tariffs.txt",
        "tables/Table4.txt"
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
                if not line_str or line_str.startswith("#") or line_str.startswith("="):
                    continue

                r_match = re.search(r"^(\d+)\s*[-–]\s*(\d+)", line_str)
                if r_match:
                    d_min, d_max = int(r_match.group(1)), int(r_match.group(2))
                    parts = line_str.split("|")
                    if len(parts) > 1:
                        vals = [float(p.strip().replace(",", ".")) for p in parts[1:] if p.strip()]
                        rates.append((d_min, d_max, vals))
                    else:
                        numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line_str)
                        if len(numbers) >= 3:
                            vals = [float(x.replace(",", ".")) for x in numbers[2:]]
                            rates.append((d_min, d_max, vals))
    return rates


def get_table_4_column_index(billable_weight_tons):
    """
    Точное сопоставление веса с колонками Таблицы 4:
    0: 10t, 1: 15t, 2: 20t, 3: 25t, 4: 30t, 5: 35t, 6: 40t, 7: 45t, 8: 50t, 9: 55t, 10: 60t+
    """
    w = float(billable_weight_tons or 0)
    if w <= 10: return 0
    elif w <= 15: return 1
    elif w <= 20: return 2
    elif w <= 25: return 3
    elif w <= 30: return 4
    elif w <= 35: return 5
    elif w <= 40: return 6
    elif w <= 45: return 7
    elif w <= 50: return 8
    elif w <= 55: return 9
    else: return 10  # Для 60 тонн -> колонка №10 (28.53 CHF/т на 680 км)


def calculate_table_4_base(distance_km, billable_weight_tons, *args, lang="AZ", **kwargs):
    """
    Расчет базовой ставки Таблицы 4 (Универсальные вагоны, Транзит).
    """
    rates = load_table_4_rates()
    col_idx = get_table_4_column_index(billable_weight_tons)
    tbl_name = "Cədvəl 4" if lang == "AZ" else ("Таблица 4" if lang == "RU" else "Table 4")

    if not rates:
        return None, f"{tbl_name} faylı tapılmadı"

    base_chf = None
    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            if col_idx < len(vals):
                base_chf = vals[col_idx]
            elif len(vals) > 0:
                base_chf = vals[-1]
            break

    if base_chf is None:
        return None, f"{tbl_name}, {distance_km} km"

    weight_label = f"{int(billable_weight_tons)} t" if billable_weight_tons else ""
    details_str = f"{tbl_name} ({distance_km} km, {weight_label})"
    
    return base_chf, details_str


def get_table_4_coefficients(*args, **kwargs):
    """
    Коэффициенты Таблицы 4: начисляет 1.20 для транзитных перевозок.
    """
    coeffs = []
    notes = []
    
    # Проверяем аргументы на наличие режима транзита
    args_str = str(args).lower() + str(kwargs).lower()
    if "transit" in args_str or "tranzit" in args_str or True:
        coeffs.append(("Tranzit əmsalı 1.20", 1.20))
        notes.append("Cədvəl 4: Tranzit daşımaları üzrə 1.20 əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

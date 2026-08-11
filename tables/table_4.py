import os
import re
from utils import get_weight_column_index  # Вызов единой сетки Cədvəl 1


def load_table_4_rates():
    """
    Чтение тарифных ставок Таблицы 4 из файла Table_4_Tariffs.txt / Table4.txt.
    """
    possible_files = [
        "Table_4_Tariffs.txt",
        "Table4.txt",
        "tables/Table_4_Tariffs.txt",
        "tables/Table4.txt",
        "tariff_data/Table_4_Tariffs.txt",
        "tariff_data/Table4.txt"
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


def calculate_table_4_base(distance_km, billable_weight_tons, *args, lang="AZ", **kwargs):
    """
    Расчет базовой ставки Таблицы 4 (Транзит — универсальные вагоны).
    """
    rates = load_table_4_rates()
    # Колонка веса по единому правилу Cədvəl 1
    col_idx = get_weight_column_index(billable_weight_tons)
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


def get_table_4_coefficients(shipment_type_code=None, wagon_type=None, gng_code=None, lang="AZ", *args, **kwargs):
    """
    Возвращает специфические коэффициенты Таблицы 4 (при наличии).
    Общие коэффициенты (1.20 цветмет, 1.20 маршрут Алят-Беюк Кесик) обрабатываются в utils.py.
    """
    coeffs = []
    notes = []
    return coeffs, notes

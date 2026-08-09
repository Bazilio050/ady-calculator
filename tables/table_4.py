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
    else: return 10


def calculate_table_4_base(distance_km, billable_weight_tons, *args, lang="AZ", **kwargs):
    """
    Расчет базовой ставки Таблицы 4.
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


def is_non_ferrous_metal_gng(gng_code):
    """
    Проверка кода ГНГ по правилам п. 3.1.1 (коэффициент 1.20)
    """
    g = str(gng_code or "").strip().lstrip("0")
    if not g:
        return False

    exact_prefixes = ["28045090", "28049", "28054", "32121", "7115", "8302", "83079", "8309", "8311", "85481"]
    if any(g.startswith(p) for p in exact_prefixes):
        return True

    if any(g.startswith(str(p)) for p in range(7106, 7113)):
        return True

    if g.startswith("74"):
        return not (g.startswith("7401") or g.startswith("7418"))

    if g.startswith("75"):
        return not g.startswith("7501")

    if g.startswith("76"):
        return not g.startswith("7615")

    if g.startswith("78") or g.startswith("79") or g.startswith("80"):
        return True

    if g.startswith("81"):
        return not g.startswith("81052")

    return False


def get_table_4_coefficients(shipment_type_code=None, wagon_type=None, gng_code=None, lang="AZ", ui_t=None, *args, **kwargs):
    """
    Коэффициенты Таблицы 4 (Транзит)
    """
    coeffs = []
    notes = []

    # Только реальный коэффициент на цветные металлы по п. 3.1.1
    if is_non_ferrous_metal_gng(gng_code):
        lbl = "Əlvan metal 1.20" if lang == "AZ" else ("Цветной металл 1.20" if lang == "RU" else "Non-ferrous metal 1.20")
        coeffs.append((lbl, 1.20))
        notes.append("Cədvəl 4: Əlvan metal / spesifik yüklərə (1,20) artırma əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

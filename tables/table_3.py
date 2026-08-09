import os
import re

def load_table_3_rates():
    """
    Чтение тарифных ставок Таблицы 3 из файла Table_3_Tariffs.txt / Table3.txt.
    """
    possible_files = [
        "Table_3_Tariffs.txt",
        "Table3.txt",
        "tables/Table_3_Tariffs.txt",
        "tables/Table3.txt"
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


def get_table_3_column_index(billable_weight_tons):
    """
    Сопоставление веса с колонками Таблицы 3:
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


def calculate_table_3_base(distance_km, billable_weight_tons, *args, lang="AZ", **kwargs):
    """
    Расчет базовой ставки Таблицы 3 (Импорт / Экспорт универсальные вагоны).
    Возвращает строго 2 значения: (base_chf, details_str)
    """
    rates = load_table_3_rates()
    col_idx = get_table_3_column_index(billable_weight_tons)
    tbl_name = "Cədvəl 3" if lang == "AZ" else ("Таблица 3" if lang == "RU" else "Table 3")

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
    Проверка п. 3.1.1 (1.20) — Цветные металлы, драгметаллы и специфика
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


def is_timber_wood_gng(gng_code):
    """
    Проверка древесины и лесных грузов (1.04) — Группа ГНГ 44
    """
    g = str(gng_code or "").strip().lstrip("0")
    return g.startswith("44")


def get_table_3_coefficients(shipment_type_code=None, wagon_type=None, gng_code=None, lang="AZ", ui_t=None, *args, **kwargs):
    """
    Коэффициенты Таблицы 3 (Импорт / Экспорт).
    ВНИМАНИЕ: Коэффициент 1.50 к Таблице 3 НЕ применяем вообще.
    Возвращает строго 2 значения: (coeffs, notes)
    """
    coeffs = []
    notes = []

    # 1. Цветные металлы и специфика (1.20)
    if is_non_ferrous_metal_gng(gng_code):
        lbl = "Əlvan metal 1.20" if lang == "AZ" else ("Цветной металл 1.20" if lang == "RU" else "Non-ferrous metal 1.20")
        coeffs.append((lbl, 1.20))
        notes.append("Cədvəl 3: Əlvan metal / spesifik yüklərə (1,20) artırma əmsalı tətbiq olunmuşdur.")

    # 2. Лесоматериалы и древесина (1.04)
    if is_timber_wood_gng(gng_code):
        lbl = "Meşə yükləri 1.04" if lang == "AZ" else ("Лесные грузы 1.04" if lang == "RU" else "Timber/Wood 1.04")
        coeffs.append((lbl, 1.04))
        notes.append("Cədvəl 3: Ağac və meşə məhsullarına (GNG 44) 1.04 artırma əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

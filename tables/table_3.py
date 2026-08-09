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


def extract_gng_digits(gng_code, kwargs):
    """
    Универсальное извлечение цифр ГНГ из любых аргументов.
    """
    candidates = [
        gng_code,
        kwargs.get("gng_code"),
        kwargs.get("gng"),
        kwargs.get("cargo_code"),
        kwargs.get("cargo")
    ]
    for c in candidates:
        if c:
            m = re.search(r"\d+", str(c))
            if m:
                return m.group(0)
    return ""


def is_non_ferrous_metal_gng(gng_code, kwargs):
    """
    Проверка п. 3.1.1 (1.20) — Цветные металлы, драгметаллы и специфика
    """
    g = extract_gng_digits(gng_code, kwargs)
    if not g:
        return False

    exact_prefixes = ["28045090", "28049", "28054", "32121", "7115", "8302", "83079", "8309", "8311", "85481"]
    if any(g.startswith(p) for p in exact_prefixes):
        return True

    if len(g) >= 4 and 7106 <= int(g[:4]) <= 7112:
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


def is_import_shipment(shipment_type_code, kwargs):
    """
    Проверка на режим Импорта (idxal)
    """
    candidates = [
        shipment_type_code,
        kwargs.get("shipment_type_code"),
        kwargs.get("shipment_type"),
        kwargs.get("mode")
    ]
    for c in candidates:
        if c:
            st = str(c).lower()
            if "idxal" in st or "import" in st:
                return True
    return True  # По умолчанию для Таблицы 3 в случае сомнений считаем Импортом


def is_104_import_eligible_gng(gng_code, kwargs):
    """
    Проверка коэффициента 1.04 при импорте для:
    1. Лес и пиломатериалы: ГНГ 4403, 4404, 4407–4413
    2. Чёрные металлы: ГНГ 72 (все), 7301–7307
    """
    g = extract_gng_digits(gng_code, kwargs)
    if not g:
        return False

    # 1. Лесоматериалы (4403, 4404, 4407-4413)
    if g.startswith("4403") or g.startswith("4404"):
        return True
    if len(g) >= 4 and 4407 <= int(g[:4]) <= 4413:
        return True

    # 2. Чёрные металлы (72 - все позиции, 7301-7307)
    if g.startswith("72"):
        return True
    if len(g) >= 4 and 7301 <= int(g[:4]) <= 7307:
        return True

    return False


def get_table_3_coefficients(shipment_type_code=None, wagon_type=None, gng_code=None, lang="AZ", ui_t=None, *args, **kwargs):
    """
    Коэффициенты Таблицы 3 (Импорт / Экспорт).
    """
    coeffs = []
    notes = []

    # 1. Цветные металлы и специфика (1.20)
    if is_non_ferrous_metal_gng(gng_code, kwargs):
        lbl = "Əlvan metal 1.20" if lang == "AZ" else ("Цветной металл 1.20" if lang == "RU" else "Non-ferrous metal 1.20")
        coeffs.append((lbl, 1.20))
        notes.append("Cədvəl 3: Əlvan metal / spesifik yüklərə (1,20) artırma əmsalı tətbiq olunmuşdur.")

    # 2. Лесоматериалы (4403, 4404, 4407-4413) и Чёрные металлы (72, 7301-7307) при ИМПОРТЕ -> 1.04
    if is_import_shipment(shipment_type_code, kwargs) and is_104_import_eligible_gng(gng_code, kwargs):
        lbl = "İdxal yükləri (1.04)" if lang == "AZ" else ("Импортные грузы (1.04)" if lang == "RU" else "Import cargo (1.04)")
        coeffs.append((lbl, 1.04))
        notes.append("Cədvəl 3: İdxal daşımaları zamanı taxta (4403, 4404, 4407-4413) və qara metallara (72, 7301-7307) 1.04 əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

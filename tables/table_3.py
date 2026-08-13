import os
import re
from utils import get_weight_column_index, extract_gng_digits


def load_table_3_rates():
    """
    Чтение тарифных ставок Таблицы 3 из файла Table_3_Tariffs.txt / Table3.txt.
    """
    possible_files = [
        "Table_3_Tariffs.txt",
        "Table3.txt",
        "tables/Table_3_Tariffs.txt",
        "tables/Table3.txt",
        "tariff_data/Table_3_Tariffs.txt",
        "tariff_data/Table3.txt"
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


def calculate_table_3_base(distance_km, billable_weight_tons, *args, lang="AZ", **kwargs):
    """
    Расчет базовой ставки Таблицы 3 (Импорт / Экспорт универсальные вагоны).
    """
    rates = load_table_3_rates()
    col_idx = get_weight_column_index(billable_weight_tons)
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


def is_import_shipment(shipment_type_code, kwargs):
    """
    Безопасная проверка на режим Импорта (idxal)
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
            if "ixrac" in st or "export" in st or "daxili" in st or "tranzit" in st:
                return False
    return False


def get_table_3_coefficients(shipment_type_code=None, gng_code=None, lang="AZ", *args, **kwargs):
    """
    Возвращает коэффициенты, специфичные ТОЛЬКО для Таблицы 3.
    """
    coeffs = []
    notes = []

    st = str(shipment_type_code or kwargs.get("shipment_type") or kwargs.get("mode") or "").lower()
    g_raw = gng_code or kwargs.get("gng") or kwargs.get("cargo_gng_code") or ""
    g = re.sub(r'\D', '', str(g_raw))

    if "idxal" in st or "import" in st:
        is_wood = False
        is_metal = False

        if g:
            if g.startswith("4403") or g.startswith("4404") or (len(g) >= 4 and 4407 <= int(g[:4]) <= 4413):
                is_wood = True
            elif g.startswith("72") or (len(g) >= 4 and 7301 <= int(g[:4]) <= 7307):
                is_metal = True

        if is_wood or is_metal or not g:
            lbl = "İdxal yükləri 1.04" if lang == "AZ" else ("Импортные грузы 1.04" if lang == "RU" else "Import cargo 1.04")
            coeffs.append((lbl, 1.04))

            if is_metal:
                note_msg = (
                    "Cədvəl 3: İdxal daşımaları zamanı qara metallara 1.04 əmsalı tətbiq olunmuşdur."
                    if lang == "AZ" else
                    ("Таблица 3: При импорте чёрных металлов применяется коэффициент 1.04."
                     if lang == "RU" else
                     "Table 3: 1.04 coefficient applied for import of ferrous metals.")
                )
            else:
                note_msg = (
                    "Cədvəl 3: İdxal daşımaları zamanı meşə materiallarına (taxta) 1.04 əmsalı tətbiq olunmuşdur."
                    if lang == "AZ" else
                    ("Таблица 3: При импорте лесоматериалов применяется коэффициент 1.04."
                     if lang == "RU" else
                     "Table 3: 1.04 coefficient applied for import of timber.")
                )
            notes.append(note_msg)

    return coeffs, notes

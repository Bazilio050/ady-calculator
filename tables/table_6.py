import os
import json
import re
from utils import extract_gng_digits


def load_table_6_config():
    """Загрузка конфигурации и правил Таблицы 6 из table_6_config.json."""
    config_path = "tables/table_6_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_table_6_rates():
    """Чтение тарифных ставок из Table_6_Tariffs.txt / Table6.txt."""
    possible_files = [
        "Table_6_Tariffs.txt",
        "Table6.txt",
        "tables/Table_6_Tariffs.txt",
        "tables/Table6.txt",
        "tariff_data/Table_6_Tariffs.txt",
        "tariff_data/Table6.txt"
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
                if not line_str or line_str.startswith("#") or line_str.startswith("=") or "Məsafə" in line_str or "Col" in line_str:
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
                        if len(numbers) >= 2:
                            vals = [float(x.replace(",", ".")) for x in numbers[1:]]
                            rates.append((d_min, d_max, vals))
    return rates


def determine_table_6_column(gng_code, park_type="SPS") -> int:
    """
    Определяет индекс колонки (0..6, соответствующие Col 2..Col 8 в Table_6_Tariffs.txt):
    col_idx 0 = Столбец 2 (Нефть и нефтепродукты)
    col_idx 1 = Столбец 3 (Энергетические газы)
    col_idx 2 = Столбец 4 (Газы и углеводороды)
    col_idx 3 = Столбец 5 (Спирт и фенолы)
    col_idx 4 = Столбец 6 (Скоропортящиеся жидкие)
    col_idx 5 = Столбец 7 (Другие грузы)
    col_idx 6 = Столбец 8 (Частные цистерны / Özəl çənlər - только 29023, 27071-27073 и т.д.)
    """
    clean_gng = extract_gng_digits(gng_code)
    norm_gng = clean_gng.lstrip("0") if clean_gng else ""

    # 1. Столбец 8 (Özəl çənlər) — только для узкого списка углеводородов
    private_only_prefixes = ["290211", "29022", "29023", "290241", "290242", "290243", "290244", "29026", "29027", "29029", "27071", "27072", "27073"]
    if park_type == "SPS" and any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in private_only_prefixes):
        return 6  # Столбец 8

    # 2. Столбец 2 (Нефть и нефтепродукты)
    oil_prefixes = ["2709", "2710", "2712", "2713", "2714", "2715", "3403", "3404", "3811", "3817", "3824"]
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in oil_prefixes):
        return 0  # Столбец 2

    # 3. Столбец 3 (Энергетические газы)
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in ["2705", "2711"]):
        return 1  # Столбец 3

    # 4. Столбец 4 (Газы и химические углеводороды)
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in ["2801", "2804", "2811", "2812", "2814", "2853", "2901", "2902", "3817", "3823"]):
        return 2  # Столбец 4

    # 5. Столбец 5 (Спирты и фенолы)
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in ["1520", "27077", "27079", "2905", "2906", "2907", "2908", "2909", "2932", "2933", "3820", "3905"]):
        return 3  # Столбец 5

    # 6. Столбец 6 (Пищевые и скоропортящиеся)
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in ["0401", "0403", "0404", "0405", "0406", "1501", "1502", "1503", "1504", "1505", "1506", "1507", "1508", "1509", "1510", "1511", "1512", "1513", "1514", "1515", "1516", "1517", "1518", "2009", "2105", "2201", "2202", "2203", "2204", "2205", "2206"]):
        return 4  # Столбец 6

    return 5  # По умолчанию Столбец 7 (Digər yüklər)


def calculate_table_6_base(distance_km, billable_weight_tons, gng_code, park_type="SPS", *args, lang="AZ", **kwargs):
    """
    Рассчитывает базовую тарифную ставку по Таблице 6 (Наливные грузы в цистернах).
    Возвращает: (rate_per_ton, details_str)
    """
    col_idx = determine_table_6_column(gng_code, park_type)
    rates = load_table_6_rates()
    tbl_name = "Cədvəl 6" if lang == "AZ" else ("Таблица 6" if lang == "RU" else "Table 6")

    if not rates:
        return None, f"{tbl_name} faylı tapılmadı"

    rate_per_ton = None
    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            if col_idx < len(vals):
                rate_per_ton = vals[col_idx]
            elif len(vals) > 0:
                rate_per_ton = vals[-1]
            break

    if rate_per_ton is None:
        return None, f"{tbl_name}, {distance_km} km"

    details_str = f"{tbl_name} ({distance_km} km, sütun {col_idx + 2})"
    return rate_per_ton, details_str


def get_table_6_coefficients(shipment_type_code=None, wagon_type=None, gng_code=None, park_type="SPS", lang="AZ", *args, **kwargs):
    """
    Специфические коэффициенты Таблицы 6:
    Повышающий 1.20 для Нефти и Нефтепродуктов (Столбец 2) строго при ИМПОРТЕ или ТРАНЗИТЕ.
    На ЭКСПОРТ 1.20 НЕ применяется!
    """
    coeffs = []
    notes = []
    clean_gng = extract_gng_digits(gng_code)
    col_idx = determine_table_6_column(clean_gng, park_type)
    
    st_lower = str(shipment_type_code or kwargs.get("shipment_type") or kwargs.get("mode") or "").lower()

    # Коэффициент 1.20 применяется ТОЛЬКО для Импорта и Транзита (на Экспорт НЕ распространяется)
    if col_idx == 0 and any(k in st_lower for k in ["import", "transit", "idxal", "tranzit"]):
        c_val_oil = 1.20
        c_lbl_oil = "Neft/Neft məhsulları 1.20" if lang == "AZ" else ("Нефть/Нефтепродукты 1.20" if lang == "RU" else "Oil/Petroleum 1.20")
        coeffs.append((c_lbl_oil, c_val_oil))
        notes.append("Cədvəl 6: İdxal və ya tranzit rejimində neft və neft məhsullarına 1.20 artırma əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

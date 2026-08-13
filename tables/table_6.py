import os
import re


def extract_gng_digits(val) -> str:
    """Безопасно извлекает только цифры из кода ГНГ любого типа."""
    if val is None:
        return ""
    if isinstance(val, dict):
        val = val.get("cargo_gng_code") or val.get("gng_code") or val.get("code") or ""
    return re.sub(r'\D', '', str(val))


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


def determine_table_6_column(gng_code=None, park_type="SPS", *args, **kwargs) -> int:
    """
    Определение столбца Таблицы 6:
    col_idx 0 = Столбец 2 (Нефть и нефтепродукты: 2709, 2710, 2712, 2713, 2714, 2715, 3403, 3404...)
    col_idx 1 = Столбец 3 (Энергетические газы)
    col_idx 2 = Столбец 4 (Газы и химические углеводороды)
    col_idx 3 = Столбец 5 (Спирты и фенолы)
    col_idx 4 = Столбец 6 (Скоропортящиеся / жиры 1501-1506)
    col_idx 5 = Столбец 7 (Другие грузы, ВКЛЮЧАЯ растительные масла 1507-1515)
    col_idx 6 = Столбец 8 (Частные цистерны / Özəl çənlər - строго 29023, 27071-27073)
    """
    if gng_code is None or isinstance(gng_code, dict):
        d = gng_code if isinstance(gng_code, dict) else kwargs
        gng_code = d.get("cargo_gng_code") or d.get("gng_code") or d.get("code") or ""

    clean_gng = extract_gng_digits(gng_code)
    norm_gng = clean_gng.lstrip("0") if clean_gng else ""
    park_type = str(park_type or "SPS").upper()

    # 1. ПРИОРИТЕТ №1: Нефть и нефтепродукты (Столбец 2 -> col_idx 0)
    oil_prefixes = ["2709", "2710", "2712", "2713", "2714", "2715", "3403", "3404", "3811", "3817", "3824"]
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in oil_prefixes):
        return 0

    # 2. ПРИОРИТЕТ №2: Частные цистерны (Столбец 8 -> col_idx 6) - только для 2707 и 2902
    private_only_prefixes = [
        "27071", "27072", "27073", "290211", "29022", "29023",
        "290241", "290242", "290243", "290244", "29026", "29027", "29029"
    ]
    if park_type == "SPS" and any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in private_only_prefixes):
        return 6

    # 3. Энергетические газы (Столбец 3 -> col_idx 1)
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in ["2705", "2711"]):
        return 1

    # 4. Газы и химические углеводороды (Столбец 4 -> col_idx 2)
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in ["2801", "2804", "2811", "2812", "2814", "2853", "2901", "2902", "3823"]):
        return 2

    # 5. Спирты и фенолы (Столбец 5 -> col_idx 3)
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in ["1520", "27077", "27079", "2905", "2906", "2907", "2908", "2909", "2932", "2933", "3820", "3905"]):
        return 3

    # 6. Скоропортящиеся жидкие грузы (Столбец 6 -> col_idx 4)
    food_prefixes = [
        "0401", "0403", "0404", "0405", "0406", 
        "1501", "1502", "1503", "1504", "1505", "1506", 
        "151610", "151790", "2009", "2105", "2201", "2202", "2203", "2204", "2205", "2206"
    ]
    if any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in food_prefixes):
        return 4

    # 7. Фоллбек: Прочие грузы (Столбец 7 -> col_idx 5)
    return 5


def calculate_table_6_base(distance_km, billable_weight_tons, gng_code=None, park_type="SPS", *args, lang="AZ", **kwargs):
    col_idx = determine_table_6_column(gng_code, park_type, **kwargs)
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
    coeffs = []
    notes = []
    
    g_raw = gng_code or kwargs.get("gng") or kwargs.get("cargo_gng_code") or ""
    clean_gng = extract_gng_digits(g_raw)
    norm_gng = clean_gng.lstrip("0") if clean_gng else ""
    
    st_lower = str(shipment_type_code or kwargs.get("shipment_type") or kwargs.get("mode") or "").lower()

    # 💡 Повышающий коэффициент 1.20 строго для сырой нефти и основных нефтепродуктов (2709, 2710, 2712, 2713, 2714, 2715)
    oil_surcharge_prefixes = ["2709", "2710", "2712", "2713", "2714", "2715"]
    is_oil_cargo = any(norm_gng.startswith(p) or clean_gng.startswith(p) for p in oil_surcharge_prefixes)

    if is_oil_cargo and any(k in st_lower for k in ["import", "transit", "idxal", "tranzit"]):
        c_val_oil = 1.20
        c_lbl_oil = "Neft/Neft məhsulları" if lang == "AZ" else ("Нефть/Нефтепродукты" if lang == "RU" else "Oil/Petroleum")
        coeffs.append((c_lbl_oil, c_val_oil))
        notes.append("Cədvəl 6: İdxal və ya tranzit rejimində neft və neft məhsullarına 1.20 artırma əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

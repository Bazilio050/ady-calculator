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


def determine_table_6_column(gng_code, park_type="SPS"):
    """
    Определяет индекс колонки (0..6, соответствующие Col 2..Col 8 в Table_6_Tariffs.txt)
    на основе ГНГ и группы (Инвентарные МПС vs Частные СПС).
    """
    clean_gng = extract_gng_digits(gng_code)
    park_type = str(park_type or "SPS").upper()

    t6_cfg = load_table_6_config()
    mapping = t6_cfg.get("table_6_rules", {}).get("columns_mapping", {})

    # 1. Если цистерна частная (Özəl / SPS) — проверяем попадание под спец-список углеводородов (Столбец 8 -> col_idx 6)
    if park_type == "SPS":
        sps_rules = mapping.get("sps_private", [])
        for rule in sps_rules:
            prefixes = rule.get("gng_prefixes", [])
            if any(clean_gng.startswith(p) for p in prefixes if p):
                return rule.get("column_index", 6)

    # 2. Во всех остальных случаях (МПС или стандартные наливные грузы) выбираем колонки 2..7 (col_idx 0..5)
    mps_rules = mapping.get("mps_inventory", [])
    default_col = 5  # "Digər yüklər" (Col 7)

    for rule in mps_rules:
        if rule.get("is_default"):
            default_col = rule.get("column_index", 5)
            continue

        prefixes = rule.get("gng_prefixes", [])
        excludes = rule.get("exclude_prefixes", [])

        if any(clean_gng.startswith(p) for p in prefixes if p) and not any(clean_gng.startswith(ex) for ex in excludes if ex):
            return rule.get("column_index", 5)

    return default_col


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
    """
    coeffs = []
    notes = []
    clean_gng = extract_gng_digits(gng_code, kwargs)
    col_idx = determine_table_6_column(clean_gng, park_type)
    
    st_lower = str(shipment_type_code or kwargs.get("shipment_type") or kwargs.get("mode") or "").lower()

    # Повышающий коэффициент 1.20 для Нефти и Нефтепродуктов (Столбец 2) ТОЛЬКО при ИМПОРТЕ или ТРАНЗИТЕ
    if col_idx == 0 and any(k in st_lower for k in ["import", "transit", "idxal", "tranzit"]):
        c_val_oil = 1.20
        c_lbl_oil = "Neft/Neft məhsulları 1.20" if lang == "AZ" else ("Нефть/Нефтепродукты 1.20" if lang == "RU" else "Oil/Petroleum 1.20")
        coeffs.append((c_lbl_oil, c_val_oil))
        notes.append("Cədvəl 6: İdxal və ya tranzit rejimində neft və neft məhsullarına 1.20 artırma əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

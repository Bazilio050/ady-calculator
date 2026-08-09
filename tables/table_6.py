import os
import json
import re


def load_table_6_config():
    """Загрузка конфигурации и правил Таблицы 6 из table_6_config.json."""
    config_path = "tables/table_6_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки {config_path}: {e}")
    return {}


def load_table_6_rates():
    """Чтение тарифных ставок из Table_6_Tariffs.txt / Table6.txt."""
    possible_files = [
        "Table_6_Tariffs.txt",
        "Table6.txt",
        "tables/Table_6_Tariffs.txt",
        "tables/Table6.txt"
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

                r_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", line_str)
                if r_match:
                    d_min, d_max = int(r_match.group(1)), int(r_match.group(2))
                    parts = line_str.split("|")
                    if len(parts) > 1:
                        vals = [float(p.strip().replace(",", ".")) for p in parts[1:] if p.strip()]
                        rates.append((d_min, d_max, vals))
                    else:
                        numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line_str)
                        if len(numbers) >= 2:
                            val = float(numbers[-1].replace(",", "."))
                            rates.append((d_min, d_max, [val]))
    return rates


def determine_table_6_column(gng_code, park_type="SPS"):
    """
    Определяет индекс колонки (0..6, соответствующие Col 2..Col 8) на основе ГНГ и типа парка (MPS или SPS).
    """
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    park_type = str(park_type or "SPS").upper()

    t6_cfg = load_table_6_config()
    mapping = t6_cfg.get("table_6_rules", {}).get("columns_mapping", {})

    # 1. Проверка для частных цистерн (Özəl çənlər / SPS) -> Col 8 (индекс 6)
    if park_type == "SPS":
        sps_rules = mapping.get("sps_private", [])
        for rule in sps_rules:
            prefixes = rule.get("gng_prefixes", [])
            if any(clean_gng.startswith(p) for p in prefixes if p):
                return rule.get("column_index", 6)

    # 2. Проверка для инвентарных цистерн (İnventar parka məxsus / MPS) -> Col 2..Col 7 (индексы 0..5)
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


def calculate_table_6_base(distance_km, billable_weight_tons, gng_code, park_type, config, lang="AZ"):
    """
    Рассчитывает базовую тарифную ставку по Таблице 6 (Наливные грузы в цистернах).
    Возвращает 2 значения: (rate_per_ton, details_str).
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


def get_table_6_coefficients(shipment_type_code, wagon_type, gng_code, park_type="SPS", lang="AZ", ui_t=None):
    """
    Проверяет и возвращает специфичные коэффициенты Таблицы 6:
    1. Базовый 1.50 для Импорта/Экспорта (Исключения: Нефть/Нефтепродукты и Метанол).
    2. Повышающий 1.20 для Нефти и Нефтепродуктов при Импорте или Транзите.
    """
    if ui_t is None:
        ui_t = {}

    coeffs = []
    notes = []
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    col_idx = determine_table_6_column(clean_gng, park_type)

    # 1. Применение базового коэффициента Импорта/Экспорта (1.50)
    if shipment_type_code in ["import", "export"]:
        is_150_exception = False

        # Исключение 1: Нефть и нефтепродукты (Столбец 2 - col_idx == 0)
        if col_idx == 0:
            is_150_exception = True

        # Исключение 2: Метанол (ГНГ 29051100 / 290511)
        if clean_gng.startswith("290511"):
            is_150_exception = True

        if not is_150_exception:
            c_val = 1.50
            c_lbl = "İdxal/İxrac baza 1.50" if lang == "AZ" else ("Импорт/Экспорт база 1.50" if lang == "RU" else "Import/Export base 1.50")
            coeffs.append((c_lbl, c_val))
            if "note_import_base_150" in ui_t:
                notes.append(ui_t["note_import_base_150"])

    # 2. Повышающий коэффициент 1.20 для Нефти и Нефтепродуктов (Столбец 2) при ИМПОРТЕ или ТРАНЗИТЕ
    if shipment_type_code in ["import", "transit"] and col_idx == 0:
        c_val_oil = 1.20
        c_lbl_oil = "Neft/Neft məhsulları 1.20" if lang == "AZ" else ("Нефть/Нефтепродукты 1.20" if lang == "RU" else "Oil/Petroleum 1.20")
        coeffs.append((c_lbl_oil, c_val_oil))

        note_oil = {
            "AZ": "Cədvəl 6: İdxal və ya tranzit rejimində neft və neft məhsullarına 1.20 artırma əmsalı tətbiq olunmuşdur.",
            "RU": "Таблица 6: Применен повышающий коэффициент 1.20 для нефти и нефтепродуктов при импорте или транзите.",
            "EN": "Table 6: A 1.20 markup coefficient applied for oil and petroleum products in import or transit mode."
        }
        notes.append(note_oil.get(lang, note_oil["AZ"]))

    return coeffs, notes

import os
import json
import re


def load_table_4_config():
    """Загрузка конфигурации и правил Таблицы 4."""
    config_path = "tables/table_4_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки {config_path}: {e}")
    return {}


def load_table_4_rates():
    """Чтение тарифных ставок транзита."""
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
                r_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", line)
                if r_match:
                    d_min, d_max = int(r_match.group(1)), int(r_match.group(2))
                    parts = line.split("|")
                    if len(parts) > 1:
                        vals = [float(p.strip().replace(",", ".")) for p in parts[1:] if p.strip()]
                        rates.append((d_min, d_max, vals))
                    else:
                        numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line)
                        if len(numbers) >= 2:
                            val = float(numbers[-1].replace(",", "."))
                            rates.append((d_min, d_max, [val]))
    return rates


def calculate_table_4_base(distance_km, billable_weight_tons, config, lang="AZ"):
    """Рассчитывает базовую тарифную ставку по Таблице 4."""
    rates = load_table_4_rates()
    tbl_name = "Cədvəl 4" if lang == "AZ" else ("Таблица 4" if lang == "RU" else "Table 4")

    if not rates:
        return None, f"{tbl_name} faylı tapılmadı"

    weight_intervals = config.get("tables_1_4_weight_intervals", [])
    if not weight_intervals:
        t4_cfg = load_table_4_config()
        weight_intervals = t4_cfg.get("tables_1_4_weight_intervals", [])

    col_idx = 7
    for item in weight_intervals:
        if item.get("min_weight", 0) <= billable_weight_tons <= item.get("max_weight", 999):
            col_idx = item.get("column_index", 7)
            break

    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            val = vals[col_idx] if len(vals) == 11 else (vals[min(col_idx, len(vals) - 1)] if len(vals) > 1 else vals[0])
            return val, f"{tbl_name}, {d_min}-{d_max} km, {int(billable_weight_tons)} t"

    return None, f"{tbl_name}, {distance_km} km"


def get_table_4_coefficients(shipment_type_code, wagon_type, gng_code, lang="AZ", ui_t=None):
    """
    Проверяет и возвращает коэффициенты Таблицы 4 (Транзит).
    Включает пункт 3.1.1 (1.20 для цветных металлов и спецхимии).
    """
    if ui_t is None:
        ui_t = {}

    coeffs = []
    notes = []

    clean_gng = re.sub(r'\D', '', str(gng_code or ""))

    default_nf_prefixes = [
        "28045090", "28049", "28054", "32121",
        "7106", "7107", "7108", "7109", "7110", "7111", "7112", "7115",
        "74", "75", "76", "78", "79", "80", "81",
        "8302", "83079", "8309", "8311", "85481"
    ]
    default_nf_excludes = ["7401", "7418", "7501", "7615", "81052"]

    t4_cfg = load_table_4_config()
    rules = t4_cfg.get("coefficients_updated_rules_2026", {})
    nf_cfg = rules.get("non_ferrous_metals_1_20", {})

    nf_prefixes = nf_cfg.get("gng_prefixes", default_nf_prefixes)
    nf_excludes = nf_cfg.get("exclude_prefixes", default_nf_excludes)

    if clean_gng:
        is_non_ferrous = any(clean_gng.startswith(p) for p in nf_prefixes if p) and not any(clean_gng.startswith(ex) for ex in nf_excludes if ex)

        if is_non_ferrous:
            c_val = nf_cfg.get("coefficient_value", 1.20)
            c_lbl = nf_cfg.get("labels", {}).get(lang, "Əlvan metallar 1.20") if isinstance(nf_cfg.get("labels"), dict) else "Əlvan metallar 1.20"
            coeffs.append((c_lbl, c_val))

            note_nf = {
                "AZ": "Cədvəl 4 (bənd 3.1.1): Əlvan metallar, qiymətli metallar və xüsusi kimyəvi yüklər üzrə 1.20 artırma əmsalı tətbiq olunmuşdur.",
                "RU": "Таблица 4 (п. 3.1.1): Применен повышающий коэффициент 1.20 для цветных/драгоценных металлов и спецхимии.",
                "EN": "Table 4 (cl. 3.1.1): A 1.20 markup coefficient applied for non-ferrous/precious metals and special chemicals."
            }
            notes.append(note_nf.get(lang, note_nf["AZ"]))

    return coeffs, notes

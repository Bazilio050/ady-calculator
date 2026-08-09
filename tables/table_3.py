import os
import json
import re


def load_table_3_config():
    """
    Загружает конфигурацию и правила Таблицы 3 из справочника table_3_config.json.
    """
    config_path = "tables/table_3_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки {config_path}: {e}")
    return {}


def load_table_3_rates():
    """
    Оригинальный рабочая функция чтения тарифных ставок из текстового файла.
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


def calculate_table_3_base(distance_km, billable_weight_tons, config, lang="AZ"):
    """
    Оригинальная рабочая функция расчета базовой ставки.
    """
    rates = load_table_3_rates()
    tbl_name = "Cədvəl 3" if lang == "AZ" else ("Таблица 3" if lang == "RU" else "Table 3")

    if not rates:
        return None, f"{tbl_name} faylı tapılmadı"

    weight_intervals = config.get("tables_1_4_weight_intervals", [])
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


def get_table_3_coefficients(shipment_type_code, wagon_type, gng_code, lang="AZ", ui_t=None):
    """
    Проверяет и возвращает специфичные коэффициенты Таблицы 3.
    """
    if ui_t is None:
        ui_t = {}

    coeffs = []
    notes = []
    gng = str(gng_code or "").strip()
    w_type = str(wagon_type or "universal").lower()

    t3_cfg = load_table_3_config()
    rules = t3_cfg.get("coefficients_updated_rules_2026", {})

    # 1. Повышающий коэффициент 1.20 (Цветные металлы, спецхимия - п. 3.1.1)
    nf_cfg = rules.get("non_ferrous_metals_1_20", {})
    if nf_cfg and gng:
        nf_prefixes = nf_cfg.get("gng_prefixes", [])
        nf_excludes = nf_cfg.get("exclude_prefixes", [])

        is_non_ferrous = any(gng.startswith(p) for p in nf_prefixes if p) and not any(gng.startswith(ex) for ex in nf_excludes if ex)

        if is_non_ferrous:
            c_val = nf_cfg.get("coefficient_value", 1.20)
            c_lbl = nf_cfg.get("labels", {}).get(lang, "Əlvan metallar 1.20")
            coeffs.append((c_lbl, c_val))

            note_nf = {
                "AZ": "Cədvəl 3 (bənd 3.1.1): Əlvan metallar, qiymətli metallar və xüsusi kimyəvi yüklər üzrə 1.20 artırma əmsalı tətbiq olunmuşdur.",
                "RU": "Таблица 3 (п. 3.1.1): Применен повышающий коэффициент 1.20 для цветных/драгоценных металлов и спецхимии.",
                "EN": "Table 3 (cl. 3.1.1): A 1.20 markup coefficient applied for non-ferrous/precious metals and special chemicals."
            }
            notes.append(note_nf.get(lang, note_nf["AZ"]))

    # 2. Коэффициенты Импорта и Экспорта (1.50 и 1.04)
    if shipment_type_code in ["import", "export"]:
        ie_cfg = rules.get("import_export_base_1_50", {})
        if ie_cfg:
            exceptions = ie_cfg.get("exceptions", {})
            is_150_exception = False

            wood_codes = exceptions.get("wood_gng_prefixes", ["4403", "4404", "4407"])
            if w_type == "universal" and any(gng.startswith(w) for w in wood_codes if w):
                is_150_exception = True

            metal_codes = exceptions.get("metal_gng_prefixes", ["72", "73"])
            if w_type == "universal" and any(gng.startswith(m) for m in metal_codes if m):
                is_150_exception = True

            if not is_150_exception:
                c_val = ie_cfg.get("coefficient_value", 1.50)
                c_lbl = ie_cfg.get("labels", {}).get(lang, "İdxal/İxrac baza 1.50")
                coeffs.append((c_lbl, c_val))
                if "note_import_base_150" in ui_t:
                    notes.append(ui_t["note_import_base_150"])

        imp_cfg = rules.get("import_metal_wood_1_04", {})
        if imp_cfg and shipment_type_code == "import":
            imp_prefixes = imp_cfg.get("gng_prefixes", ["44", "72", "73"])
            if any(gng.startswith(p) for p in imp_prefixes if p):
                c_val = imp_cfg.get("coefficient_value", 1.04)
                c_lbl = imp_cfg.get("labels", {}).get(lang, "İdxal meşə/metal 1.04")
                coeffs.append((c_lbl, c_val))
                if "note_timber_metal" in ui_t:
                    notes.append(ui_t["note_timber_metal"])

    return coeffs, notes

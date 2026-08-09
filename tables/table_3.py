import os
import json


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


def calculate_table_3_base(distance_km, billable_weight_tons, config, lang="AZ"):
    """
    Находит базовую ставку за тонну по Таблице 3 в зависимости от расстояния.
    """
    t3_cfg = load_table_3_config()
    rates = t3_cfg.get("distance_rates", [])

    # Если в t3_cfg сетка ставок не найдена, смотрим в общем конфиге (страховка)
    if not rates:
        rates = config.get("table_3_rates", [])

    selected_rate = None
    for item in rates:
        min_d = item.get("min_km", 0)
        max_d = item.get("max_km", 9999)
        if min_d <= distance_km <= max_d:
            selected_rate = item
            break

    if not selected_rate and rates:
        selected_rate = rates[-1]

    if not selected_rate:
        return None, "Таблица 3 не найдена", False

    rate_per_ton = selected_rate.get("rate_chf_per_ton", 0.0)

    details_str = f"Cədvəl 3 ({distance_km} km)" if lang == "AZ" else (
        f"Таблица 3 ({distance_km} км)" if lang == "RU" else f"Table 3 ({distance_km} km)"
    )

    return rate_per_ton, details_str, False


def get_table_3_coefficients(shipment_type_code, wagon_type, gng_code, lang="AZ", ui_t=None):
    """
    Проверяет и возвращает коэффициенты, относящиеся к Таблице 3:
    1. Повышающий 1.20 для цветных металлов и спецхимии (п. 3.1.1).
    2. Базовый 1.50 для Импорта/Экспорта (и исключения для него).
    3. Специальный 1.04 для импорта леса и черных металлов.
    """
    if ui_t is None:
        ui_t = {}

    coeffs = []
    notes = []
    gng = str(gng_code or "").strip()
    w_type = str(wagon_type or "universal").lower()

    # Загружаем правила из нашего справочника table_3_config.json
    t3_cfg = load_table_3_config()
    rules = t3_cfg.get("coefficients_updated_rules_2026", {})

    # -------------------------------------------------------------------
    # Правило 1: Коэффициент 1.20 (Цветные металлы, спецхимия - п. 3.1.1)
    # -------------------------------------------------------------------
    nf_cfg = rules.get("non_ferrous_metals_1_20", {})
    if nf_cfg and gng:
        nf_prefixes = nf_cfg.get("gng_prefixes", [])
        nf_excludes = nf_cfg.get("exclude_prefixes", [])

        # Проверяем совпадение кода ГНГ со списком цветных металлов
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

    # -------------------------------------------------------------------
    # Правило 2: Коэффициенты Импорта и Экспорта (1.50 и 1.04)
    # -------------------------------------------------------------------
    if shipment_type_code in ["import", "export"]:
        # Базовый коэффициент 1.50
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

        # Импортный коэффициент 1.04 (для леса и черных металлов)
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

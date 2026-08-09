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
    Универсальный поиск базовой ставки по Таблице 3 для расстояния distance_km и веса billable_weight_tons.
    Возвращает ровно 2 значения: (rate_per_ton, details_str).
    """
    t3_cfg = load_table_3_config()

    # 1. Поиск массива ставок во всех возможных источниках
    rates = (
        t3_cfg.get("distance_rates")
        or t3_cfg.get("rates")
        or t3_cfg.get("distance_matrix")
        or (config.get("table_3_rates") if isinstance(config, dict) else None)
        or (config.get("distance_rates") if isinstance(config, dict) else None)
        or []
    )

    # 2. Определение индекса весовой колонки (если используется матрица весов)
    weight_intervals = t3_cfg.get("tables_1_4_weight_intervals", [])
    col_idx = 0
    if weight_intervals:
        for interval in weight_intervals:
            w_min = interval.get("min_weight", 0)
            w_max = interval.get("max_weight", 999)
            if w_min <= billable_weight_tons <= w_max:
                col_idx = interval.get("column_index", 0)
                break

    selected_rate_item = None
    if isinstance(rates, list) and len(rates) > 0:
        for item in rates:
            if isinstance(item, dict):
                min_d = item.get("min_km", item.get("min_dist", 0))
                max_d = item.get("max_km", item.get("max_dist", 9999))
                if min_d <= distance_km <= max_d:
                    selected_rate_item = item
                    break

        if not selected_rate_item and rates:
            selected_rate_item = rates[-1]

    # 3. Извлечение значения ставки из найденного элемента
    rate_per_ton = None
    if selected_rate_item:
        if "rate_chf_per_ton" in selected_rate_item:
            rate_per_ton = float(selected_rate_item["rate_chf_per_ton"])
        elif "rate" in selected_rate_item:
            rate_per_ton = float(selected_rate_item["rate"])
        elif "rates" in selected_rate_item and isinstance(selected_rate_item["rates"], list):
            r_list = selected_rate_item["rates"]
            if col_idx < len(r_list):
                rate_per_ton = float(r_list[col_idx])
            elif len(r_list) > 0:
                rate_per_ton = float(r_list[-1])

    if rate_per_ton is None:
        return None, "Таблица 3 не найдена"

    details_str = f"Cədvəl 3 ({distance_km} km)" if lang == "AZ" else (
        f"Таблица 3 ({distance_km} км)" if lang == "RU" else f"Table 3 ({distance_km} km)"
    )

    return rate_per_ton, details_str


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

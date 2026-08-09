import os
import json


def load_table_3_config():
    """Загрузка конфигурации ставок и правил Таблицы 3."""
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
    Рассчитывает базовую тарифную ставку по Таблице 3 (Повагонные отправки в универсальных вагонах).
    """
    t3_cfg = load_table_3_config()
    rates = t3_cfg.get("distance_rates", [])

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


def get_table_3_coefficients(shipment_type_code, wagon_type, gng_code, config, lang, ui_t):
    """
    Возвращает специфичные коэффициенты Таблицы 3 (Импорт и Экспорт).
    Перенесено из engine.py для соблюдения модульной структуры.
    """
    coeffs = []
    notes = []
    gng = str(gng_code or "").strip()
    w_type = str(wagon_type or "universal").lower()

    if shipment_type_code not in ["import", "export"]:
        return coeffs, notes

    # 1. Базовый коэффициент 1.50 для Импорта/Экспорта и его исключения
    ie_config = config.get("coefficients_updated_rules_2026", {}).get("import_export_base_1_50", {})
    exceptions = ie_config.get("exceptions", {})
    is_150_exception = False

    wood_codes = exceptions.get("wood_gng_prefixes", ["4403", "4404", "4407"])
    if w_type == "universal" and any(gng.startswith(w) for w in wood_codes if w):
        is_150_exception = True

    metal_codes = exceptions.get("metal_gng_prefixes", ["72", "73"])
    if w_type == "universal" and any(gng.startswith(m) for m in metal_codes if m):
        is_150_exception = True

    if not is_150_exception:
        coeff_val = ie_config.get("coefficient_value", 1.50)
        lbl_ie = ie_config.get("labels", {}).get(lang, "Import/Export Base") if isinstance(ie_config.get("labels"), dict) else "Import/Export Base"
        coeffs.append((lbl_ie, coeff_val))
        if "note_import_base_150" in ui_t:
            notes.append(ui_t["note_import_base_150"])

    # 2. Импортный коэффициент 1.04 (лес и металлы)
    imp_cfg = config.get("coefficients_updated_rules_2026", {}).get("import_metal_wood_1_04", {})
    imp_prefixes = imp_cfg.get("gng_prefixes", ["44", "72", "73"])
    if shipment_type_code == "import" and any(gng.startswith(p) for p in imp_prefixes if p):
        coeff_val = imp_cfg.get("coefficient_value", 1.04)
        lbl_imp = imp_cfg.get("labels", {}).get(lang, "Import Coeff") if isinstance(imp_cfg.get("labels"), dict) else "Import Coeff"
        coeffs.append((lbl_imp, coeff_val))
        if "note_timber_metal" in ui_t:
            notes.append(ui_t["note_timber_metal"])

    return coeffs, notes

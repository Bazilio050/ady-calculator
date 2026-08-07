import json
import os
import streamlit as st

# ---------------------------------------------------------
# 1. Константы и справочники погранпереходов
# ---------------------------------------------------------
BORDER_STATIONS = {
    "YALAMA": "Yalama (eksport)",
    "BEYUK KESIK": "Böyük Kəsik (eksport)",
    "BEYUK-KESIK": "Böyük Kəsik (eksport)",
    "ASTARA": "Astara (eks.aşır)",
    "CULFA": "Culfa (eksport)",
    "ALAT": "Ələt eksport",
    "SAMUR": "Samur (eksport)"
}

# ---------------------------------------------------------
# 2. Вспомогательные функции обработки данных
# ---------------------------------------------------------

def is_border_station(station_name: str) -> bool:
    """Проверяет, является ли станция пограничной."""
    name_clean = station_name.upper().replace("-EKSP.", "").replace("EKSP.", "").strip()
    return any(border in name_clean for border in BORDER_STATIONS.keys())

def format_station_display(st_from: str, st_to: str) -> tuple:
    """
    Если обе станции пограничные — добавляет суффикс -eksp. к обеим.
    """
    clean_from = st_from.strip()
    clean_to = st_to.strip()
    
    if is_border_station(clean_from) and is_border_station(clean_to):
        if not clean_from.lower().endswith("-eksp."):
            clean_from = f"{clean_from}-eksp."
        if not clean_to.lower().endswith("-eksp."):
            clean_to = f"{clean_to}-eksp."
            
    return clean_from, clean_to

def get_clean_station_name_for_lookup(station_name: str) -> str:
    """Приводит наименование станции к стандарту базы расстояний."""
    name_upper = station_name.upper().replace("-EKSP.", "").replace("EKSP.", "").strip()
    for border_key, official_name in BORDER_STATIONS.items():
        if border_key in name_upper:
            return official_name
    return station_name.strip()

def parse_gng_info(raw_gng, rules_config: dict) -> str:
    """Корректно обрабатывает 2-значные и 4/6-значные коды ГНГ."""
    if not raw_gng:
        return "Не указан"
    
    gng_str = str(raw_gng).strip()
    
    # Поиск по группам ГНГ в конфиге
    gng_groups = rules_config.get("gng_groups", {})
    if len(gng_str) == 2 and gng_str in gng_groups:
        return f"ГНГ {gng_str} - {gng_groups[gng_str]}"
    
    return f"ГНГ {gng_str}"

def calculate_billable_weight(fact_weight: float, gng_code: str, rules_config: dict) -> float:
    """Рассчитывает расчетную массу с учетом минимальных норм (в т.ч. ГНГ 72)."""
    gng_str = str(gng_code).strip()
    min_weights = rules_config.get("min_weights", {})
    
    # Проверка минимальной нормы для группы 72 (Черные металлы)
    if gng_str.startswith("72") or gng_str == "72":
        min_norm = min_weights.get("72", 60.0)
        return max(fact_weight, min_norm)
        
    default_min = min_weights.get("default", 10.0)
    return max(fact_weight, default_min)

# ---------------------------------------------------------
# 3. Логика коэффициентов
# ---------------------------------------------------------

def get_applicable_coefficients(cargo_info: dict, route_info: dict, rules_config: dict) -> list:
    """Рассчитывает список применимых коэффициентов на основе введенных данных."""
    applied_coeffs = []
    
    mode = cargo_info.get("mode")  # 'idxal', 'ixrac', 'tranzit'
    gng_code = str(cargo_info.get("gng_code", ""))
    wagon_type = cargo_info.get("wagon_type")  # 'universal', 'tank', 'bunker_semi', etc.
    table_number = cargo_info.get("table_number")
    is_oil_table6_col2 = cargo_info.get("is_oil_table6_col2", False)
    
    st_from_clean = get_clean_station_name_for_lookup(route_info.get("station_from", ""))
    st_to_clean = get_clean_station_name_for_lookup(route_info.get("station_to", ""))

    # 1. Проверка Коэффициента 1.50 (Импорт / Экспорт)
    if mode in ["idxal", "ixrac"]:
        is_exception = False
        
        # Таблица 3
        if table_number == 3:
            is_exception = True
            
        # Лес в универсальных вагонах (ГНГ 4403, 4404, 4407–4413)
        wood_codes = ["4403", "4404", "4407", "4408", "4409", "4410", "4411", "4412", "4413"]
        if wagon_type == "universal" and any(gng_code.startswith(code) for code in wood_codes):
            is_exception = True
            
        # Черные металлы в универсальных вагонах (ГНГ 72, 7301–7307)
        metal_exact = ["7301", "7302", "7303", "7304", "7305", "7306", "7307"]
        if wagon_type == "universal" and (gng_code.startswith("72") or any(gng_code.startswith(code) for code in metal_exact)):
            is_exception = True
            
        # Метанол в цистернах и бункерных полувагонах
        if gng_code.startswith("290511") and wagon_type in ["tank", "bunker_semi"]:
            is_exception = True
            
        # Нефть из Таблицы 6 (столбец 2) в цистернах
        if is_oil_table6_col2 and wagon_type == "tank":
            is_exception = True

        if not is_exception:
            applied_coeffs.append({"name": "Коэффициент 1,50 (Импорт/Экспорт)", "value": 1.50})

    # 2. Коэффициент 1.04 (Лес и металл на импорт)
    if mode == "idxal":
        if gng_code.startswith("44") or gng_code.startswith("72") or gng_code.startswith("73"):
            applied_coeffs.append({"name": "Коэффициент 1,04 (Лес и металл на импорт)", "value": 1.04})

    # 3. Коэффициент 1.20 (Транзит Алят – Беюк-Кесик)
    if mode == "tranzit":
        route_pair = {st_from_clean.upper(), st_to_clean.upper()}
        if "ƏLƏT EKSPORT" in route_pair and "BÖYÜK KƏSIK (EKSPORT)" in route_pair:
            applied_coeffs.append({"name": "Коэффициент 1,20 (Транзит Алят - Беюк-Кесик)", "value": 1.20})

    # 4. Коэффициент 1.20 (Нефтепродукты в цистернах)
    if mode in ["idxal", "tranzit"] and wagon_type == "tank":
        if cargo_info.get("is_oil_or_petroleum", False):
            applied_coeffs.append({"name": "Коэффициент 1,20 (Нефтепродукты в цистернах)", "value": 1.20})

    # 5. Коэффициент 1.20 (Рефрижераторы)
    if mode == "tranzit" and wagon_type in ["refrigerated_section", "refrigerated_container"]:
        applied_coeffs.append({"name": "Коэффициент 1,20 (Рефрижераторы)", "value": 1.20})

    return applied_coeffs

# ---------------------------------------------------------
# 4. Загрузка конфигурации и Streamlit UI
# ---------------------------------------------------------

@st.cache_data
def load_config():
    if os.path.exists("rules_config.json"):
        with open("rules_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    st.set_page_config(page_title="ADY Tarif Kalkulyatoru", page_icon="🚂", layout="wide")
    rules_config = load_config()

    st.title("🚂 ADY Tarif Kalkulyatoru")
    
    # Пример вывода результатов расчета
    st.subheader("1. Marşrut və daşıma şərtləri")

    # Входные параметры
    st_from_raw = "Yalama"
    st_to_raw = "Beyuk kasik"
    gng_raw = "72"
    fact_weight = 35.0
    wagon_type = "universal"
    mode = "idxal"

    # Применяем правильное форматирование названий станций
    disp_from, disp_to = format_station_display(st_from_raw, st_to_raw)
    route_display = f"{disp_from} - {disp_to}"

    # Парсим ГНГ и веса
    gng_display = parse_gng_info(gng_raw, rules_config)
    billable_weight = calculate_billable_weight(fact_weight, gng_raw, rules_config)

    # Отображение таблицы условий
    st.table([
        {"Parametr": "Marşrut", "Qiymət / Həcm": route_display},
        {"Parametr": "Daşıma növü", "Qiymət / Həcm": "İdxal daşınması" if mode == "idxal" else mode},
        {"Parametr": "Yük / Vəziyyət", "Qiymət / Həcm": f"{gng_display}, Universal vaqon (SPS)"},
        {"Parametr": "Faktiki / Hesablaşma çəkisi", "Qiymət / Həcm": f"{fact_weight} t / {billable_weight} t"},
    ])

if __name__ == "__main__":
    main()

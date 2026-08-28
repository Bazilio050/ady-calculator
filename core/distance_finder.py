# ==============================================================================
# МОДУЛЬ ПОИСКА РАССТОЯНИЙ И КОДОВ СТАНЦИЙ ADY (С ПОДДЕРЖКОЙ ЛОКАЛИЗАЦИИ)
# ==============================================================================
import os
import re
import sys

# Подключение функции локализации из data/stations_mapping.py
try:
    from data.stations_mapping import get_localized_station_name
except ImportError:
    try:
        from stations_mapping import get_localized_station_name
    except ImportError:
        def get_localized_station_name(name, lang="AZ"):
            return name

BORDER_NODES = {
    "Yalama (eksport)": ["yalama", "yalama-eksport", "yalama eksport", "ялама", "ялама-эксп", "ялама экспорт"],
    "Astara (eksport)": ["astara", "astara-eksport", "astara eksport", "астара", "астара-эксп", "астара экспорт"],
    "Böyük Kəsik (eksport)": [
        "boyuk kesik eksport", "böyük kəsik eksport", "boyuk kesik-eksport", 
        "беюк-кясик-эксп", "беюк кясик эксп", "беюк кясик экспорт", "беюк-кясик эксп"
    ],
    "Culfa (eksport)": ["culfa", "culfa-eksport", "джульфа", "джульфа-эксп"],
    "Ələt eksp / Bakı liman": [
        "alat", "ələt", "alat-eksport", "ələt-eksport", "алят", "алят-эксп",
        "aktau", "актау", "kurik", "kuryk", "курык", "курыт", "turk", "turkmen", "трк", "туркменбаши"
    ]
}

def normalize_name(text: str) -> str:
    """ Нормализует название станции: регистр, символы, латиница/кириллица, пробелы """
    if not text:
        return ""
    text = str(text).lower().strip()
    text = text.replace("*", "").replace("(", "").replace(")", "").replace("-", " ")
    
    replacements = {
        'ə': 'e', 'ö': 'o', 'ü': 'u', 'ç': 'c', 'ş': 's', 'ı': 'i', 'ğ': 'g',
        'ё': 'е', 'й': 'и'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    text = re.sub(r'[^a-zа-я0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_code(text: str) -> str:
    """Извлекает 6-значный код ЕСР из строки"""
    match = re.search(r'\b\d{6}\b', str(text))
    return match.group(0) if match else None

def resolve_alat_code(text: str) -> tuple:
    """ Применяет жесткие правила маппинга для Алята и морских направлений """
    norm = normalize_name(text)
    if "trk" in norm or "turk" in norm or "туркмен" in norm:
        return "Ələt eksport-Türk.", "548803"
    if "aktau" in norm or "актау" in norm:
        return "Ələt eksport Aktau", "549204"
    if "kurik" in norm or "kuryk" in norm or "курык" in norm or "курыт" in norm or "alat eksp" in norm or "alet eksp" in norm or "алят эксп" in norm:
        return "Ələt eksport Kurik", "553002"
    if "yeni" in norm or "новый" in norm:
        return "Ələt yeni", "548703"
    if "alat" in norm or "alet" in norm or "алят" in norm:
        return "Ələt", "548502"
    return None, None

def find_border_column(station_name: str) -> str:
    norm = normalize_name(station_name)
    for main_node, aliases in BORDER_NODES.items():
        for alias in aliases:
            if normalize_name(alias) in norm:
                return main_node
    return None

def parse_distances_file():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "Distances.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден!")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_idx = -1
    headers = []
    for idx, line in enumerate(lines):
        if "| Stansiyanın adı |" in line or "| Stansiyanın" in line:
            header_idx = idx
            headers = [h.strip().replace("*", "") for h in line.split("|")[1:-1]]
            break

    if header_idx == -1:
        raise ValueError("Не удалось распознать структуру таблицы в data/Distances.txt")

    stations_data = {}
    for line in lines[header_idx + 2:]:
        if not line.strip() or not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < len(headers):
            continue
            
        st_name = cols[0].replace("*", "").strip()
        st_code = cols[1].replace("*", "").strip()
        
        distances = {}
        for h_name, val in zip(headers[2:], cols[2:]):
            clean_h_name = h_name.replace("*", "").strip()
            try:
                distances[clean_h_name] = int(val.strip())
            except ValueError:
                distances[clean_h_name] = None
                
        stations_data[st_name] = {
            "code": st_code,
            "distances": distances
        }
    return stations_data

def match_station(target_name, stations_data):
    if not target_name:
        return None, None

    # 1. Проверка маппинга для Алята
    alat_name, alat_code = resolve_alat_code(target_name)
    if alat_code:
        for st_key, data in stations_data.items():
            if data.get("code") == alat_code:
                return st_key, data

    # 2. Поиск по 6-значному коду ЕСР
    target_code = extract_code(target_name)
    if target_code:
        for st_key, data in stations_data.items():
            if data.get("code") == target_code:
                return st_key, data

    # 3. Поиск по строгому точечному совпадению
    norm_target = normalize_name(target_name)
    for st_key, data in stations_data.items():
        if normalize_name(st_key) == norm_target:
            return st_key, data

    # 4. Частичный поиск по названию
    for st_key, data in stations_data.items():
        st_norm = normalize_name(st_key)
        if norm_target == st_norm or (len(norm_target) > 3 and norm_target in st_norm):
            return st_key, data

    return None, None

def get_route_info(from_station: str, to_station: str = None, lang: str = "AZ") -> dict:
    stations_data = parse_distances_file()

    # Защита: если первым аргументом пришел словарь nlu_res из app.py
    if isinstance(from_station, dict):
        if to_station is None and "lang" in from_station:
            lang = from_station.get("lang", lang)
        to_st_val = from_station.get("to_station", "")
        from_st_val = from_station.get("from_station", "")
        from_station = from_st_val
        to_station = to_st_val

    border_from = find_border_column(from_station)
    border_to = find_border_column(to_station)

    # УНИВЕРСАЛЬНАЯ ЛОГИКА: если найден погранпереход, ищем его напрямую в базе
    if border_from and border_from in stations_data:
        name_from, data_from = border_from, stations_data[border_from]
    else:
        name_from, data_from = match_station(from_station, stations_data)

    if border_to and border_to in stations_data:
        name_to, data_to = border_to, stations_data[border_to]
    else:
        name_to, data_to = match_station(to_station, stations_data)

    code_from = data_from["code"] if data_from else ""
    code_to = data_to["code"] if data_to else ""

    raw_from_name = name_from or from_station
    raw_to_name = name_to or to_station

    loc_from_name = get_localized_station_name(raw_from_name, lang=lang)
    loc_to_name = get_localized_station_name(raw_to_name, lang=lang)

    fmt_from = f"{loc_from_name}" + (f" ({code_from})" if code_from else "")
    fmt_to = f"{loc_to_name}" + (f" ({code_to})" if code_to else "")

    dist = None

    def get_dist_from_data(st_data, target_border_or_name):
        if not st_data or not target_border_or_name:
            return None
        target_norm = normalize_name(target_border_or_name)
        for h_key, d_val in st_data.get("distances", {}).items():
            h_norm = normalize_name(h_key)
            if target_norm in h_norm or h_norm in target_norm:
                return d_val
        return None

    if data_to:
        dist = get_dist_from_data(data_to, border_from or name_from)

    if dist is None and data_from:
        dist = get_dist_from_data(data_from, border_to or name_to)

    if dist is None:
        raise ValueError(f"Не удалось определить расстояние между '{from_station}' и '{to_station}'.")

    return {
        "distance_km": dist,
        "from_formatted": fmt_from,
        "to_formatted": fmt_to,
        "route_formatted": f"{fmt_from} – {fmt_to}",
        "raw_from_name": raw_from_name,
        "raw_to_name": raw_to_name
    }
    }

def get_route_distance(from_station: str, to_station: str) -> int:
    return get_route_info(from_station, to_station)["distance_km"]

get_distance_between_stations = get_route_distance

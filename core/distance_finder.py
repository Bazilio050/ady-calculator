# ==============================================================================
# МОДУЛЬ ПОИСКА РАССТОЯНИЙ И КОДОВ СТАНЦИЙ ADY
# ==============================================================================
import os
import re

try:
    from data.stations_mapping import get_localized_station_name
except ImportError:
    try:
        from stations_mapping import get_localized_station_name
    except ImportError:
        def get_localized_station_name(name, lang="AZ"):
            return name

def normalize_name(text: str) -> str:
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
    match = re.search(r'\b\d{6}\b', str(text))
    return match.group(0) if match else None

def resolve_alat_code(text: str) -> tuple:
    """Применяет жесткие правила маппинга для Алята и морских направлений"""
    norm = normalize_name(text)
    
    # 1. Если явно указан Туркменбаши
    if "trk" in norm or "turk" in norm or "туркмен" in norm:
        return "Ələt eksport-Türk.", "548803"
        
    # 2. Если явно указан Актау
    if "aktau" in norm or "актау" in norm:
        return "Ələt eksport Aktau", "549204"
        
    # 3. Если явно указан Курык
    if "kurik" in norm or "kuryk" in norm or "курык" in norm or "курыт" in norm:
        return "Ələt eksport Kurik", "553002"
        
    # 4. Если указан просто "Алят эксп / Алят экс" (без порта) — берем Курык/Баку Лиман как базовый погранпереход Алят
    if "eksp" in norm or "эксп" in norm or "экс" in norm:
        return "Ələt eksport", "553002"
        
    # 5. Новый порт
    if "yeni" in norm or "новый" in norm:
        return "Ələt yeni", "548703"
        
    # 6. Обычная внутренняя станция Алят
    if "alat" in norm or "alet" in norm or "алят" in norm:
        return "Ələt", "548502"
        
    return None, None

def detect_border_node(station_name: str) -> str:
    """Точно определяет ключ погранперехода в файле Distances.txt"""
    norm = normalize_name(station_name)
    if not norm:
        return None
    if "kesik" in norm or "kesik" in norm or "кясик" in norm or "касик" in norm:
        return "Böyük Kəsik (eksport)"
    if "yalama" in norm or "ялама" in norm:
        return "Yalama (eksport)"
    if "astara" in norm or "астара" in norm:
        return "Astara (eksport)"
    if "culfa" in norm or "джульфа" in norm:
        return "Culfa (eksport)"
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

    # 1. Проверка Алята
    alat_name, alat_code = resolve_alat_code(target_name)
    if alat_code:
        for st_key, data in stations_data.items():
            if data.get("code") == alat_code:
                return st_key, data

    # 2. Поиск по коду ЕСР
    target_code = extract_code(target_name)
    if target_code:
        for st_key, data in stations_data.items():
            if data.get("code") == target_code:
                return st_key, data

    # 3. Поиск по точному совпадению
    norm_target = normalize_name(target_name)
    for st_key, data in stations_data.items():
        if normalize_name(st_key) == norm_target:
            return st_key, data

    # 4. Частичный поиск
    for st_key, data in stations_data.items():
        st_norm = normalize_name(st_key)
        if norm_target == st_norm or (len(norm_target) > 3 and norm_target in st_norm):
            return st_key, data

    return None, None

def get_route_info(from_station: str, to_station: str = None, lang: str = "AZ") -> dict:
    stations_data = parse_distances_file()

    if isinstance(from_station, dict):
        if to_station is None and "lang" in from_station:
            lang = from_station.get("lang", lang)
        to_st_val = from_station.get("to_station", "")
        from_st_val = from_station.get("from_station", "")
        from_station = from_st_val
        to_station = to_st_val

    # ПРИОРИТЕТ 1: Проверяем, является ли станция погранпереходом
    border_from = detect_border_node(from_station)
    border_to = detect_border_node(to_station)

    if border_from and border_from in stations_data:
        name_from = border_from
        data_from = stations_data[border_from]
    else:
        name_from, data_from = match_station(from_station, stations_data)

    if border_to and border_to in stations_data:
        name_to = border_to
        data_to = stations_data[border_to]
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

def get_route_distance(from_station: str, to_station: str) -> int:
    return get_route_info(from_station, to_station)["distance_km"]

get_distance_between_stations = get_route_distance

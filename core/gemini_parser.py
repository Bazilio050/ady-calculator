# ==============================================================================
# МОДУЛЬ ПОИСКА РАССТОЯНИЙ И КОДОВ СТАНЦИЙ ADY
# ==============================================================================
import os
import re

BORDER_NODES = {
    "Yalama (eksport)": ["yalama", "yalama-eksport", "yalama eksport", "ялама", "ялама-эксп", "ялама экспорт"],
    "Astara (eksport)": ["astara", "astara-eksport", "astara eksport", "астара", "астара-эксп", "астара экспорт"],
    "Böyük Kəsik (eksport)": ["boyuk kesik", "böyük kəsik", "boyuk kesik-eksport", "беюк-кясик", "беюк кясик", "беюк-кясик-эксп", "беюк кясик экспорт"],
    "Culfa (eksport)": ["culfa", "culfa-eksport", "джульфа", "джульфа-эксп"],
    "Ələt eksp / Bakı liman": [
        "alat", "ələt", "alat-eksport", "ələt-eksport", "алят", "алят-эксп",
        "alat eksport aktau", "ələt eksport aktau", "алят актау",
        "alat eksport kurik", "ələt eksport kurik", "алят курык",
        "alat eksport-turk.", "ələt eksport-türk.", "алят туркменбаши", "алят туркменистан",
        "baki ticarat liman", "bakı ticarət limanı", "бакинский порт", "порт алят"
    ]
}

def normalize_name(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    replacements = {
        'ə': 'e', 'ö': 'o', 'ü': 'u', 'ç': 'c', 'ş': 's', 'ı': 'i', 'ğ': 'g',
        'ё': 'е', 'й': 'и'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def find_border_column(station_name: str) -> str:
    norm = normalize_name(station_name)
    for main_node, aliases in BORDER_NODES.items():
        for alias in aliases:
            if normalize_name(alias) in norm:
                return main_node
    return None

def parse_distances_file():
    file_path = os.path.join("data", "Distances.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError("Файл data/Distances.txt не найден!")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_idx = -1
    headers = []
    for idx, line in enumerate(lines):
        if "| Stansiyanın adı |" in line or "| Stansiyanın" in line:
            header_idx = idx
            headers = [h.strip() for h in line.split("|")[1:-1]]
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
            
        st_name = cols[0].replace("**", "").strip()
        st_code = cols[1].strip()
        
        distances = {}
        for h_name, val in zip(headers[2:], cols[2:]):
            try:
                distances[h_name] = int(val.strip())
            except ValueError:
                distances[h_name] = None
                
        stations_data[st_name] = {
            "code": st_code,
            "distances": distances
        }
    return stations_data

def match_station(target_name, stations_data):
    norm_target = normalize_name(target_name)
    
    # 1. Приоритет: СТРОГОЕ ТОЧНОЕ совпадение
    for st_key, data in stations_data.items():
        if normalize_name(st_key) == norm_target:
            return st_key, data
            
    # 2. Вторично: частичное совпадение
    for st_key, data in stations_data.items():
        if norm_target in normalize_name(st_key):
            return st_key, data
            
    return None, None

def get_route_info(from_station: str, to_station: str) -> dict:
    stations_data = parse_distances_file()

    border_from = find_border_column(from_station)
    border_to = find_border_column(to_station)

    name_from, data_from = match_station(from_station, stations_data)
    name_to, data_to = match_station(to_station, stations_data)

    if not data_from and border_from:
        name_from, data_from = match_station(border_from, stations_data)
    if not data_to and border_to:
        name_to, data_to = match_station(border_to, stations_data)

    code_from = data_from["code"] if data_from else ""
    code_to = data_to["code"] if data_to else ""

    fmt_from = f"{name_from or from_station}" + (f" ({code_from})" if code_from else "")
    fmt_to = f"{name_to or to_station}" + (f" ({code_to})" if code_to else "")

    dist = None

    if border_from and border_to:
        _, data_border_to = match_station(border_to, stations_data)
        if data_border_to and border_from in data_border_to["distances"]:
            dist = data_border_to["distances"][border_from]

    if dist is None and border_to and data_from:
        if border_to in data_from["distances"]:
            dist = data_from["distances"][border_to]

    if dist is None and border_from and data_to:
        if border_from in data_to["distances"]:
            dist = data_to["distances"][border_from]

    if dist is None:
        raise ValueError(f"Не удалось вычесть расстояние между '{from_station}' и '{to_station}'.")

    return {
        "distance_km": dist,
        "from_formatted": fmt_from,
        "to_formatted": fmt_to,
        "route_formatted": f"{fmt_from} – {fmt_to}"
    }

def get_route_distance(from_station: str, to_station: str) -> int:
    return get_route_info(from_station, to_station)["distance_km"]

get_distance_between_stations = get_route_distance

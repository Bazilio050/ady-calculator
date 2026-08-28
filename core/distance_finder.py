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

def resolve_exact_station_key(input_text: str, stations_data: dict) -> tuple:
    """Простая и надежная привязка ввода пользователя к строгим ключам из Distances.txt"""
    norm = normalize_name(input_text)
    
    # 1. Алят и его порты
    if "alat" in norm or "alet" in norm or "алят" in norm:
        if "trk" in norm or "turk" in norm or "туркмен" in norm:
            key = "Ələt eksport-Türk."
        elif "aktau" in norm or "актау" in norm:
            key = "Ələt eksport Aktau"
        elif "yeni" in norm or "новый" in norm:
            key = "Ələt yeni"
        elif "eksp" in norm or "эксп" in norm or "экс" in norm or "kurik" in norm or "курык" in norm:
            key = "Ələt eksport Kurik"
        else:
            key = "Ələt"
        return key, stations_data.get(key)

    # 2. Беюк Кясик
    if "kesik" in norm or "кясик" in norm or "касик" in norm:
        key = "Böyük Kəsik (eksport)" if ("eksp" in norm or "экс" in norm or "эксп" in norm) else "Böyük Kəsik"
        return key, stations_data.get(key)

    # 3. Ялама
    if "yalama" in norm or "ялама" in norm:
        key = "Yalama (eksport)"
        return key, stations_data.get(key)

    # 4. Астара
    if "astara" in norm or "астара" in norm:
        key = "Astara (eksport)" if ("eksp" in norm or "экс" in norm or "эксп" in norm) else "Astara"
        return key, stations_data.get(key)

    # 5. Джульфа
    if "culfa" in norm or "джульфа" in norm:
        key = "Culfa (eksport)" if ("eksp" in norm or "экс" in norm or "эксп" in norm) else "Culfa"
        return key, stations_data.get(key)

    # 6. Поиск по коду ЕСР или обычному совпадению
    code = extract_code(input_text)
    if code:
        for st_key, data in stations_data.items():
            if data.get("code") == code:
                return st_key, data

    for st_key, data in stations_data.items():
        if normalize_name(st_key) == norm:
            return st_key, data

    for st_key, data in stations_data.items():
        if len(norm) > 3 and norm in normalize_name(st_key):
            return st_key, data

    return None, None

def get_route_info(from_station: str, to_station: str = None, lang: str = "AZ") -> dict:
    stations_data = parse_distances_file()

    raw_from_input = from_station
    raw_to_input = to_station

    if isinstance(from_station, dict):
        if to_station is None and "lang" in from_station:
            lang = from_station.get("lang", lang)
        raw_to_input = from_station.get("to_station", "")
        raw_from_input = from_station.get("from_station", "")

    # Определение точных ключей станций
    key_from, data_from = resolve_exact_station_key(raw_from_input, stations_data)
    key_to, data_to = resolve_exact_station_key(raw_to_input, stations_data)

    if not data_from:
        raise ValueError(f"Станция отправления '{raw_from_input}' не найдена.")
    if not data_to:
        raise ValueError(f"Станция назначения '{raw_to_input}' не найдена.")

    code_from = data_from.get("code", "")
    code_to = data_to.get("code", "")

    # Поиск километража в матрице
    dist = None
    target_norm_from = normalize_name(key_from)
    for h_key, d_val in data_to.get("distances", {}).items():
        if target_norm_from in normalize_name(h_key) or normalize_name(h_key) in target_norm_from:
            dist = d_val
            break

    if dist is None:
        target_norm_to = normalize_name(key_to)
        for h_key, d_val in data_from.get("distances", {}).items():
            if target_norm_to in normalize_name(h_key) or normalize_name(h_key) in target_norm_to:
                dist = d_val
                break

    if dist is None:
        raise ValueError(f"Не удалось определить расстояние между '{raw_from_input}' и '{raw_to_input}'.")

    # Форматирование названий под выгрузку
    loc_from_name = get_localized_station_name(key_from, lang=lang)
    loc_to_name = get_localized_station_name(key_to, lang=lang)

    fmt_from = f"{loc_from_name}" + (f" ({code_from})" if code_from else "")
    fmt_to = f"{loc_to_name}" + (f" ({code_to})" if code_to else "")

    return {
        "distance_km": dist,
        "from_formatted": fmt_from,
        "to_formatted": fmt_to,
        "route_formatted": f"{fmt_from} – {fmt_to}",
        "raw_from_name": key_from,
        "raw_to_name": key_to
    }

def get_route_distance(from_station: str, to_station: str) -> int:
    return get_route_info(from_station, to_station)["distance_km"]

get_distance_between_stations = get_route_distance

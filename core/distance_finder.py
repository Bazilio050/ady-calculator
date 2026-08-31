# core/distance_finder.py
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

def resolve_exact_station_key(input_text: str, stations_data: dict, is_transit: bool = False) -> tuple:
    norm = normalize_name(input_text)
    
    # Флаг экспорта/транзита или наличия ключевых слов стыка
    has_exp_kw = any(k in norm for k in ["eksp", "экс", "эксп", "export", "ashir", "ашир"])
    use_export_profile = is_transit or has_exp_kw

    # 1. Ялама (Любое направление)
    if "yalama" in norm or "ялама" in norm:
        key = "Yalama (eksport)" if use_export_profile else "Yalama"
        if key not in stations_data and "Yalama (eksport)" in stations_data:
            key = "Yalama (eksport)"
        return key, stations_data.get(key)

    # 2. Беюк Кясик (Любое направление)
    if any(k in norm for k in ["kesik", "кясик", "касик"]):
        key = "Böyük Kəsik (eksport)" if use_export_profile else "Böyük Kəsik"
        if key not in stations_data and "Böyük Kəsik (eksport)" in stations_data:
            key = "Böyük Kəsik (eksport)"
        return key, stations_data.get(key)

    # 3. Астара (Любое направление)
    if "astara" in norm or "астара" in norm:
        key = "Astara (eks.aşır)" if use_export_profile else "Astara"
        if key not in stations_data and "Astara (eks.aşır)" in stations_data:
            key = "Astara (eks.aşır)"
        return key, stations_data.get(key)

    # 4. Алят (Экспортные направления Порта и Перехода)
    if any(k in norm for k in ["alat", "elet", "алят", "aktau", "актау", "kurik", "курык"]):
        if "yeni" in norm or "новый" in norm:
            key = "Ələt yeni"
        elif use_export_profile or any(k in norm for k in ["liman", "port"]):
            key = "Ələt eksport Kurik"
        else:
            key = "Ələt"
        return key, stations_data.get(key)

    # 5. Прямой поиск по совпадению названий или кодам
    for st_key, data in stations_data.items():
        if normalize_name(st_key) == norm:
            return st_key, data

    code = extract_code(input_text)
    if code:
        for st_key, data in stations_data.items():
            if data.get("code") == code:
                return st_key, data

    for st_key, data in stations_data.items():
        if len(norm) > 3 and norm in normalize_name(st_key):
            return st_key, data

    return None, None

def lookup_dist(source_data, target_key):
    if not source_data or "distances" not in source_data:
        return None
    
    t_norm = normalize_name(target_key)
    distances_dict = source_data.get("distances", {})
    
    # 1. Поиск для Алята (колонки Ələt eksp / Bakı liman)
    if any(k in t_norm for k in ["alat", "elet", "алят", "aktau", "актау", "kurik", "курык"]):
        for h_key, d_val in distances_dict.items():
            h_norm = normalize_name(h_key)
            if ("elet" in h_norm or "alat" in h_norm) and ("eksp" in h_norm or "liman" in h_norm or "eksport" in h_norm):
                if d_val is not None:
                    return d_val

    # 2. Поиск для Беюк Кясик (колонка Boyuk Kesik eksport)
    if "kesik" in t_norm or "кясик" in t_norm or "касик" in t_norm:
        for h_key, d_val in distances_dict.items():
            h_norm = normalize_name(h_key)
            if ("kesik" in h_norm or "кясик" in h_norm) and ("eksp" in h_norm or "eksport" in h_norm):
                if d_val is not None:
                    return d_val

    # 3. Точный поиск совпадений по заголовку
    for h_key, d_val in distances_dict.items():
        h_norm = normalize_name(h_key)
        if t_norm == h_norm or t_norm in h_norm or h_norm in t_norm:
            if d_val is not None:
                return d_val

    return None

def get_route_info(from_station: str, to_station: str = None, lang: str = "AZ", shipment_type: str = None) -> dict:
    stations_data = parse_distances_file()

    raw_from_input = from_station
    raw_to_input = to_station

    if isinstance(from_station, dict):
        if to_station is None and "lang" in from_station:
            lang = from_station.get("lang", lang)
        raw_to_input = from_station.get("to_station", "")
        raw_from_input = from_station.get("from_station", "")

    is_transit = shipment_type in ["transit", "export"]

    key_from, data_from = resolve_exact_station_key(raw_from_input, stations_data, is_transit=is_transit)
    key_to, data_to = resolve_exact_station_key(raw_to_input, stations_data, is_transit=is_transit)

    dist = None
    if data_from:
        dist = lookup_dist(data_from, key_to)
    if dist is None and data_to:
        dist = lookup_dist(data_to, key_from)

    if dist is None:
        raise ValueError(f"Не удалось определить расстояние между '{raw_from_input}' и '{raw_to_input}'.")

    code_from = data_from.get("code", "") if data_from else ""
    code_to = data_to.get("code", "") if data_to else ""

    loc_from_name = get_localized_station_name(key_from, lang=lang)
    loc_to_name = get_localized_station_name(key_to, lang=lang)

    def build_station_label(loc_name, code, key_name, raw_input):
        raw_norm = normalize_name(raw_input)
        if "kurik" in raw_norm or "курык" in raw_norm:
            return "Ələt-eksp.Kurik"
        elif "aktau" in raw_norm or "актау" in raw_norm:
            return "Ələt-eksp.Aktau"
        elif "trk" in raw_norm or "turk" in raw_norm or "туркмен" in raw_norm:
            return "Ələt-eksp.Türk."
        elif "alat" in raw_norm or "elet" in raw_norm or "алят" in raw_norm:
            if "eksp" in raw_norm or "export" in raw_norm or "эксп" in raw_norm or is_transit:
                return "Ələt-eksp."
        elif "astara" in raw_norm or "астара" in raw_norm:
            if is_transit or "eksp" in raw_norm or "эксп" in raw_norm:
                return "Astara (eks.aşır)"
        elif "kesik" in raw_norm or "кясик" in raw_norm:
            if is_transit or "eksp" in raw_norm or "эксп" in raw_norm:
                return "Böyük Kəsik-eksp."
        if not code:
            return loc_name
        return f"{loc_name} ({code})"

    fmt_from = build_station_label(loc_from_name, code_from, key_from, raw_from_input)
    fmt_to = build_station_label(loc_to_name, code_to, key_to, raw_to_input)

    return {
        "distance_km": dist,
        "from_formatted": fmt_from,
        "to_formatted": fmt_to,
        "route_formatted": f"{fmt_from} – {fmt_to}",
        "raw_from_name": key_from,
        "raw_to_name": key_to,
        "from_code": code_from,
        "to_code": code_to
    }

def get_route_distance(from_station: str, to_station: str) -> int:
    return get_route_info(from_station, to_station)["distance_km"]

get_distance_between_stations = get_route_distance

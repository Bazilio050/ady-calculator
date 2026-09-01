# core/distance_finder.py
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from data.stations_mapping import get_localized_station_name

def normalize_name(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower().strip()
    replacements = {'ə': 'e', 'ö': 'o', 'ü': 'u', 'ç': 'c', 'ş': 's', 'ı': 'i', 'ğ': 'g', 'ё': 'е', 'й': 'и'}
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'[^a-zа-я0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_distances_file():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "Distances.txt")
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_idx = -1
    headers = []
    for idx, line in enumerate(lines):
        if "| Stansiyanın adı |" in line or "| Stansiyanın" in line:
            header_idx = idx
            headers = [h.strip().replace("*", "") for h in line.split("|")[1:-1]]
            break

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

    return headers[2:], stations_data

def get_border_column_header(station_text: str, headers: list) -> str:
    norm = normalize_name(station_text)
    if "yalama" in norm or "ялама" in norm:
        return "Yalama (eksport)"
    elif "astara" in norm or "астара" in norm:
        return "Astara (eks.aşır)"
    elif "kesik" in norm or "кясик" in norm or "касик" in norm:
        return "Böyük Kəsik (eksport)"
    elif "culfa" in norm or "джульфа" in norm:
        return "Culfa (eksport)"
    elif any(k in norm for k in ["alat", "elet", "алят", "aktau", "актау", "kurik", "курык", "liman", "trk", "трк", "turkm", "туркм"]):
        return "Ələt eksp / Bakı liman"
    return None

def resolve_target_row_key(station_text: str, stations_data: dict, is_origin: bool = True, is_transit: bool = False, shipment_type: str = None) -> str:
    norm = normalize_name(station_text)

    # Определяем, нужен ли экспортный стык:
    # 1. При транзите — всегда стык
    # 2. При импорте — стык только для 1-й станции (вход)
    # 3. При экспорте — стык только для 2-й станции (выход)
    use_border_joint = (
        (shipment_type == "transit") or
        (shipment_type == "import" and is_origin) or
        (shipment_type == "export" and not is_origin) or
        (is_transit and shipment_type is None)
    )

    # 1. Порт-паром на Туркменбаши / ТРК
    if any(k in norm for k in ["trk", "трк", "turkmenbasy", "туркменбаши", "туркменбашы", "turkm", "туркм"]):
        return "Ələt eksport-Türk."

    # 2. Порты Актау и Курык
    if "kurik" in norm or "курык" in norm:
        return "Ələt eksport Kurik"
    if "aktau" in norm or "актау" in norm:
        return "Ələt eksport Aktau"

    # 3. Алят
    if any(k in norm for k in ["alat", "elet", "алят"]):
        if use_border_joint or any(k in norm for k in ["eksp", "эксп", "eksport", "экспорт"]):
            return "Ələt eksport Kurik"
        return "Ələt"

    # 4. Пограничные стыковые пункты
    if any(k in norm for k in ["kesik", "кясик", "касик"]):
        return "Böyük Kəsik (eksport)" if use_border_joint else "Böyük Kəsik"
    
    if "astara" in norm or "астара" in norm:
        return "Astara (eks.aşır)" if use_border_joint else "Astara"

    if "yalama" in norm or "ялама" in norm:
        return "Yalama (eksport)" if use_border_joint else "Yalama"

    if "culfa" in norm or "джульфа" in norm:
        return "Culfa (eksport)" if use_border_joint else "Culfa"

    # 5. Внутренние станции
    if any(k in norm for k in ["absheron", "abseron", "абшерон", "апшерон"]):
        return "Abşeron"

    # Поиск по базе
    for st_key in stations_data.keys():
        if normalize_name(st_key) == norm:
            return st_key

    for st_key in stations_data.keys():
        if norm in normalize_name(st_key):
            return st_key

    return None

def get_route_info(from_station: str, to_station: str = None, lang: str = "AZ", shipment_type: str = None) -> dict:
    headers, stations_data = parse_distances_file()

    raw_from = from_station.get("from_station", "") if isinstance(from_station, dict) else from_station
    raw_to = from_station.get("to_station", "") if isinstance(from_station, dict) else to_station

    current_lang = (lang or "AZ").upper()
    
    if not shipment_type:
        shipment_type = "transit"

    is_transit_mode = (shipment_type == "transit")

    from_col = get_border_column_header(raw_from, headers)
    to_row_key = resolve_target_row_key(raw_to, stations_data, is_transit=is_transit_mode, shipment_type=shipment_type)

    from_row_key = resolve_target_row_key(raw_from, stations_data, is_transit=is_transit_mode, shipment_type=shipment_type)
    to_col = get_border_column_header(raw_to, headers)

    dist = None
    if from_col and to_row_key in stations_data:
        dist = stations_data[to_row_key]["distances"].get(from_col)

    if dist is None and to_col and from_row_key in stations_data:
        dist = stations_data[from_row_key]["distances"].get(to_col)

    if dist is None:
        raise ValueError(f"Не удалось определить расстояние между '{raw_from}' и '{raw_to}'.")

    def get_station_code(key_name):
        if not key_name:
            return ""
        if key_name in stations_data and stations_data[key_name].get("code"):
            return stations_data[key_name]["code"]
        clean_base = key_name.replace("(eksport)", "").replace("(eks.aşır)", "").strip()
        for st_k, st_v in stations_data.items():
            if normalize_name(st_k) == normalize_name(clean_base):
                return st_v.get("code", "")
        return ""

    code_from = get_station_code(from_row_key)
    code_to = get_station_code(to_row_key)

    def build_label(
        raw_in: str,
        fallback_key: str,
        code: str,
        shipment_type: str,
        is_origin: bool,  # True если это станция отправления, False если назначения
        current_lang: str,
    ) -> str:
        norm = normalize_name(raw_in)
        norm_fallback = normalize_name(fallback_key)
        hide_code = False
        base_key = fallback_key

        # Определяем, должен ли данный пункт быть экспортным стыком (-эксп.)
        # 1. При транзите — обе станции стыки
        # 2. При импорте — только первая станция (вход в страну)
        # 3. При экспорте — только вторая станция (выход из страны)
        is_border_joint = (
            (shipment_type == "transit") or
            (shipment_type == "import" and is_origin) or
            (shipment_type == "export" and not is_origin)
        )

        # 1. Порты и терминалы Алята (КОД СКРЫВАЕТСЯ)
        if any(k in norm or k in norm_fallback for k in ["kurik", "курык"]):
            base_key = "Ələt eksport Kurik"
            hide_code = True
        elif any(k in norm or k in norm_fallback for k in ["aktau", "актау"]):
            base_key = "Ələt eksport Aktau"
            hide_code = True
        elif any(k in norm or k in norm_fallback for k in ["trk", "трк", "turk", "туркмен"]):
            base_key = "Ələt eksport-Türk."
            hide_code = True
        elif any(k in norm or k in norm_fallback for k in ["alat", "elet", "алят"]):
            if is_border_joint or "eksp" in norm or "эксп" in norm:
                base_key = "Ələt eksport"
                hide_code = True
            else:
                base_key = "Ələt"

        # 2. Пограничные пункты (стык или чистая станция)
        elif any(k in norm or k in norm_fallback for k in ["kesik", "кясик", "касик"]):
            base_key = "Böyük Kəsik (eksport)" if is_border_joint else "Böyük Kəsik"
            hide_code = False
        elif any(k in norm or k in norm_fallback for k in ["astara", "астара"]):
            base_key = "Astara (eksport)" if is_border_joint else "Astara"
            hide_code = False
        elif any(k in norm or k in norm_fallback for k in ["yalama", "ялама"]):
            base_key = "Yalama (eksport)" if is_border_joint else "Yalama"
            hide_code = False
        elif any(k in norm or k in norm_fallback for k in ["culfa", "джульфа"]):
            base_key = "Culfa (eksport)" if is_border_joint else "Culfa"
            hide_code = False

        localized_name = get_localized_station_name(base_key, lang=current_lang)

        if code and not hide_code:
            return f"{localized_name} ({code})"
        return localized_name

    fmt_from = build_label(
        raw_from,
        from_row_key or raw_from,
        code_from,
        shipment_type,
        is_origin=True,
        current_lang=current_lang,
    )
    fmt_to = build_label(
        raw_to, 
        to_row_key or raw_to, 
        code_to, 
        shipment_type, 
        is_origin=False,
        current_lang=current_lang,
    )

    return {
        "distance_km": dist,
        "from_formatted": fmt_from,
        "to_formatted": fmt_to,
        "route_formatted": f"{fmt_from} – {fmt_to}",
        "raw_from_name": raw_from,
        "raw_to_name": to_row_key,
        "from_code": code_from,
        "to_code": code_to,
    }

def get_route_distance(from_station: str, to_station: str) -> int:
    return get_route_info(from_station, to_station)["distance_km"]

get_distance_between_stations = get_route_distance

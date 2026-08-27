# ==============================================================================
# МОДУЛЬ ПОИСКА РАССТОЯНИЙ И КОДОВ СТАНЦИЙ ADY
# ==============================================================================
import os
import re

BORDER_NODES = {
    "Yalama (eksport)": ["yalama", "yalama-eksport", "yalama eksport", "ялама", "ялама-эксп", "ялама экспорт"],
    "Astara (eksport)": ["astara", "astara-eksport", "astara eksport", "астара", "астара-эксп", "астара экспорт"],
    "Böyük Kəsik (eksport)": ["boyuk kesik", "böyük kəsik", "boyuk kesik-eksport", "беюк-кясик", "беюк кясик", "беюк-кясик-эксп"],
    "Culfa (eksport)": ["culfa", "culfa-eksport", "джульфа", "джульфа-эксп"],
    "Ələt eksp / Bakı liman": [
        "alat", "ələt", "alat-eksport", "ələt-eksport", "алят", "алят-эксп",
        "aktau", "актау", "kurik", "kuryk", "курык", "курыт", "turk", "turkmen", "трк", "туркменбаши"
    ]
}

def normalize_name(text: str) -> str:
    """ Нормализует название станции: регистр, символы **, азербайджанская кириллица/латиница, пробелы """
    if not text:
        return ""
    text = text.lower().strip()
    text = text.replace("*", "").replace("(", "").replace(")", "").replace("-", " ")
    
    replacements = {
        'ə': 'e', 'ö': 'o', 'ü': 'u', 'ç': 'c', 'ş': 's', 'ı': 'i', 'ğ': 'g',
        'ё': 'е', 'й': 'и', 'я': 'a'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_code(text: str) -> str:
    match = re.search(r'\b\d{6}\b', str(text))
    return match.group(0) if match else None

def resolve_alat_code(text: str) -> tuple:
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
            if normalize_name(alias) == norm or (len(norm) >= 4 and normalize_name(alias) in norm):
                return main_node
    return None

def parse_distances_file():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "Distances.txt")
    if not os.path.exists(file_path):
        file_path = os.path.join(base_dir, "Distances.txt")
    if not os.path.exists(file_path):
        file_path = "Distances.txt"

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
        raise ValueError("Не удалось распознать структуру таблицы в Distances.txt")

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

    # 1. Алят
    alat_name, alat_code = resolve_alat_code(target_name)
    if alat_code:
        for st_key, data in stations_data.items():
            if data.get("code") == alat_code:
                return st_key, data

    # 2. Поиск по коду
    target_code = extract_code(target_name)
    if target_code:
        for st_key, data in stations_data.items():
            if data.get("code") == target_code:
                return st_key, data

    # 3. Точный поиск
    norm_target = normalize_name(target_name)
    for st_key, data in stations_data.items():
        if normalize_name(st_key) == norm_target:
            return st_key, data

    # 4. Частичное совпадение
    for st_key, data in stations_data.items():
        st_norm = normalize_name(st_key)
        if norm_target == st_norm or (len(norm_target) > 3 and norm_target in st_norm):
            return st_key, data

    return None, None

def format_display_name(raw_input: str, matched_name: str, code: str, lang: str = "AZ") -> str:
    """ Форматирует вывод станции на экран по правилам ADY """
    norm_raw = normalize_name(raw_input)
    norm_matched = normalize_name(matched_name)

    # 1. Проверяем наличие конкретного порта строго по отдельным словам (\b)
    has_specific_port = bool(re.search(r'\b(kurik|kuryk|курык|курыт|aktau|актау|trk|turk|туркмен)\b', norm_raw))

    # 2. Проверяем Алят и любой корень слова (eks, eksp, exp, экс, эксп, экспорт)
    is_alat = any(a in norm_raw for a in ["alat", "alet", "алят"])
    has_exp_root = bool(re.search(r'\b(eks|eksp|exp|экс|эксп|экспорт)', norm_raw)) or "eksp" in norm_matched

    # Если обобщенный Алят-эксп (без указания точного порта) — выводим без кода
    if is_alat and has_exp_root and not has_specific_port:
        return "Ələt-eksp."

    # 3. Правило для пограничных станций (Ялама, Астара, Беюк Кясик, Джульфа)
    suf = "-eksp." if lang.upper() in ["AZ", "RU"] else "-exp."
    
    clean_name = matched_name.replace("(eksport)", "").replace("eksport", "").replace("eks.aşır", "").strip()
    
    if "yalama" in norm_matched:
        clean_name = "Yalama"
    elif "astara" in norm_matched:
        clean_name = "Astara"
    elif "boyuk" in norm_matched or "kesik" in norm_matched:
        clean_name = "Böyük Kəsik"
    elif "culfa" in norm_matched:
        clean_name = "Culfa"

    is_border = any(b_key in norm_matched for b_key in ["yalama", "astara", "boyuk", "kesik", "culfa"])
    
    if is_border:
        display_name = f"{clean_name}{suf}"
    else:
        display_name = clean_name

    if code:
        return f"{display_name} ({code})"
    return display_name

def get_route_info(from_station, to_station=None, lang="AZ") -> dict:
    if isinstance(from_station, dict):
        nlu_data = from_station
        from_st = nlu_data.get("from_station", "")
        to_st = nlu_data.get("to_station", "")
        manual_dist = nlu_data.get("manual_distance_km")
    else:
        from_st = str(from_station)
        to_st = str(to_station)
        manual_dist = None

    stations_data = parse_distances_file()

    border_from = find_border_column(from_st)
    border_to = find_border_column(to_st)

    search_from = border_from if border_from else from_st
    name_from, data_from = match_station(search_from, stations_data)
    name_to, data_to = match_station(to_st, stations_data)

    code_from = data_from["code"] if data_from else ""
    code_to = data_to["code"] if data_to else ""

    # Передаем исходный текст (из nlu_data или аргумента), чтобы корректно распознать "экс" / "эксп"
    raw_text_from = nlu_data.get("raw_text", from_st) if isinstance(from_station, dict) else from_st
    raw_text_to = nlu_data.get("raw_text", to_st) if isinstance(from_station, dict) else to_st

    fmt_from = format_display_name(raw_text_from, name_from or from_st, code_from, lang=lang)
    fmt_to = format_display_name(raw_text_to, name_to or to_st, code_to, lang=lang)
    dist = None

    if manual_dist is not None and float(manual_dist or 0) > 0:
        dist = int(float(manual_dist))

    if dist is None and border_from and data_to:
        for h_key, d_val in data_to["distances"].items():
            if normalize_name(h_key) == normalize_name(border_from):
                dist = d_val
                break

    if dist is None and border_to and data_from:
        for h_key, d_val in data_from["distances"].items():
            if normalize_name(h_key) == normalize_name(border_to):
                dist = d_val
                break

    if dist is None:
        dist = 0

    return {
        "distance_km": dist,
        "from_formatted": fmt_from,
        "to_formatted": fmt_to,
        "route_formatted": f"{fmt_from} – {fmt_to}",
        "route_display": f"{fmt_from} – {fmt_to}"
    }

get_route_summary = get_route_info

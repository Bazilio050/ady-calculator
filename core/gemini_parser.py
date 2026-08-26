# ==============================================================================
# МОДУЛЬ ЛОКАЛЬНОГО ПОИСКА СТАНЦИЙ И РАССЧЕТА РАССТОЯНИЙ ADY
# ==============================================================================
import json
import os
import re
from typing import Dict, Optional, Tuple
from difflib import get_close_matches

try:
    from rapidfuzz import process, fuzz
    HAS_RAPIDFUZZ = True
except ImportError:  # <--- ЗДЕСЬ БЫЛА ОПЕЧАТКА (было ImporterError)
    HAS_RAPIDFUZZ = False

# ==============================================================================
# СЛОВАРИ ПОГРАНИЧНЫХ СТЫКОВ И ПЕРЕВОДОВ НАЗВАНИЙ
# ==============================================================================

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

# Список пограничных стыков для определения правила применения приписки -эксп.
BORDER_STATION_NAMES = {"Yalama", "Böyük Kəsik", "Astara", "Culfa", "Ələt-eksp."}

# Переводы названий станций на русский и английский языки
STATION_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "Yalama": {"az": "Yalama", "ru": "Ялама", "en": "Yalama"},
    "Böyük Kəsik": {"az": "Böyük Kəsik", "ru": "Беюк Кясик", "en": "Beyuk Kasik"},
    "İmişli": {"az": "İmişli", "ru": "Имишли", "en": "Imishli"},
    "Abşeron": {"az": "Abşeron", "ru": "Апшерон", "en": "Absheron"},
    "Salyan": {"az": "Salyan", "ru": "Сальяны", "en": "Salyan"},
    "Bakı yük": {"az": "Bakı yük", "ru": "Баку гл.", "en": "Baku freight"},
    "Gəncə": {"az": "Gəncə", "ru": "Гянджа", "en": "Ganja"},
    "Astara": {"az": "Astara", "ru": "Астара", "en": "Astara"},
    "Culfa": {"az": "Culfa", "ru": "Джульфа", "en": "Julfa"},
    "Ələt": {"az": "Ələt", "ru": "Алят", "en": "Alat"},
    "Ələt yeni": {"az": "Ələt yeni", "ru": "Алят новый", "en": "Alat yeni"}
}

# Приписки пограничных станций по языкам
EXP_SUFFIX = {
    "az": "-eksp.",
    "ru": "-эксп.",
    "en": "-exp."
}

def load_aliases() -> dict:
    """ Загружает словарь псевдонимов и русских названий из data/aliases.json """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    aliases_path = os.path.join(base_dir, "data", "aliases.json")
    if os.path.exists(aliases_path):
        try:
            with open(aliases_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def normalize_name(text: str) -> str:
    """ Нормализует название станции для поиска """
    if not text:
        return ""
    text = text.lower().strip()
    text = text.replace("*", "").replace("(", "").replace(")", "").replace("-", " ")
    
    replacements = {
        'ə': 'e', 'ö': 'o', 'ü': 'u', 'ç': 'c', 'ş': 's', 'ı': 'i', 'ğ': 'g',
        'ё': 'е', 'й': 'и'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_code(text: str) -> Optional[str]:
    """ Извлекает 6-значный код ЕСР из строки, если он присутствует """
    match = re.search(r'\b\d{6}\b', str(text))
    return match.group(0) if match else None

def resolve_alat_code(text: str) -> Tuple[Optional[str], Optional[str]]:
    """ Специальные правила маппинга для Алята и морских терминалов """
    norm = normalize_name(text)
    if "trk" in norm or "turk" in norm or "туркмен" in norm:
        return "Ələt eksport-Türk.", "548803"
    if "aktau" in norm or "актау" in norm:
        return "Ələt eksport Aktau", "549204"
    if "kurik" in norm or "kuryk" in norm or "курык" in norm or "курыт" in norm:
        return "Ələt eksport Kurik", "553002"
    if "yeni" in norm or "новый" in norm:
        return "Ələt yeni", "548703"
    if "alat" in norm or "alet" in norm or "алят" in norm:
        return "Ələt", "548502"
    return None, None

def find_border_column(station_name: str) -> Optional[str]:
    """ Находит пограничный столбец матрицы расстояний """
    if not station_name:
        return None
    clean_name = re.sub(r'\(\d{6}\)|\b\d{6}\b', '', str(station_name)).strip()
    norm = normalize_name(clean_name)
    
    for main_node, aliases in BORDER_NODES.items():
        for alias in aliases:
            norm_alias = normalize_name(alias)
            if norm_alias == norm or (len(norm_alias) > 3 and norm_alias in norm):
                return main_node
    return None

def parse_distances_file() -> dict:
    """ Парсит файл тарифных расстояний data/Distances.txt """
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

def match_station(target_name: str, stations_data: dict) -> Tuple[Optional[str], Optional[dict]]:
    """ Сопоставляет название станции из запроса со справочником ADY """
    if not target_name:
        return None, None

    # 1. Проверка через словари псевдонимов (aliases.json)
    aliases = load_aliases()
    norm_input = normalize_name(target_name)
    if norm_input in aliases:
        target_name = aliases[norm_input]

    # 2. Проверка маппинга для Алята (Курык, Актау, ТРК)
    alat_name, alat_code = resolve_alat_code(target_name)
    if alat_code:
        for st_key, data in stations_data.items():
            if data.get("code") == alat_code:
                return st_key, data

    # 3. Поиск по 6-значному коду ЕСР (если передавался)
    target_code = extract_code(target_name)
    if target_code:
        for st_key, data in stations_data.items():
            if data.get("code") == target_code:
                return st_key, data

    # 4. Точное и частичное соответствие по имени
    norm_target = normalize_name(target_name)
    for st_key, data in stations_data.items():
        if normalize_name(st_key) == norm_target:
            return st_key, data

    for st_key, data in stations_data.items():
        st_norm = normalize_name(st_key)
        if norm_target == st_norm or (len(norm_target) > 3 and norm_target in st_norm):
            return st_key, data

    # 5. Нечёткий (fuzzy) поиск через RapidFuzz или Difflib
    station_names = list(stations_data.keys())
    
    if HAS_RAPIDFUZZ:
        best_match = process.extractOne(target_name, station_names, scorer=fuzz.WRatio)
        if best_match and best_match[1] >= 70:
            matched_key = best_match[0]
            return matched_key, stations_data[matched_key]
    else:
        matches = get_close_matches(target_name, station_names, n=1, cutoff=0.6)
        if matches:
            matched_key = matches[0]
            return matched_key, stations_data[matched_key]

    return None, None

# ==============================================================================
# ФУНКЦИИ КРАСИВОГО ФОРМАТИРОВАНИЯ ВЫВОДА СТАНЦИЙ (PYTHON)
# ==============================================================================

def format_station_display(st_name: str, 
                           st_code: str, 
                           parsed_data: dict, 
                           is_from: bool, 
                           lang: str = "ru") -> str:
    """
    Формирует отображение станции на выбранном языке (az/ru/en) 
    с учетом приписок -эксп., кодов ЕСР и правил скрытия для Алята.
    """
    lang = lang.lower()
    suf = EXP_SUFFIX.get(lang, "-эксп.")
    shipment_type = parsed_data.get("shipment_type", "")
    alat_terminal = parsed_data.get("alat_terminal")
    is_exp_flag = parsed_data.get("is_exp_flag", False)
    
    # --------------------------------------------------------------------------
    # 1. СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ СТАНЦИИ АЛЯТ
    # --------------------------------------------------------------------------
    if "Ələt" in st_name or "Alat" in st_name or "Алят" in st_name:
        # 1.1 Запрос с конкретным паромным терминалом (Курык / Актау / Туркменбаши)
        if alat_terminal == "Kurik":
            name = "Ələt-eksp. Kurik" if lang == "az" else "Алят-эксп. Курык" if lang == "ru" else "Alat-exp. Kuryk"
            return f"{name} ({st_code or '553002'})"
            
        elif alat_terminal == "Aktau":
            name = "Ələt-eksp. Aktau" if lang == "az" else "Алят-эксп. Актау" if lang == "ru" else "Alat-exp. Aktau"
            return f"{name} ({st_code or '549204'})"
            
        elif alat_terminal == "Turk":
            name = "Ələt-eksp. Türk." if lang == "az" else "Алят-эксп. Туркм." if lang == "ru" else "Alat-exp. Turk."
            return f"{name} ({st_code or '548803'})"
            
        # 1.2 Обобщенный Алят-эксп (код ЕСР СТРОГО СКРЫВАЕТСЯ по нашему правилу)
        elif is_exp_flag or "eksp" in st_name.lower():
            name = f"Ələt{suf}" if lang == "az" else f"Алят{suf}" if lang == "ru" else f"Alat{suf}"
            return name  # Возвращаем БЕЗ кода в скобках!

        # 1.3 Алят новый (Ələt yeni)
        elif "yeni" in st_name.lower() or "новый" in st_name.lower():
            name = "Ələt yeni" if lang == "az" else "Алят новый" if lang == "ru" else "Alat yeni"
            return f"{name} ({st_code or '548703'})"

    # --------------------------------------------------------------------------
    # 2. ЛОГИКА ДЛЯ ВСЕХ ОСТАЛЬНЫХ СТАНЦИЙ
    # --------------------------------------------------------------------------
    # Определяем, требуется ли приписка -эксп.
    should_have_exp = False
    if shipment_type == "tranzit":
        should_have_exp = True
    elif shipment_type in ["ixrac", "export"] and not is_from:
        should_have_exp = True
    elif shipment_type in ["idxal", "import"] and is_from:
        should_have_exp = True

    # Получаем перевод наименования
    translations = STATION_TRANSLATIONS.get(st_name, {"az": st_name, "ru": st_name, "en": st_name})
    base_name = translations.get(lang, st_name)
    code_str = f" ({st_code})" if st_code else ""

    if should_have_exp:
        return f"{base_name}{suf}{code_str}"
    else:
        return f"{base_name}{code_str}"

# ==============================================================================
# ОСНОВНАЯ ФУНКЦИЯ РАСЧЕТА МАРШРУТА
# ==============================================================================

def get_route_info(parsed_data: dict, lang: str = "ru") -> dict:
    """
    Принимает отпарсенные данные из gemini_parser.py и вычисляет расстояние
    по матрице Distances.txt, формируя отформатированные строки станций.
    """
    from_station = parsed_data.get("from_station", "")
    to_station = parsed_data.get("to_station", "")

    stations_data = parse_distances_file()

    border_from = find_border_column(from_station)
    border_to = find_border_column(to_station)

    name_from, data_from = match_station(from_station, stations_data)
    name_to, data_to = match_station(to_station, stations_data)

    code_from = data_from["code"] if data_from else ""
    code_to = data_to["code"] if data_to else ""

    # Форматируем красивый вывод на выбранном языке
    fmt_from = format_station_display(name_from or from_station, code_from, parsed_data, is_from=True, lang=lang)
    fmt_to = format_station_display(name_to or to_station, code_to, parsed_data, is_from=False, lang=lang)

    dist = None

    # Поиск расстояния по матрице
    if data_to and data_to.get("distances"):
        for h_key, d_val in data_to["distances"].items():
            if d_val is not None and d_val > 0:
                norm_h = normalize_name(h_key)
                if (name_from and normalize_name(name_from) in norm_h) or \
                   (border_from and normalize_name(border_from) in norm_h) or \
                   ("yalama" in norm_h if border_from == "Yalama (eksport)" else False):
                    dist = d_val
                    break

    if dist is None and data_from and data_from.get("distances"):
        for h_key, d_val in data_from["distances"].items():
            if d_val is not None and d_val > 0:
                norm_h = normalize_name(h_key)
                if (name_to and normalize_name(name_to) in norm_h) or \
                   (border_to and normalize_name(border_to) in norm_h) or \
                   ("boyuk" in norm_h if border_to == "Böyük Kəsik (eksport)" else False):
                    dist = d_val
                    break

    if dist is None and border_from and border_to:
        for st_key, st_data in stations_data.items():
            st_norm = normalize_name(st_key)
            if "boyuk" in st_norm or "kesik" in st_norm:
                for h_key, d_val in st_data["distances"].items():
                    if "yalama" in normalize_name(h_key):
                        if d_val is not None and d_val > 0:
                            dist = d_val
                            break
            if dist:
                break

    if dist is None or dist == 0:
        raise ValueError(f"Не удалось определить расстояние между '{from_station}' и '{to_station}'.")

    return {
        "distance_km": dist,
        "from_formatted": fmt_from,
        "to_formatted": fmt_to,
        "route_formatted": f"{fmt_from} – {fmt_to}"
    }

import os
import re
from datetime import datetime

# ==============================================================================
# UTILS-01: Константы и пограничные узлы ADY
# ==============================================================================
BORDER_COLUMN_MAP = {
    "547508": 3,  # Yalama (eksport)
    "545006": 3,  # Yalama
    "558701": 4,  # Böyük Kəsik (eksport)
    "558631": 4,  # Böyük Kəsik
    "554503": 5,  # Astara (eks.aşır)
    "554500": 5,  # Astara
    "550108": 6,  # Culfa (eksport)
    "550100": 6,  # Culfa
    "548803": 7,  # Ələt (eksport)
    "548502": 7,  # Ələt baş
    "553002": 7,  # Ələt-yeni (паром)
    "549204": 7,  # Ələt Aktau
}

BORDER_STATIONS_MAP = {
    "yalama": {"local": "545006", "border": "547508"},
    "boyuk kesik": {"local": "558631", "border": "558701"},
    "böyük kəsik": {"local": "558631", "border": "558701"},
    "беюк кясик": {"local": "558631", "border": "558701"},
    "беюккясик": {"local": "558631", "border": "558701"},
    "astara": {"local": "554500", "border": "554503"},
    "астара": {"local": "554500", "border": "554503"},
    "culfa": {"local": "550100", "border": "550108"},
    "джульфа": {"local": "550100", "border": "550108"},
    "alet": {"local": "548502", "border": "553002"},
    "elet": {"local": "548502", "border": "553002"},
    "алят": {"local": "548502", "border": "553002"},
}

_DISTANCES_CACHE = None

# ==============================================================================
# UTILS-02: Поиск расстояний и кэширование
# ==============================================================================
def _load_distances_cache():
    global _DISTANCES_CACHE
    if _DISTANCES_CACHE is not None:
        return _DISTANCES_CACHE

    _DISTANCES_CACHE = []
    filepath = "Distances.txt"
    if not os.path.exists(filepath):
        possible = [f for f in os.listdir(".") if "dist" in f.lower() or "məsafə" in f.lower() or "masafe" in f.lower()]
        if possible:
            filepath = possible[0]

    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    parts = [p.strip() for p in line.split("\t")]
                    if len(parts) >= 3:
                        _DISTANCES_CACHE.append(parts)
        except Exception as e:
            print(f"Error loading distances: {e}")

    return _DISTANCES_CACHE

def get_distance_by_esr(esr_from: str, esr_to: str) -> int:
    """Точный поиск километража по закешированной таблице Distances.txt."""
    if not esr_from or not esr_to:
        return None

    c_from = re.sub(r'\D', '', str(esr_from))
    c_to = re.sub(r'\D', '', str(esr_to))

    if not c_from or not c_to:
        return None

    if c_from == c_to:
        return 0

    col_idx = BORDER_COLUMN_MAP.get(c_to)
    target_row_esr = c_from

    if col_idx is None:
        col_idx = BORDER_COLUMN_MAP.get(c_from)
        target_row_esr = c_to

    if col_idx is None:
        return None

    cache = _load_distances_cache()
    for parts in cache:
        if len(parts) <= col_idx:
            continue

        row_esr_code = re.sub(r'\D', '', parts[2])

        if row_esr_code and (row_esr_code in target_row_esr or target_row_esr in row_esr_code):
            val_str = re.sub(r'\D', '', parts[col_idx])
            if val_str and val_str.isdigit():
                return int(val_str)

    return None

def get_calculation_distance(actual_dist_km: int, shipment_mode: str = "import") -> int:
    """Возвращает расчетное расстояние с учетом тарифных норм (min 101/151 км)."""
    if actual_dist_km is None or actual_dist_km <= 0:
        return 0

    calc_dist = actual_dist_km
    mode = str(shipment_mode or "").lower()

    if "import" in mode or "idxal" in mode or "импорт" in mode:
        calc_dist = max(actual_dist_km, 151)
    elif "export" in mode or "ixrac" in mode or "экспорт" in mode:
        calc_dist = max(actual_dist_km, 101)

    return calc_dist

# ==============================================================================
# UTILS-03: Определение ЕСР-кодов станций
# ==============================================================================
def resolve_complex_station_code(raw_input: str) -> str:
    """Универсальный локальный резолвер сложных внутренних станций ADY."""
    text = str(raw_input or "").lower()

    if any(r in text for r in ["тагиев", "tagiyev", "тагив", "г.тагиев", "h.z.", "г. тагиев", "g.tagiyev", "g tagiyev"]):
        if any(m in text for m in ["сорт", "sort", "чешид", "cesid", "ceşid"]):
            return "546901"
        return "546302"

    if any(r in text for r in ["баку порт", "baki liman", "bakı liman", "торговый порт", "ticarət liman"]):
        if any(m in text for m in ["перевал", "ашир", "aşır", "ашыр"]):
            return "547209"
        if any(m in text for m in ["эксп", "exp", "ixrac", "экспорт"]):
            return "547406"
        return "547302"

    if any(r in text for r in ["баку юк", "bakı yük", "баку груз", "баку товар"]):
        if any(m in text for m in ["терминал", "terminal"]):
            return "547603"
        return "547105"

    if any(r in text for r in ["sanqacal", "сангачал", "sanqaçal", "сангачалы"]):
        if any(m in text for m in ["терминал", "terminal", "ашир", "aşır", "перевал"]):
            return "548606"
        return "548305"

    if any(r in text for r in ["qaradag", "гарадаг", "qaradağ", "карадаг"]):
        if any(m in text for m in ["терминал", "terminal"]):
            return "549702"
        return "548201"

    if any(r in text for r in ["сумгаит", "sumqayit", "sumqayıt"]):
        if any(m in text for m in ["главный", "баш", "bas", "baş"]):
            return "546001"
        if any(m in text for m in ["пасс", "шехер", "seher", "город"]):
            return "546209"
        return "546105"

    if any(r in text for r in ["mingecevir", "мингечевир", "mingəçevir"]):
        if any(m in text for m in ["город", "şəhər", "шехер", "seher"]):
            return "555807"
        return "555703"

    if any(r in text for r in ["гянджа", "ganja", "gəncə"]):
        if any(m in text for m in ["грузовая", "юк", "yük"]):
            return "558108"
        return "558004"

    if any(r in text for r in ["баладжары", "bilacari", "biləcəri", "баледжары"]):
        if any(m in text for m in ["сорт", "sort", "чешид", "cesid"]):
            return "545107"
        return "545200"

    return None

def get_border_esr(station_name: str, position: str = "from", shipment_mode: str = "import") -> str:
    """Определение пограничного ЕСР с поддержкой позиционных параметров."""
    st_clean = str(station_name or "").lower().strip()
    pos = "from" if str(position).lower() in ["from", "origin"] else "to"
    mode = str(shipment_mode or "").lower()

    for key, val in BORDER_STATIONS_MAP.items():
        if key in st_clean:
            if "transit" in mode or "tranzit" in mode:
                return val["border"]
            elif ("import" in mode or "idxal" in mode) and pos == "from":
                return val["border"]
            elif ("export" in mode or "ixrac" in mode) and pos == "to":
                return val["border"]
            else:
                return val["border"] if "eksp" in st_clean or "эксп" in st_clean else val["local"]
    return None

def resolve_esr_by_station_name(station_name: str, user_input_raw: str = "", position: str = "from", shipment_mode: str = "import", *args, **kwargs) -> str:
    """Универсальная точка входа для получения ЕСР-кода."""
    if isinstance(user_input_raw, str) and user_input_raw in ["from", "to", "origin", "dest"]:
        shipment_mode = position if position not in ["from", "to", "origin", "dest"] else shipment_mode
        position = user_input_raw
        user_input_raw = ""

    st_clean = str(station_name or "").strip()

    border_esr = get_border_esr(st_clean, position=position, shipment_mode=shipment_mode)
    if border_esr:
        return border_esr

    complex_esr = resolve_complex_station_code(f"{st_clean} {user_input_raw}")
    if complex_esr:
        return complex_esr

    cache = _load_distances_cache()
    st_lower = st_clean.lower()
    for parts in cache:
        if len(parts) >= 3:
            name = parts[1].lower()
            code = parts[2]
            if st_lower in name or name in st_lower:
                return code

    return None

def is_border_esr(esr_code: str) -> bool:
    return str(esr_code) in BORDER_COLUMN_MAP

def format_station_display_name(st_name: str, esr_code: str, lang: str = "AZ") -> str:
    if is_border_esr(esr_code):
        suf = "-эксп." if lang == "RU" else "-eksp."
        return f"{st_name}{suf}"
    return st_name

# ==============================================================================
# UTILS-04: Вспомогательные расчётные функции
# ==============================================================================
def get_weight_column_index(weight_tons: float) -> int:
    """Возвращает индекс колонки для Таблиц 3 и 4."""
    w = float(weight_tons or 0)
    if w <= 12: return 1
    elif w <= 16: return 2
    elif w <= 23: return 3
    elif w <= 26: return 4
    elif w <= 31: return 5
    elif w <= 36: return 6
    elif w <= 40: return 7
    elif w <= 46: return 8
    elif w <= 51: return 9
    elif w <= 55: return 10
    else: return 11

def extract_gng_digits(gng_code: str) -> str:
    return re.sub(r'\D', '', str(gng_code or ""))

def get_min_weight_by_gng(gng_code: str, act_weight: float) -> float:
    gng = str(gng_code or "").strip()
    if gng.startswith("44") or gng.startswith("4707"):
        return max(45.0, act_weight)
    if gng.startswith("72") or gng.startswith("1001"):
        return max(60.0, act_weight)
    return max(10.0, act_weight)

def get_transporter_min_weight(axles: int, act_weight: float) -> float:
    if axles <= 4:
        return max(10.0, act_weight)
    elif axles <= 8:
        return max(15.0, act_weight)
    return max(20.0, act_weight)

def is_long_platform_scep(user_input_raw: str, wagon_type: str) -> bool:
    inp = str(user_input_raw or "").lower()
    return "19m" in inp or "19 м" in inp or "19m" in str(wagon_type or "").lower()

def should_apply_150_coeff(*args, **kwargs) -> bool:
    try:
        mode = str(args[0] if len(args) > 0 else kwargs.get('shipment_mode', '')).lower()
        tbl = float(args[1] if len(args) > 1 else kwargs.get('table_num', 0))
        park = str(args[4] if len(args) > 4 else kwargs.get('park_type', '')).upper()

        if mode in ["import", "export", "idxal", "ixrac"]:
            if tbl in [5, 6]:
                return True
            if park == "SPS" and tbl not in [3, 4]:
                return True
        return False
    except Exception:
        return False

def get_global_coefficients(shipment_type_code: str, gng_code: str, origin_esr: str, dest_esr: str, lang: str = "AZ") -> tuple:
    coeffs = []
    notes = []
    gng = str(gng_code or "")
    if shipment_type_code in ["import", "idxal"] and (gng.startswith("44") or gng.startswith("72")):
        lbl = "Meşə/Metal 1.04" if lang == "AZ" else ("Лес/Металл 1.04" if lang == "RU" else "Wood/Metal 1.04")
        coeffs.append((lbl, 1.04))
    return coeffs, notes

def get_exchange_rate_for_date(target_dt: datetime) -> tuple:
    return 0.79, "01.07.2026 - 30.09.2026"

def parse_date_from_string(date_str: str) -> datetime:
    return datetime.now()

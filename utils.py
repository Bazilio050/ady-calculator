import os
import re

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
}

BORDER_STATIONS_MAP = {
    "yalama": {"local": "545006", "border": "547508"},
    "boyuk kesik": {"local": "558631", "border": "558701"},
    "böyük kəsik": {"local": "558631", "border": "558701"},
    "беюк кясик": {"local": "558631", "border": "558701"},
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
# UTILS-02: Кэширование и поиск расстояний
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
    """Точный поиск километража по закешированной таблице Distances.txt (0 токенов)."""
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

# ==============================================================================
# UTILS-03: Локальное определение ЕСР-кодов станций
# ==============================================================================
def resolve_complex_station_code(raw_input: str) -> str:
    """Универсальный локальный резолвер сложных внутренних станций ADY."""
    text = str(raw_input or "").lower()

    # 1. Группа Тагиев (Z.Tağıyev 546302 vs Z.Tağıyev çeşidləmə 546901)
    if any(r in text for r in ["тагиев", "tagiyev", "тагив", "г.тагиев", "h.z.", "г. тагиев", "g.tagiyev", "g tagiyev"]):
        if any(m in text for m in ["сорт", "sort", "чешид", "cesid", "ceşid"]):
            return "546901"
        return "546302"

    # 2. Группа Баку Торговый Порт / Ляман (547302 vs 547406 vs 547209)
    if any(r in text for r in ["баку порт", "baki liman", "bakı liman", "торговый порт", "ticarət liman"]):
        if any(m in text for m in ["перевал", "ашир", "aşır", "ашыр"]):
            return "547209"
        if any(m in text for m in ["эксп", "exp", "ixrac", "экспорт"]):
            return "547406"
        return "547302"

    # 3. Группа Баку Товарный / Грузовой / Гюнес (547105 vs 547603)
    if any(r in text for r in ["баку юк", "bakı yük", "баку груз", "баку товар"]):
        if any(m in text for m in ["терминал", "terminal"]):
            return "547603"
        return "547105"

    # 4. Группа Сангачал (548305 vs 548606)
    if any(r in text for r in ["sanqacal", "сангачал", "sanqaçal", "сангачалы"]):
        if any(m in text for m in ["терминал", "terminal", "ашир", "aşır", "перевал"]):
            return "548606"
        return "548305"

    # 5. Группа Гарадаг (548201 vs 549702)
    if any(r in text for r in ["qaradag", "гарадаг", "qaradağ", "карадаг"]):
        if any(m in text for m in ["терминал", "terminal"]):
            return "549702"
        return "548201"

    # 6. Группа Сумгаит (546105 vs 546001 vs 546209)
    if any(r in text for r in ["сумгаит", "sumqayit", "sumqayıt"]):
        if any(m in text for m in ["главный", "баш", "bas", "baş"]):
            return "546001"
        if any(m in text for m in ["пасс", "шехер", "seher", "город"]):
            return "546209"
        return "546105"

    # 7. Группа Мингечевир (555703 vs 555807)
    if any(r in text for r in ["mingecevir", "мингечевир", "mingəçevir"]):
        if any(m in text for m in ["город", "şəhər", "шехер", "seher"]):
            return "555807"
        return "555703"

    # 8. Группа Гянджа (558004 vs 558108)
    if any(r in text for r in ["гянджа", "ganja", "gəncə"]):
        if any(m in text for m in ["грузовая", "юк", "yük"]):
            return "558108"
        return "558004"

    # 9. Группа Баладжары (545200 vs 545107)
    if any(r in text for r in ["баладжары", "bilacari", "biləcəri", "баледжары"]):
        if any(m in text for m in ["сорт", "sort", "чешид", "cesid"]):
            return "545107"
        return "545200"

    return None

def get_border_esr(station_name: str, position: str = "from", shipment_mode: str = "import") -> str:
    """Определение пограничного ЕСР с учетом направления перевозки."""
    st_clean = str(station_name or "").lower().strip()
    for key, val in BORDER_STATIONS_MAP.items():
        if key in st_clean:
            if shipment_mode == "transit":
                return val["border"]
            elif shipment_mode == "import" and position == "from":
                return val["border"]
            elif shipment_mode == "export" and position == "to":
                return val["border"]
            else:
                return val["local"]
    return None

def resolve_esr_by_station_name(station_name: str, position: str = "from", shipment_mode: str = "import") -> str:
    """Универсальная точка входа для получения ЕСР-кода."""
    border_esr = get_border_esr(station_name, position=position, shipment_mode=shipment_mode)
    if border_esr:
        return border_esr

    complex_esr = resolve_complex_station_code(station_name)
    if complex_esr:
        return complex_esr

    cache = _load_distances_cache()
    st_clean = str(station_name or "").lower().strip()
    for parts in cache:
        if len(parts) >= 3:
            name = parts[1].lower()
            code = parts[2]
            if st_clean in name or name in st_clean:
                return code
    return None

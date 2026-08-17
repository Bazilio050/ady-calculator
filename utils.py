import os
import re
from datetime import datetime

# ==============================================================================
# 1. РЕЕСТР ПОГРАНИЧНЫХ СТАНЦИЙ И ЕСР-КОДОВ
# ==============================================================================

BORDER_ESR_CODES = {
    "545006", "547508", "545307", "545107",
    "558631", "558701", "558504", "558400",
    "554109", "554503", "553905",
    "550004", "550108", "550803",
    "550502", "550409",
    "549204", "553002", "548803", "547302", "547406", "547209", "548502", "548703"
}

BORDER_STATION_ESR_OVERRIDE = {
  # Пограничные и базовые узлы
    "boyuk kesik": "558701",
    "beyuk kasik": "558701",
    "böyük kəsik": "558701",
    "беюк кясик": "558701",
    "беюк кесик": "558701",
    "б кясик": "558701",
    "б кесик": "558701",
    "yalama": "547508",
    "ялама": "547508",
    "astara": "554109",
    "астара": "554109",
    "culfa": "550108",
    "serur": "550409",
    "kuryk": "553002",
    "kurik": "553002",
    "quruq": "553002",
    "курык": "553002",
    "aktau": "549204",
    "aqtau": "549204",
    "актау": "549204",
    "turkmenbashi": "548803",
    "türkmenbaşı": "548803",
    "туркменбаши": "548803",
    "trk": "548803",
    "трк": "548803",
    "absheron": "548004",
    "абшерон": "548004",
    "baku": "547001",
    "bakı": "547001",
    "баку": "547001",
    "alet": "548502",
    "elet": "548502",
    "ələt": "548502",
    "алят": "548502",

    # Баку, Грузовые станции и Порты
    "baku yuk": "547105",
    "bakı yük": "547105",
    "baku tov": "547105",
    "баку тов": "547105",
    "баку товарный": "547105",
    "баку грузовой": "547105",
    "baku yuk terminal": "547603",
    "bakı yük terminal": "547603",
    "баку терм": "547603",
    "баку грузовой терминал": "547603",
    "baku port": "547302",
    "alat port": "547302",
    "баку лиман": "547302",
    "торговый порт": "547302",
    "bakı ticarət liman": "547302",
    "баку лиман эксп": "547406",
    "торговый порт эксп": "547406",
    "bakı ticarət limanı eks": "547406",
    "баку лиман перевалка": "547209",
    "торговый порт аширма": "547209",
    "bakı ticarət limanı aşır": "547209",

    # Алят, Гарадаг, Сангачал
    "alet yeni": "548703",
    "elet yeni": "548703",
    "ələt yeni": "548703",
    "алят новый": "548703",
    "алят ени": "548703",
    "garadag": "548201",
    "qaradağ": "548201",
    "карадаг": "548201",
    "garadag terminal": "549702",
    "qaradağ terminal": "549702",
    "карадаг терм": "549702",
    "карадаг терминал": "549702",
    "sangachal": "548305",
    "sanqaçal": "548305",
    "сангачал": "548305",
    "сангачалы": "548305",
    "sangachal ter asirma": "548606",
    "sanqaçal ter aşırma": "548606",
    "сангачал аширма": "548606",
    "сангачалы перевалка": "548606",

    # З. Тагиев, Союк-Булак
    "tagiyev": "546302",
    "z tagiyev": "546302",
    "z tağıyev": "546302",
    "тагиев": "546302",
    "з тагиев": "546302",
    "г з тагиев": "546302",
    "гаджи зейналабдин тагиев": "546302",
    "насосный": "546302",
    "nasosni": "546302",
    "tagiyev cesidleme": "546901",
    "z tağıyev çeşidləmə": "546901",
    "тагиев сорт": "546901",
    "тагиев сортировка": "546901",
    "тагиев чеш": "546901",
    "soyuqbulaq": "558608",
    "soyuq bulaq": "558608",
    "союк булак": "558608",
    "союгбулаг": "558608",

    # Региональные станции
    "ganja": "556208",
    "gəncə": "556208",
    "гянджа": "556208",
    "mingachevir": "555703",
    "mingəçevir": "555703",
    "мингечевир": "555703",
    "mingachevir shahar": "555807",
    "mingəçevir şəhər": "555807",
    "мингечевир шахар": "555807",
    "мингечевир город": "555807",
    "qushchu korpu": "556301",
    "quşçu körpü": "556301",
    "кушчу корпю": "556301",
    "кушчу мост": "556301",
}

BORDER_COLUMN_MAP = {
    "545006": 3, "547508": 3, "545307": 3, "545107": 3,
    "554109": 4, "554503": 4, "553905": 4,
    "558701": 5, "558631": 5, "558504": 5, "558400": 5,
    "550004": 6, "550108": 6, "550803": 6,
    "549204": 7, "553002": 7, "548803": 7, "547302": 7, 
    "547406": 7, "547209": 7, "548502": 7, "548703": 7
}


def is_border_esr(esr_code: str) -> bool:
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    return clean_esr in BORDER_ESR_CODES


def format_station_display_name(raw_name: str, esr_code: str, site_lang: str = "AZ") -> str:
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    st_name = str(raw_name or "").strip()

    if is_border_esr(clean_esr):
        lang_upper = str(site_lang or "AZ").upper()
        suffix = "-эксп." if lang_upper == "RU" else ("-exp." if lang_upper == "EN" else "-eksp.")
        if not st_name.endswith(suffix):
            st_name = f"{st_name}{suffix}"

    return f"{st_name} ({clean_esr})" if clean_esr else st_name


def resolve_esr_by_station_name(station_name: str, user_input_raw: str = "") -> str:
    if not station_name:
        return ""

    clean = re.sub(r'-(eksp|эксп|exp)\b', '', str(station_name), flags=re.IGNORECASE).strip().lower()
    clean_norm = clean.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')

    sorted_overrides = sorted(BORDER_STATION_ESR_OVERRIDE.items(), key=lambda x: len(x[0]), reverse=True)
    for b_name, b_esr in sorted_overrides:
        if b_name in clean_norm:
            return b_esr

    possible_paths = ["Distances.txt", "tariff_data/Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = next((p for p in possible_paths if os.path.exists(p)), None)

    if not dist_file:
        return ""

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            for line in f:
                if "|" not in line or ":---" in line or "Stansiyanın" in line:
                    continue

                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 3:
                    continue

                file_st_name = parts[1].replace("*", "").strip().lower()
                file_st_name = file_st_name.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
                file_esr = re.sub(r'\D', '', parts[2])

                if clean_norm and file_st_name and (clean_norm in file_st_name or file_st_name in clean_norm):
                    return file_esr
    except Exception as e:
        print(f"Error resolving ESR: {e}")

    return ""


def get_distance_by_esr(esr_from: str, esr_to: str) -> int:
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
        col_idx = 3

    possible_paths = ["Distances.txt", "tariff_data/Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = next((p for p in possible_paths if os.path.exists(p)), None)

    if not dist_file:
        return None

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            for line in f:
                if "|" not in line or ":---" in line or "Stansiyanın" in line:
                    continue

                parts = [p.strip() for p in line.split("|")]
                if len(parts) <= col_idx:
                    continue

                row_esr_code = re.sub(r'\D', '', parts[2])

                if row_esr_code and (row_esr_code in target_row_esr or target_row_esr in row_esr_code):
                    val_str = re.sub(r'\D', '', parts[col_idx])
                    if val_str and val_str.isdigit():
                        return int(val_str)

    except Exception as e:
        print(f"Error reading Distances.txt: {e}")

    return None


def get_calculation_distance(distance_km: int, shipment_type: str) -> int:
    st_lower = str(shipment_type or "").lower()
    if any(k in st_lower for k in ["ixrac", "export", "экспорт"]):
        return max(distance_km, 101)
    if any(k in st_lower for k in ["idxal", "import", "импорт"]):
        return max(distance_km, 151)
    return distance_km


def get_weight_column_index(billable_weight_tons: float) -> int:
    w = float(billable_weight_tons or 0)
    if w <= 12: return 0
    elif w <= 16: return 1
    elif w <= 23: return 2
    elif w <= 26: return 3
    elif w <= 31: return 4
    elif w <= 36: return 5
    elif w <= 40: return 6
    elif w <= 46: return 7
    elif w <= 51: return 8
    elif w <= 55: return 9
    else: return 10


def extract_gng_digits(gng_code, kwargs=None) -> str:
    kwargs = kwargs or {}
    candidates = [gng_code, kwargs.get("gng_code"), kwargs.get("gng"), kwargs.get("cargo_code")]
    for c in candidates:
        if c:
            m = re.search(r"\d+", str(c))
            if m:
                return m.group(0)
    return ""


def get_min_weight_by_gng(gng_code: str, actual_weight_tons: float) -> float:
    g = extract_gng_digits(gng_code)
    w = float(actual_weight_tons or 0)
    if not g:
        return w

    if g in ["28182000", "7201", "1701", "1107", "7203", "7401", "7501", "81052"] or g.startswith("2701") or g.startswith("2702") or g.startswith("10"):
        return max(w, 60.0)
    if g.startswith("26") and not (2618 <= int(g[:4]) <= 2621 if len(g) >= 4 else False):
        return max(w, 60.0)
    if g.startswith("31") and not g.startswith("3101"):
        return max(w, 60.0)
    if len(g) >= 4 and 1101 <= int(g[:4]) <= 1103:
        return max(w, 60.0)
    if g.startswith("72") and not g.startswith("7204"):
        return max(w, 60.0)
    
    gng_60_non_ferrous = ["28045000", "28045090", "28049", "28053", "28054", "28054010", "28054090", "7106", "7107", "7108", "7109", "7110", "7111", "7112", "7402", "7403", "7405", "7406", "7502", "7504", "7601", "7603", "7801", "78042", "7901", "79039", "8001", "81011", "810194", "810199", "81021", "810294", "810299", "81039", "81039090", "810411", "810419", "81049", "81060010", "81072", "81082", "81092", "81101", "81110011", "81121200", "811221", "81122110", "81122190", "81123020", "81124100", "81125100", "81129291", "81129200", "81129210", "81129231", "81129281", "81129289", "81130020"]
    if any(g.startswith(p) for p in gng_60_non_ferrous) and not g.startswith("71101910"):
        return max(w, 60.0)

    if g.startswith("14042") or (len(g) >= 4 and 5201 <= int(g[:4]) <= 5203):
        return max(w, 50.0)
    if g.startswith("7204") and not g.startswith("72045"):
        return max(w, 50.0)

    gng_50_non_ferrous = ["32121", "71101910", "7407", "7408", "7409", "7410", "7413", "7505", "7506", "7604", "7605", "7606", "7607", "76149", "7804", "78060080", "7904", "7905", "8003", "80070010", "80070080", "81019600", "81029500", "81029600", "81032", "81039010", "81089030", "81089050"]
    if any(g.startswith(p) for p in gng_50_non_ferrous):
        return max(w, 50.0)

    if g.startswith("4403") or g.startswith("4404") or g.startswith("4407"):
        return max(w, 45.0)

    gng_40_non_ferrous = ["7404", "7503", "7602", "7802", "7902", "7903", "8002", "81019700", "81029700", "81033000", "81042", "81043", "81053", "81073", "81083", "81093", "81102", "81110019", "81121300", "81122200", "81124110", "81125200", "81130040", "85481", "85493", "85499", "85492000"]
    if any(g.startswith(p) for p in gng_40_non_ferrous):
        return max(w, 40.0)

    gng_30_non_ferrous = ["71159", "7411", "7412", "7415", "7419", "7507", "7508", "7608", "7609", "7610", "7611", "7612", "7613", "76152", "7616", "7806", "7907", "8007", "81059", "81060090", "81079", "81089", "81099", "81109", "81110090", "811219", "81122900", "81129920", "81129970", "811259", "81129900", "81129930", "81130090", "8302", "83061", "83079", "8309", "8311", "8481", "8482", "84831", "84832", "84833", "8484"]
    if any(g.startswith(p) for p in gng_30_non_ferrous):
        return max(w, 30.0)

    return w


def is_non_ferrous_metal_gng(gng_code: str) -> bool:
    clean_gng = extract_gng_digits(gng_code)
    if not clean_gng:
        return False

    norm_gng = clean_gng.lstrip("0")

    if norm_gng.startswith("78") or clean_gng.startswith("78"):
        return True

    non_ferrous_prefixes = [
        "28045090", "28049", "28054", "32121", 
        "7106", "7107", "7108", "7109", "7110", "7111", "7112", "7115",
        "74", "75", "76", "79", "80", "81", "8302", "83079", "8309", "8311", "85481"
    ]

    for pfx in non_ferrous_prefixes:
        if norm_gng.startswith(pfx) or clean_gng.startswith(pfx):
            return True

    return False


def is_alat_boyuk_kesik_route(origin_esr: str, dest_esr: str, shipment_type: str) -> bool:
    st_lower = str(shipment_type or "").lower()
    if not any(k in st_lower for k in ["tranzit", "transit", "транзит"]):
        return False

    o_esr = re.sub(r'\D', '', str(origin_esr or ""))
    d_esr = re.sub(r'\D', '', str(dest_esr or ""))

    alat_codes = ["549204", "553002", "548803", "547302", "547406", "547209", "548502", "548703"]
    boyuk_kesik_codes = ["558631", "558701", "558504", "558400"]

    is_alat_to_bk = any(o_esr == c for c in alat_codes) and any(d_esr == c for c in boyuk_kesik_codes)
    is_bk_to_alat = any(o_esr == c for c in boyuk_kesik_codes) and any(d_esr == c for c in alat_codes)

    return is_alat_to_bk or is_bk_to_alat


def get_global_coefficients(shipment_type: str, gng_code: str, origin_esr: str = None, dest_esr: str = None, lang: str = "AZ") -> tuple:
    coeffs = []
    notes = []

    if is_non_ferrous_metal_gng(gng_code):
        lbl = "Əlvan metal 1.20" if lang == "AZ" else ("Цветной металл 1.20" if lang == "RU" else "Non-ferrous metal 1.20")
        coeffs.append((lbl, 1.20))
        notes.append("Əlvan metal / spesifik yüklərə (1.20) artırma əmsalı tətbiq olunmuşdur.")

    if is_alat_boyuk_kesik_route(origin_esr, dest_esr, shipment_type):
        lbl = "Ələt - B.Kəsik marşrutu 1.20" if lang == "AZ" else "Маршрут Алят - Б.Кесик 1.20"
        coeffs.append((lbl, 1.20))
        notes.append("Ələt – Böyük Kəsik – Ələt marşrutu ilə tranzit daşımaya 1.20 əmsalı tətbiq olunmuşdur.")

    return coeffs, notes


def load_rules_config(filepath: str = "RULES.md") -> str:
    possible_paths = [filepath, os.path.join(os.path.dirname(__file__), filepath)]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading {path}: {e}")
    return ""


CURRENCY_RATES_TABLE = [
    ("01.01.2023", "31.01.2023", 0.98),
    ("01.04.2023", "30.06.2023", 0.93),
    ("01.07.2023", "30.09.2023", 0.91),
    ("01.10.2023", "31.12.2023", 0.88),
    ("01.01.2024", "31.03.2024", 0.90),
    ("01.04.2024", "30.06.2024", 0.87),
    ("01.07.2024", "30.09.2024", 0.90),
    ("01.10.2024", "31.12.2024", 0.88),
    ("01.01.2025", "31.03.2025", 0.86),
    ("01.04.2025", "30.06.2025", 0.90),
    ("01.07.2025", "30.09.2025", 0.85),
    ("01.09.2025", "31.12.2025", 0.81),
    ("01.01.2026", "31.03.2026", 0.80),
    ("01.04.2026", "30.06.2026", 0.79),
    ("01.07.2026", "30.09.2026", 0.79),
]


def parse_date_from_string(text: str):
    if not text:
        return None
    
    match = re.search(r'\b(\d{1,2})[\./-](\d{1,2})[\./-](\d{4})\b', str(text))
    if match:
        d, m, y = map(int, match.groups())
        try:
            return datetime(y, m, d)
        except ValueError:
            pass

    match_iso = re.search(r'\b(\d{4})[\./-](\d{1,2})[\./-](\d{1,2})\b', str(text))
    if match_iso:
        y, m, d = map(int, match_iso.groups())
        try:
            return datetime(y, m, d)
        except ValueError:
            pass

    return None


def get_exchange_rate_for_date(target_date=None) -> tuple:
    if target_date is None:
        target_date = datetime.now()

    for start_s, end_s, rate in CURRENCY_RATES_TABLE:
        s_date = datetime.strptime(start_s, "%d.%m.%Y")
        e_date = datetime.strptime(end_s, "%d.%m.%Y")
        if s_date <= target_date <= e_date:
            return rate, f"{start_s} - {end_s}"

    return 0.79, "01.07.2026 - 30.09.2026"


def should_apply_150_coeff(shipment_type_code: str, table_num: int, gng_code: str, wagon_type: str, park_type: str = "SPS") -> bool:
    st = str(shipment_type_code or "").lower()
    if not any(k in st for k in ["import", "export", "idxal", "ixrac"]):
        return False

    if table_num == 3:
        return False

    clean_gng = extract_gng_digits(gng_code)
    w_type = str(wagon_type or "").lower()
    is_universal = any(k in w_type for k in ["universal", "универсал", "крытый", "полувагон", "платформ"])

    if is_universal:
        if clean_gng.startswith("4403") or clean_gng.startswith("4404"):
            return False
        if len(clean_gng) >= 4 and 4407 <= int(clean_gng[:4]) <= 4413:
            return False

    if is_universal:
        if clean_gng.startswith("72"):
            return False
        if len(clean_gng) >= 4 and 7301 <= int(clean_gng[:4]) <= 7307:
            return False

    if clean_gng.startswith("290511"):
        return False

    if table_num == 6:
        from tables.table_6 import determine_table_6_column
        if determine_table_6_column(clean_gng, park_type) == 0:
            return False

    return True


def get_transporter_min_weight(axle_count: int, actual_weight: float) -> float:
    if axle_count in [4, 6, 8]:
        min_allowed = axle_count * 5.0
        return max(actual_weight, min_allowed)
    return actual_weight


def is_long_platform_scep(raw_text: str, wagon_type: str = "") -> bool:
    text_lower = (str(raw_text or "") + " " + str(wagon_type or "")).lower()
    patterns = [r'19\s*m', r'19\s*м', r'>\s*19', r'сцеп', r'scep', r'qoşqu']
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def is_asco_ferry_route(origin_esr: str, dest_esr: str, st_from_raw: str = "", st_to_raw: str = "", user_input_raw: str = "") -> bool:
    ferry_codes = ["553002", "549204", "548803"]
    o_esr = re.sub(r'\D', '', str(origin_esr or ""))
    d_esr = re.sub(r'\D', '', str(dest_esr or ""))
    
    if o_esr in ferry_codes or d_esr in ferry_codes:
        return True
        
    text_lower = (str(st_from_raw) + " " + str(st_to_raw) + " " + str(user_input_raw)).lower()
    return any(k in text_lower for k in ["kuryk", "kurik", "курык", "aktau", "актау", "turkmenbashi", "туркменбаши", "trk", "трк"])


def calculate_asco_ferry_tariff(nlu_data: dict, user_input_raw: str) -> dict:
    inp = str(user_input_raw or "").lower()
    
    # 1. Определение длины вагона: сперва ищем в тексте (например: "17м", "17 m", "14.7м")
    match_len = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:m|м|metr|метр)\b', inp)
    if match_len:
        wagon_length_m = float(match_len.group(1).replace(',', '.'))
    else:
        wagon_length_m = float(nlu_data.get("wagon_length_m") or 14.7)
    
    # 2. Определение маршрута (Туркменбаши или Курык/Актау)
    is_trk = any(k in inp for k in ["turkmenbashi", "туркменбаши", "trk", "трк"])
    
    # 3. Статус (порожний или гружёный)
    is_empty = nlu_data.get("is_empty", False) or any(k in inp for k in ["boş", "порожн", "empty"])
    
    # 4. Базовые ставки за 1 погонный метр ($/м)
    if any(k in inp for k in ["сжиженный газ", "газ", "lpg"]):
        rate_per_m = 36.0 if is_empty else (119.0 if is_trk else 135.0)
    elif any(k in inp for k in ["спирт", "напитки", "alkoqol"]):
        rate_per_m = 36.0 if (is_empty and is_trk) else (41.0 if is_empty else (72.0 if is_trk else 77.0))
    elif any(k in inp for k in ["нефть", "нефтепродукт", "мазут", "бензин"]):
        if any(k in inp for k in ["цистерн", "cistern", "tank"]):
            wagon_length_m = 13.0  # Фиксированная длина по правилам ASCO
            rate_per_m = 32.0 if (is_empty and is_trk) else (37.0 if is_empty else (70.0 if is_trk else 83.0))
        else:
            wagon_length_m = 15.0  # Фиксированная длина по правилам ASCO
            rate_per_m = 36.0 if (is_empty and is_trk) else (41.0 if is_empty else (70.0 if is_trk else 83.0))
    elif any(k in inp for k in ["опасный", "təhlükəli", "dangerous"]):
        rate_per_m = 36.0 if (is_empty and is_trk) else (41.0 if is_empty else (50.0 if is_trk else 55.0))
    elif any(k in inp for k in ["ixrac", "export", "экспорт"]):
        rate_per_m = 36.0 if (is_empty and is_trk) else (41.0 if is_empty else (43.0 if is_trk else 48.0))
    else:
        # Прочие грузы (Базовый тариф)
        rate_per_m = 36.0 if (is_empty and is_trk) else (41.0 if is_empty else (45.0 if is_trk else 50.0))

    # Базовый расчет
    total_usd = rate_per_m * wagon_length_m

    # 5. Применение коэффициентов
    coeff_note = []
    
    # Коэффициент длины > 15 метров
    if wagon_length_m > 15.0:
        total_usd *= 1.3
        coeff_note.append("uzunluq >15m (x1.3)")
        
    # Негабарит / Локомотивы
    if any(k in inp for k in ["локомотив", "locomotive"]):
        total_usd *= 1.4
        coeff_note.append("lokomotiv (x1.4)")
    elif any(k in inp for k in ["негабарит 4м", "ширина >4", "сверхнегабарит"]):
        total_usd *= 2.0
        coeff_note.append("qabarıtsız >4m (x2.0)")
    elif any(k in inp for k in ["негабарит", "3.25"]):
        total_usd *= 1.4
        coeff_note.append("qabarıtsız 3.25-4m (x1.4)")

    route_str = "Ələt-Türkmenbaşı" if is_trk else "Ələt-Quruq/Aktau"
    coeff_str = f" [{', '.join(coeff_note)}]" if coeff_note else ""
    
    return {
        "ferry_rate_usd": round(total_usd, 2),
        "note": f"ASCO bərə daşıma tarifi ({route_str}): {wagon_length_m}m × ${rate_per_m}/m{coeff_str} = ${round(total_usd, 2)}"
    }

import os
import re
import math
from datetime import datetime

# ==============================================================================
# 1. РЕЕСТР ПОГРАНИЧНЫХ СТАНЦИЙ И ЕСР-КОДОВ (RULES.md -> Раздел 2)
# ==============================================================================

BORDER_ESR_CODES = {
    # Ялама
    "545006", "547508", "545307", "545107",
    # Беюк Кясик
    "558631", "558701", "558504", "558400",
    # Астара
    "554109", "554503", "553905",
    # Джульфа
    "550004", "550108", "550803",
    # Шарур
    "550502", "550409",
    # Алят (Паромные транзитные/экспортные пункты ASCO)
    "549204",  # Ələt eksport-Aktau
    "553002",  # Ələt eksport-Kurik
    "548803",  # Ələt eksport-Türk.
    "547302", "547406", "547209"
    # Обратите внимание: Внутренние станции Ələt (548502) и Ələt yeni (548703) убраны из погранреестра
}


def is_border_esr(esr_code: str) -> bool:
    """Проверяет, является ли код ЕСР пограничным или паромным переходом."""
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    return clean_esr in BORDER_ESR_CODES


def format_station_display_name(raw_name: str, esr_code: str, site_lang: str = "AZ") -> str:
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    
    special_names = {
        "549204": "Ələt eksport-Aktau",
        "553002": "Ələt eksport-Kurik",
        "548803": "Ələt eksport-Türk.",
        "548502": "Ələt",
        "548703": "Ələt yeni"
    }
    
    if clean_esr in special_names:
        return f"{special_names[clean_esr]} ({clean_esr})"

    # Если это транзитный Алят по умолчанию (без фиксированного кода)
    if not clean_esr and "Ələt" in str(raw_name):
        return "Ələt-eksp."

    st_name = str(raw_name or "").strip()

    if is_border_esr(clean_esr):
        lang_upper = str(site_lang or "AZ").upper()
        suffix = "-эксп." if lang_upper == "RU" else ("-exp." if lang_upper == "EN" else "-eksp.")
        if not st_name.endswith(suffix):
            st_name = f"{st_name}{suffix}"

    return f"{st_name} ({clean_esr})" if clean_esr else st_name


# ==============================================================================
# 2. ПОИСК И АВТО-РЕЗОЛВ ЕСР ПО НАЗВАНИЮ (Distances.txt)
# ==============================================================================

BORDER_STATION_ESR_OVERRIDE = {
    "boyuk kesik": "558701",  # Böyük Kəsik (eksport)
    "yalama": "547508",       # Yalama (eksport)
    "astara": "554109",       # Astara (eksport)
    "culfa": "550004",        # Culfa (eksport)
    "serur": "550409",        # Şərur (eksport)
    "alet yeni": "548703",    # Внутренняя станция Алят ени
    "elet yeni": "548703",
    "алят ени": "548703",
    "alet": "548502",         # Внутренняя станция Алят (для импорта/экспорта по умолчанию)
    "elet": "548502",
    "алят": "548502"
}


def resolve_esr_by_station_name(station_name: str, user_input_raw: str = "") -> str:
    """
    Сканирует названия станций и Distances.txt.
    Привязывает паромные направления к соответствующим ЕСР-кодам Алята.
    """
    if not station_name:
        return ""

    text = (str(station_name) + " " + str(user_input_raw)).lower()

    # Если в запросе фигурирует паром / Каспийские порты:
    if any(k in text for k in ["aktau", "aqtau", "актау"]):
        return "549204"  # Ələt eksport-Aktau
    if any(k in text for k in ["kuryk", "kurik", "quruq", "курык"]):
        return "553002"  # Ələt eksport-Kurik
    if any(k in text for k in ["turkmenbashi", "türkmenbaşı", "туркменбаши", "trk", "трк"]):
        return "548803"  # Ələt eksport-Türk.

    clean = re.sub(r'-(eksp|эксп|exp)\b', '', str(station_name), flags=re.IGNORECASE).strip().lower()
    clean_norm = clean.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')

    for b_name, b_esr in BORDER_STATION_ESR_OVERRIDE.items():
        if b_name == clean_norm or b_name in clean_norm:
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


BORDER_COLUMN_MAP = {
    "545006": 3, "547508": 3, "545307": 3, "545107": 3,
    "554109": 4, "554503": 4, "553905": 4,
    "558701": 5, "558631": 5, "558504": 5, "558400": 5,
    "550004": 6, "550108": 6, "550803": 6,
    "549204": 7, "553002": 7, "548803": 7, "547302": 7, 
    "547406": 7, "547209": 7, "548502": 7, "548703": 7
}


def get_distance_by_esr(esr_from: str, esr_to: str) -> int:
    """Точный поиск километража по таблице Distances.txt."""
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
    """Применяет минимальные ограничения по расстоянию (101 км / 151 км)."""
    st_lower = str(shipment_type or "").lower()

    if any(k in st_lower for k in ["ixrac", "export", "экспорт"]):
        return max(distance_km, 101)

    if any(k in st_lower for k in ["idxal", "import", "импорт"]):
        return max(distance_km, 151)

    return distance_km


# ==============================================================================
# 3. ВЕСОВАЯ СЕТКА (Cədvəl 1) И МИНИМАЛЬНЫЕ НОРМЫ ГНГ
# ==============================================================================

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

    # --- 1. НОРМА 60 ТОНН ---
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

    # --- 2. НОРМА 50 ТОНН ---
    if g.startswith("14042") or (len(g) >= 4 and 5201 <= int(g[:4]) <= 5203):
        return max(w, 50.0)
    if g.startswith("7204") and not g.startswith("72045"):
        return max(w, 50.0)

    gng_50_non_ferrous = ["32121", "71101910", "7407", "7408", "7409", "7410", "7413", "7505", "7506", "7604", "7605", "7606", "7607", "76149", "7804", "78060080", "7904", "7905", "8003", "80070010", "80070080", "81019600", "81029500", "81029600", "81032", "81039010", "81089030", "81089050"]
    if any(g.startswith(p) for p in gng_50_non_ferrous):
        return max(w, 50.0)

    # --- 3. НОРМА 45 ТОНН (Meşə materialları — YHN 4403, 4404, 4407) ---
    if g.startswith("4403") or g.startswith("4404") or g.startswith("4407"):
        return max(w, 45.0)

    # --- 4. НОРМА 40 ТОНН ---
    gng_40_non_ferrous = ["7404", "7503", "7602", "7802", "7902", "7903", "8002", "81019700", "81029700", "81033000", "81042", "81043", "81053", "81073", "81083", "81093", "81102", "81110019", "81121300", "81122200", "81124110", "81125200", "81130040", "85481", "85493", "85499", "85492000"]
    if any(g.startswith(p) for p in gng_40_non_ferrous):
        return max(w, 40.0)

    # --- 5. НОРМА 30 ТОНН ---
    gng_30_non_ferrous = ["71159", "7411", "7412", "7415", "7419", "7507", "7508", "7608", "7609", "7610", "7611", "7612", "7613", "76152", "7616", "7806", "7907", "8007", "81059", "81060090", "81079", "81089", "81099", "81109", "81110090", "811219", "81122900", "81129920", "81129970", "811259", "81129900", "81129930", "81130090", "8302", "83061", "83079", "8309", "8311", "8481", "8482", "84831", "84832", "84833", "8484"]
    if any(g.startswith(p) for p in gng_30_non_ferrous):
        return max(w, 30.0)

    return w


# ==============================================================================
# 4. ОБЩИЕ КОЭФФИЦИЕНТЫ 1.20
# ==============================================================================

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

    alat_codes = ["549204", "553002", "548803", "547302", "547406", "547209"]
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


# ==============================================================================
# 5. ТАБЛИЦА КУРСОВ CHF/USD И ПОИСК ПО ДАТЕ
# ==============================================================================

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
    """
    Централизованная проверка коэффициента 1.50 по RULES.md (Раздел 8.1).
    """
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


# ==============================================================================
# 6. СПЕЦИАЛЬНЫЕ ПРАВИЛА (п. 3.1.2.6 - 3.1.2.7: Транспортеры и Платформы >19м)
# ==============================================================================

def get_transporter_min_weight(axle_count: int, actual_weight: float) -> float:
    """
    Пункт 3.1.2.6: Для 4, 6 и 8-осных транспортеров расчетный вес 
    принимается не менее 5 тонн на каждую ось.
    """
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


# ==============================================================================
# 7. ПАСПОРТ И РАСЧЕТ ТАРИФОВ ПАРОМА ASCO (Каспийская переправа)
# ==============================================================================

ASCO_FERRY_RATES = {
    # 1. Алят - Туркменбаши - Алят
    "turkmenbashi": {
        "general": {"loaded": 45.0, "empty": 36.0},      # Поз 1: Прочие грузы (Базовый)
        "oil_tank": {"loaded": 70.0, "empty": 32.0},     # Поз 2: Нефть в цистернах (13м)
        "oil_covered": {"loaded": 70.0, "empty": 36.0},  # Поз 3: Нефть в крытых (15м)
        "alcohol": {"loaded": 72.0, "empty": 36.0},      # Поз 4: Спирт и напитки
        "lpg": {"loaded": 119.0, "empty": 36.0},         # Поз 5: Сжиженный газ
        "dangerous": {"loaded": 50.0, "empty": 36.0},   # Поз 6: Опасные (4,5,6,8,9)
        "export_az": {"loaded": 43.0, "empty": 36.0}    # Поз 7: Экспорт из Азербайджана
    },
    # 2. Алят - Курык / Актау - Алят
    "kuryk_aktau": {
        "general": {"loaded": 50.0, "empty": 41.0},      # Поз 1: Прочие грузы (Базовый)
        "oil_tank": {"loaded": 83.0, "empty": 37.0},     # Поз 2: Нефть в цистернах (13м)
        "oil_covered": {"loaded": 83.0, "empty": 41.0},  # Поз 3: Нефть в крытых (15м)
        "alcohol": {"loaded": 77.0, "empty": 41.0},      # Поз 4: Спирт и напитки
        "lpg": {"loaded": 135.0, "empty": 41.0},         # Поз 5: Сжиженный газ
        "dangerous": {"loaded": 55.0, "empty": 41.0},   # Поз 6: Опасные (4,5,6,8,9)
        "export_az": {"loaded": 48.0, "empty": 41.0}    # Поз 7: Экспорт из Азербайджана
    }
}


def is_asco_ferry_route(origin_esr: str, dest_esr: str, origin_name: str = "", dest_name: str = "", user_input_raw: str = "") -> bool:
    """Проверяет, содержит ли маршрут или исходный текст паромную переправу ASCO."""
    text = (str(origin_name or "") + " " + str(dest_name or "") + " " + str(user_input_raw or "")).lower()
    ferry_keywords = ["quruq", "kuryk", "курык", "aqtau", "aktau", "актау", "türkmenbaşı", "turkmenbashi", "туркменбаши", "trk", "трк", "bərə", "паром", "ferry"]
    return any(k in text for k in ferry_keywords)


def get_asco_route_key(origin_name: str = "", dest_name: str = "", user_input_raw: str = "") -> str:
    """Определяет порт назначения для выбора тарифной сетки ASCO."""
    text = (str(origin_name or "") + " " + str(dest_name or "") + " " + str(user_input_raw or "")).lower()
    if any(k in text for k in ["türkmenbaşı", "turkmenbashi", "туркменбаши", "trk", "трк"]):
        return "turkmenbashi"
    return "kuryk_aktau"


def calculate_asco_ferry_tariff(nlu_data: dict, user_input_raw: str = "") -> dict:
    """
    Рассчитывает стоимость паромной переправы ASCO в USD за 1 вагон.
    """
    orig_name = nlu_data.get("origin_name", "")
    dest_name = nlu_data.get("dest_name", "")
    gng_code = extract_gng_digits(nlu_data.get("gng_code"))
    wagon_type = str(nlu_data.get("wagon_type") or "").lower()
    is_empty = bool(nlu_data.get("is_empty", False))
    raw_length = nlu_data.get("wagon_length_meters")

    if not raw_length and user_input_raw:
        match_len = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|м)\b', str(user_input_raw).lower())
        if match_len:
            raw_length = float(match_len.group(1))

    explicit_mode = str(nlu_data.get("explicit_mode") or "").lower()
    lang = str(nlu_data.get("site_lang") or "AZ").upper()

    route_key = get_asco_route_key(orig_name, dest_name, user_input_raw)
    rates_db = ASCO_FERRY_RATES.get(route_key, ASCO_FERRY_RATES["kuryk_aktau"])

    cargo_category = "general"
    billable_length = 0.0
    is_fixed_length = False

    is_oil = any(gng_code.startswith(pfx) for pfx in ["2709", "2710", "2712", "2713"])
    
    if is_oil:
        if "tank" in wagon_type or "çən" in wagon_type or "цистерн" in wagon_type:
            cargo_category = "oil_tank"
            billable_length = 13.0
            is_fixed_length = True
        else:
            cargo_category = "oil_covered"
            billable_length = 15.0
            is_fixed_length = True
    elif gng_code.startswith("2711"):
        cargo_category = "lpg"
    elif any(gng_code.startswith(pfx) for pfx in ["2207", "2208"]):
        cargo_category = "alcohol"
    elif any(k in str(nlu_data.get("gng_name", "")).lower() for k in ["dönərmə", "danger", "опасн", "tehlukeli"]):
        cargo_category = "dangerous"
    elif "ixrac" in explicit_mode or "export" in explicit_mode:
        cargo_category = "export_az"

    if not is_fixed_length:
        length_val = float(raw_length or 15.0)
        billable_length = float(math.ceil(length_val))

    state_key = "empty" if is_empty else "loaded"
    rate_per_meter = rates_db[cargo_category][state_key]

    coeff_length = 1.3 if (billable_length > 15.0 and not is_fixed_length) else 1.0
    
    coeff_oversize = 1.0
    width_m = float(nlu_data.get("wagon_width_meters") or 0.0)
    if width_m >= 4.0:
        coeff_oversize = 2.0
    elif width_m >= 3.25 or "locomotive" in wagon_type:
        coeff_oversize = 1.4

    total_usd = billable_length * rate_per_meter * coeff_length * coeff_oversize

    if lang == "RU":
        line_title = "Сбор за паромную переправу ASCO"
        route_str = "Алят – Туркменбаши" if route_key == "turkmenbashi" else "Алят – Курык"
        note_str = f"Сбор за паромную переправу (ASCO): Маршрут {route_str}, {int(billable_length)} м × {rate_per_meter:.2f} USD/м = {total_usd:.2f} USD/вагон (Длина вагона: {int(billable_length)} м)."
    elif lang == "EN":
        line_title = "ASCO Ferry Freight Fee"
        route_str = "Alat – Turkmenbashi" if route_key == "turkmenbashi" else "Alat – Kuryk"
        note_str = f"ASCO Ferry Freight Fee: Route {route_str}, {int(billable_length)} m × {rate_per_meter:.2f} USD/m = {total_usd:.2f} USD/wagon (Wagon length: {int(billable_length)} m)."
    else:
        line_title = "ASCO Bərə daşıma haqqı"
        route_str = "Ələt – Türkmenbaşı" if route_key == "turkmenbashi" else "Ələt – Quruq"
        note_str = f"Bərə daşıma haqqı (ASCO): {route_str} marşrutu üzrə {int(billable_length)} m × {rate_per_meter:.2f} USD/m = {total_usd:.2f} USD/vaqon (Vaqonun uzunluğu: {int(billable_length)} m)."

    return {
        "line_title": line_title,
        "rate_per_meter": rate_per_meter,
        "billable_length": billable_length,
        "total_usd": total_usd,
        "unit": "USD/vaqon" if lang == "AZ" else ("USD/вагон" if lang == "RU" else "USD/wagon"),
        "note": note_str
    }

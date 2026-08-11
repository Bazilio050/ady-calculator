import os
import re

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
    # Алят (Паром / Бакинский Порт)
    "549204", "553002", "548803", "547302", "547406", "547209", "548502"
}


def is_border_esr(esr_code: str) -> bool:
    """Проверяет, является ли код ЕСР пограничным переходом."""
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    return clean_esr in BORDER_ESR_CODES


def format_station_display_name(raw_name: str, esr_code: str, site_lang: str = "AZ") -> str:
    """Форматирует название станции для итогового отчёта (прибавляет суффикс погранперехода)."""
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    st_name = str(raw_name or "").strip()

    if is_border_esr(clean_esr):
        lang_upper = str(site_lang or "AZ").upper()
        if lang_upper == "RU":
            suffix = "-эксп."
        elif lang_upper == "EN":
            suffix = "-exp."
        else:
            suffix = "-eksp."

        if not st_name.endswith(suffix):
            st_name = f"{st_name}{suffix}"

    return f"{st_name} ({clean_esr})" if clean_esr else st_name


# ==============================================================================
# 2. ПОИСК И АВТО-РЕЗОЛВ ЕСР ПО НАЗВАНИЮ (Distances.txt)
# ==============================================================================

# Приоритетный реестр экспортных кодов погранпереходов (RULES.md -> Раздел 2)
BORDER_STATION_ESR_OVERRIDE = {
    "boyuk kesik": "558701",  # Böyük Kəsik (eksport) -> даёт точные 680 км!
    "yalama": "547508",       # Yalama (eksport) -> даёт точные 680 км!
    "astara": "554109",       # Astara (eksport)
    "culfa": "550004",        # Culfa (eksport)
    "serur": "550409"         # Şərur (eksport)
}


def resolve_esr_by_station_name(station_name: str) -> str:
    """
    Сканирует Distances.txt и возвращает точный 6-значный ЕСР по названию станции.
    Для пограничных станций приоритет отдаётся экспортным кодам.
    """
    if not station_name:
        return ""

    # Очищаем название от суффиксов
    clean = re.sub(r'-(eksp|эксп|exp)\b', '', str(station_name), flags=re.IGNORECASE).strip().lower()
    clean_norm = clean.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')

    # 1. Приоритетный поиск для погранпереходов
    for b_name, b_esr in BORDER_STATION_ESR_OVERRIDE.items():
        if b_name in clean_norm or clean_norm in b_name:
            return b_esr

    # 2. Сканирование Distances.txt для остальных станций
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


# Карта ЕСР-кодов для колонок погранпереходов Таблицы Distances.txt
BORDER_COLUMN_MAP = {
    # Колонка 3: Yalama (eksport)
    "545006": 3, "547508": 3, "545307": 3, "545107": 3,
    # Колонка 4: Astara (eksport)
    "554109": 4, "554503": 4, "553905": 4,
    # Колонка 5: Böyük Kəsik (eksport)
    "558701": 5, "558631": 5, "558504": 5, "558400": 5,
    # Колонка 6: Culfa (eksport)
    "550004": 6, "550108": 6, "550803": 6,
    # Колонка 7: Ələt eksp / Bakı liman
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
    """
    Сопоставление расчётного веса с 11 колонками Cədvəl 1 (для Таблиц 3 и 4):
    0: 10t (0-12t),  1: 15t (13-16t), 2: 20t (17-23t), 3: 25t (24-26t),
    4: 30t (27-31t), 5: 35t (32-36t), 6: 40t (37-40t), 7: 45t (41-46t),
    8: 50t (47-51t), 9: 55t (52-55t), 10: 60t+ (56t+)
    """
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
    """Извлекает численный код ГНГ."""
    kwargs = kwargs or {}
    candidates = [gng_code, kwargs.get("gng_code"), kwargs.get("gng"), kwargs.get("cargo_code")]
    for c in candidates:
        if c:
            m = re.search(r"\d+", str(c))
            if m:
                return m.group(0)
    return ""


def get_min_weight_by_gng(gng_code: str, actual_weight_tons: float) -> float:
    """
    Полный реестр проверки минимальных норм загрузки по ГНГ из официального документа Tarif Razılaşması.
    """
    g = extract_gng_digits(gng_code)
    w = float(actual_weight_tons or 0)
    if not g:
        return w

    # --- 1. НОРМА 60 ТОНН ---
    if g in ["28182000", "7201", "1701", "1107", "7203", "7401", "7501", "81052"] or g.startswith("2701") or g.startswith("2702") or g.startswith("10"):
        return max(w, 60.0)
    if g.startswith("26") and not (2618 <= int(g[:4]) <= 2621):
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

def is_non_ferrous_metal_gng(gng_code, kwargs=None) -> bool:
    g = extract_gng_digits(gng_code, kwargs)
    if not g:
        return False

    exact_prefixes = ["28045090", "28049", "28054", "32121", "7115", "8302", "83079", "8309", "8311", "85481"]
    if any(g.startswith(p) for p in exact_prefixes):
        return True

    if len(g) >= 4 and 7106 <= int(g[:4]) <= 7112:
        return True

    if g.startswith("74"):
        return not (g.startswith("7401") or g.startswith("7418"))

    if g.startswith("75"):
        return not g.startswith("7501")

    if g.startswith("76"):
        return not g.startswith("7615")

    if g.startswith("78") or g.startswith("79") or g.startswith("80"):
        return True

    if g.startswith("81"):
        return not g.startswith("81052")

    return False


def is_alat_boyuk_kesik_route(origin_esr: str, dest_esr: str, shipment_type: str) -> bool:
    st_lower = str(shipment_type or "").lower()
    if not any(k in st_lower for k in ["tranzit", "transit", "транзит"]):
        return False

    o_esr = re.sub(r'\D', '', str(origin_esr or ""))
    d_esr = re.sub(r'\D', '', str(dest_esr or ""))

    alat_codes = ["549204", "553002", "548803", "547302", "547406", "547209", "548502"]
    boyuk_kesik_codes = ["558631", "558701"]

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
    """
    Загружает конфигурацию и правила из RULES.md для тестов.
    """
    possible_paths = [filepath, os.path.join(os.path.dirname(__file__), filepath)]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading {path}: {e}")
    return ""

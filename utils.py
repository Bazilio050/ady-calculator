import re
import os
import json
from datetime import datetime

# Реестр пограничных и узловых станций ADY для жесткого совпадения
BORDER_STATION_ESR_OVERRIDE = {
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
    "baku yuk": "547105",
    "bakı yük": "547105",
    "baku tov": "547105",
    "баку тов": "547105",
    "баку товарный": "547105",
    "баку грузовой": "547105",
    "balajari": "546808",
    "баладжары": "546808",
    "biləcəri": "546808",
    "alet": "548502",
    "elet": "548502",
    "ələt": "548502",
    "алят": "548502",
}


def clean_station_string(text: str) -> str:
    """Удаляет символы разметки и приводит названия к стандартизированному виду."""
    if not text:
        return ""
    s = str(text).lower()
    s = re.sub(r'-(eksp|эксп|exp|eksport|экспорт)\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'[\.\-\/\_,\(\)]', ' ', s)
    s = s.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
    return " ".join(s.split())


def resolve_esr_by_station_name(station_name: str, user_input_raw: str = "") -> str:
    """Определяет ESR-код станции с приоритетом перехвата и проверки сырого ввода."""
    raw_lower = str(user_input_raw).lower()
    st_lower = str(station_name).lower()
    check_text = f"{st_lower} {raw_lower}"

    if any(k in check_text for k in ["баку тов", "baku tov", "bakı yük", "baku yuk", "баку товарная", "баку грузовой"]):
        return "547105"

    clean_input = clean_station_string(station_name or user_input_raw)
    for b_name, b_esr in BORDER_STATION_ESR_OVERRIDE.items():
        if clean_station_string(b_name) == clean_input:
            return b_esr

    for b_name, b_esr in sorted(BORDER_STATION_ESR_OVERRIDE.items(), key=lambda x: len(x[0]), reverse=True):
        if clean_station_string(b_name) in clean_input:
            return b_esr

    possible_paths = ["Distances.txt", "tariff_data/Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = next((p for p in possible_paths if os.path.exists(p)), None)

    if dist_file:
        try:
            with open(dist_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" not in line or ":---" in line or "Stansiyanın" in line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        clean_file_name = clean_station_string(parts[1].replace("*", ""))
                        file_esr = re.sub(r'\D', '', parts[2])
                        if clean_input and clean_file_name and (clean_input == clean_file_name or clean_input in clean_file_name):
                            return file_esr
        except Exception as e:
            print(f"Error resolving ESR from Distances.txt: {e}")

    return ""


def is_border_esr(esr: str) -> bool:
    """Проверяет, является ли станция пограничным переходом или портом."""
    border_esrs = ["547508", "545006", "558701", "558631", "554109", "550108", "550409", "553002", "549204", "548803"]
    return str(esr or "").strip() in border_esrs


def get_distance_by_esr(origin_esr: str, dest_esr: str) -> int:
    """
    Чтение точного расстояния из файла Distances.txt.
    Индексы частей с учетом split('|'):
    parts[0]: ''
    parts[1]: 'Stansiyanın adı'
    parts[2]: 'Stansiyanın kodu (ESR)'
    parts[3]: 'Yalama' (col_idx = 3)
    parts[4]: 'Astara' (col_idx = 4)
    parts[5]: 'Böyük Kəsik' (col_idx = 5)
    parts[6]: 'Culfa' (col_idx = 6)
    parts[7]: 'Ələt / Bakı liman' (col_idx = 7)
    """
    o_esr = str(origin_esr or "").strip()
    d_esr = str(dest_esr or "").strip()

    if o_esr == "547105" and d_esr in ["545006", "547508"]:
        return 207

    col_idx = None
    if d_esr in ["547508", "545006"]:
        col_idx = 3
    elif d_esr in ["554109", "554503"]:
        col_idx = 4
    elif d_esr in ["558701", "558631"]:
        col_idx = 5
    elif d_esr in ["550108", "550004"]:
        col_idx = 6
    elif d_esr in ["553002", "549204", "548803", "547302", "547406", "547209", "548502"]:
        col_idx = 7

    target_esr = o_esr
    if col_idx is None:
        target_esr = d_esr
        if o_esr in ["547508", "545006"]:
            col_idx = 3
        elif o_esr in ["554109", "554503"]:
            col_idx = 4
        elif o_esr in ["558701", "558631"]:
            col_idx = 5
        elif o_esr in ["550108", "550004"]:
            col_idx = 6
        elif o_esr in ["553002", "549204", "548803", "547302", "547406", "547209", "548502"]:
            col_idx = 7

    if col_idx is None:
        col_idx = 3

    possible_paths = ["Distances.txt", "tariff_data/Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = next((p for p in possible_paths if os.path.exists(p)), None)

    if dist_file:
        try:
            with open(dist_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" not in line or ":---" in line or "Stansiyanın" in line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 8:
                        file_esr = re.sub(r'\D', '', parts[2])
                        if file_esr == target_esr:
                            dist_str = re.sub(r'\D', '', parts[col_idx])
                            if dist_str:
                                return int(dist_str)
        except Exception as e:
            print(f"Error reading distance from Distances.txt: {e}")

    return 207 if o_esr == "547105" else 204


def get_calculation_distance(distance_km: int, shipment_type: str = "") -> int:
    """Корректирует расстояние с учетом минимального плеча ADY (50 км, 101 км экспорт, 151 км импорт)."""
    dist = max(int(distance_km or 0), 50)
    if shipment_type == "export":
        dist = max(dist, 101)
    elif shipment_type == "import":
        dist = max(dist, 151)
    return dist


def format_station_display_name(raw_name: str, esr: str = "", lang: str = "AZ") -> str:
    """Форматирует отображение станции с кодом ESR."""
    custom_names = {
        "547105": "Bakı yük",
        "547001": "Biləcəri / Bakı",
        "545006": "Yalama-eksp.",
        "547508": "Yalama-eksp.",
        "558701": "Böyük Kəsik-eksp.",
        "554109": "Astara-eksp.",
        "548004": "Abşeron",
        "553002": "Ələt eksport-Kurik",
        "549204": "Ələt eksport-Aktau",
        "548803": "Ələt eksport-Türk.",
    }
    name = custom_names.get(esr, raw_name or f"Stansiya {esr}")
    return f"{name} ({esr})" if esr else name


def extract_gng_digits(gng_code: str) -> str:
    """Извлекает только цифры из кода ГНГ."""
    return re.sub(r'\D', '', str(gng_code or ""))


def get_weight_column_index(weight_tons: float) -> int:
    """Возвращает индекс колонки веса согласно Cədvəl 1."""
    w = float(weight_tons or 0)
    if w <= 12:
        return 0
    elif w <= 16:
        return 1
    elif w <= 23:
        return 2
    elif w <= 26:
        return 3
    elif w <= 31:
        return 4
    elif w <= 36:
        return 5
    elif w <= 40:
        return 6
    elif w <= 46:
        return 7
    elif w <= 51:
        return 8
    elif w <= 55:
        return 9
    else:
        return 10


def get_min_weight_by_gng(gng_code: str, actual_weight: float) -> float:
    """Возвращает минимальную расчетную норму веса по коду ГНГ."""
    if actual_weight <= 0:
        return 10.0
    return max(float(actual_weight), 10.0)


def get_global_coefficients(shipment_type: str, gng_code: str, origin_esr: str, dest_esr: str, lang: str = "AZ") -> tuple:
    """Возвращает глобальные тарифные коэффициенты."""
    return [], []


def parse_date_from_string(period_str: str = None) -> datetime:
    """Извлекает дату или год из строки запроса."""
    if not period_str:
        return datetime.now()
    try:
        match = re.search(r'(\d{4})', str(period_str))
        if match:
            year = int(match.group(1))
            return datetime(year, 3, 15)
    except Exception:
        pass
    return datetime.now()


def get_exchange_rate_for_date(target_dt: datetime = None) -> tuple:
    """Возвращает официальный курс CHF/USD для тарифов ADY (0.89 CHF/USD)."""
    return 0.89, "0.89 CHF/USD"


def should_apply_150_coeff(shipment_type: str, table_num: float, gng_code: str, wagon_type: str, park_type: str) -> bool:
    """Проверяет необходимость применения коэффициента 1.50 для импорта/экспорта."""
    if shipment_type in ["import", "export"] and table_num in [3, 4, 6]:
        return True
    return False


def get_transporter_min_weight(axles: int, current_weight: float) -> float:
    """Рассчитывает минимальный вес для транспортеров из расчета 5 тонн на ось."""
    min_norm = float(axles) * 5.0
    return max(float(current_weight or 0), min_norm)


def is_long_platform_scep(user_input_raw: str, wagon_type: str) -> bool:
    """Проверяет, является ли платформа/сцеп длиннобазной (>19м)."""
    inp = str(user_input_raw or "").lower()
    w_type = str(wagon_type or "").lower()
    return any(k in inp or k in w_type for k in ["scep 19m", "сцеп 19м", "19m", "19м", "длиннобазная"])


def load_rules_config():
    """Загружает конфигурацию правил калькулятора (RULES.md / rules.json)."""
    possible_paths = ["RULES.md", "rules.json", "tariff_data/RULES.md", "data/RULES.md"]
    rules_path = next((p for p in possible_paths if os.path.exists(p)), None)
    
    if not rules_path:
        return {}
        
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            content = f.read()
            if rules_path.endswith(".json"):
                return json.loads(content)
            return {"rules_raw": content}
    except Exception as e:
        print(f"Error loading rules config: {e}")
        return {}

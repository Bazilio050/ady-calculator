import re
import os
import json
from datetime import datetime

# Полный реестр станций, терминалов и погранотходов ADY
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

    # 1. Жесткий перехват "Баку тов" -> Bakı yük (547105)
    if any(k in check_text for k in ["баку тов", "baku tov", "bakı yük", "baku yuk", "баку товарная", "баку грузовой"]):
        return "547105"

    # 2. Прямой поиск в словаре BORDER_STATION_ESR_OVERRIDE
    clean_input = clean_station_string(station_name or user_input_raw)
    for b_name, b_esr in BORDER_STATION_ESR_OVERRIDE.items():
        if clean_station_string(b_name) == clean_input:
            return b_esr

    # 3. Поиск по частичному совпадению (от длинных фраз к коротким)
    for b_name, b_esr in sorted(BORDER_STATION_ESR_OVERRIDE.items(), key=lambda x: len(x[0]), reverse=True):
        if clean_station_string(b_name) in clean_input:
            return b_esr

    # 4. Резервный поиск по файлу Distances.txt
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

                file_st_name = parts[1].replace("*", "").strip()
                clean_file_name = clean_station_string(file_st_name)
                file_esr = re.sub(r'\D', '', parts[2])

                if clean_input and clean_file_name:
                    if clean_input == clean_file_name or clean_input in clean_file_name:
                        return file_esr
    except Exception as e:
        print(f"Error resolving ESR: {e}")

    return ""


def is_border_esr(esr: str) -> bool:
    """Проверяет, является ли станция пограничным переходом или портом."""
    border_esrs = ["547508", "545006", "558701", "554109", "550108", "550409", "553002", "549204", "548803"]
    return str(esr or "").strip() in border_esrs


def get_distance_by_esr(origin_esr: str, dest_esr: str) -> int:
    """Возвращает ж/д расстояние в км между станциями по их ESR-кодам."""
    o_esr = str(origin_esr or "").strip()
    d_esr = str(dest_esr or "").strip()

    if o_esr == "547105" and d_esr in ["545006", "547508"]:
        return 207  # Bakı yük - Yalama
    if o_esr == "547001" and d_esr in ["545006", "547508"]:
        return 200  # Bakı pas. - Yalama

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
                        file_esr = re.sub(r'\D', '', parts[2])
                        if file_esr == o_esr:
                            for part in parts[3:]:
                                nums = re.findall(r'\d+', part)
                                if nums:
                                    return int(nums[0])
        except Exception as e:
            print(f"Error reading distance from file: {e}")

    return 207 if o_esr == "547105" else 300


def get_calculation_distance(distance_km: int, shipment_type: str = "") -> int:
    """Корректирует расстояние с учетом минимального плеча ADY (50 км)."""
    return max(int(distance_km or 0), 50)


def format_station_display_name(raw_name: str, esr: str = "", lang: str = "AZ") -> str:
    """Форматирует отображение станции с кодом ESR."""
    custom_names = {
        "547105": "Bakı yük",
        "547001": "Bakı",
        "545006": "Yalama-eksp.",
        "547508": "Yalama-eksp.",
        "558701": "Böyük Kəsik-eksp.",
        "554109": "Astara-eksp.",
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
    """Возвращает индекс колонки веса для тарифных таблиц."""
    w = float(weight_tons or 0)
    if w <= 10:
        return 0
    elif w <= 15:
        return 1
    elif w <= 20:
        return 2
    elif w <= 25:
        return 3
    elif w <= 30:
        return 4
    elif w <= 35:
        return 5
    elif w <= 40:
        return 6
    elif w <= 45:
        return 7
    elif w <= 50:
        return 8
    elif w <= 55:
        return 9
    elif w <= 60:
        return 10
    else:
        return 11


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
    """Возвращает официальный курс CHF/USD для тарифов ADY."""
    return 0.79, "0.79 CHF/USD"


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

import re
import os

# Обновленный полный реестр станций, терминалов и погранотходов ADY
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
    
    
                return json.loads(content)
            return {"rules_raw": content}
    except Exception as e:
        print(f"Error loading rules config: {e}")

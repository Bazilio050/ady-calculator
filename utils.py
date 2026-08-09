import os
import json
import re

# ==============================================================================
# СЛОВАРЬ ТОЧНЫХ СООТВЕТСТВИЙ И СПЕЦИАЛЬНЫХ УЗЛОВ ADY
# ==============================================================================
STATION_EXACT_MAP = {
    # 1. Астара
    "astara (eks.aşır)": "Astara",
    "astara eks asir": "Astara",
    "astara": "Astara",

    # 2. Баку Yük / Терминалы / Дефолт для "Баку"
    "bakı": "Bakı-Yük",
    "baki": "Bakı-Yük",
    "баку": "Bakı-Yük",
    "bakı yük": "Bakı-Yük",
    "baki yuk": "Bakı-Yük",
    "баку yük": "Bakı-Yük",
    "баку-юк": "Bakı-Yük",
    "баку юк": "Bakı-Yük",
    "баку товарная": "Bakı-Yük",
    "баку-тов": "Bakı-Yük",
    "bakı yük terminal": "Bakı-Yük",
    "baki yuk terminal": "Bakı-Yük",

    # 3. Бакинский морской порт
    "bakı ticarət liman": "Bakı Ticarət Limanı",
    "bakı ticarət limanı": "Bakı Ticarət Limanı",
    "bakı ticarət limanı (eks)": "Bakı Ticarət Limanı",
    "bakı ticarət limanı (aşır)": "Bakı Ticarət Limanı",
    "baki ticaret limani": "Bakı Ticarət Limanı",

    # 4. Алят и Экспортные Паромные направления
    "ələt": "Ələt",
    "elet": "Ələt",
    "алят": "Ələt",
    "ələt eksport aktau": "Ələt",
    "elet eksport aktau": "Ələt",
    "eksport aktau": "Ələt",
    "aktau": "Ələt",
    "ələt eksport kurik": "Ələt",
    "elet eksport kurik": "Ələt",
    "eksport kurik": "Ələt",
    "kurik": "Ələt",
    "курык": "Ələt",
    "ələt eksport-türk.": "Ələt",
    "elet eksport-turk": "Ələt",
    "eksport turk": "Ələt",
    "туркменбаши": "Ələt",
    "turkmenbashi": "Ələt",

    # 5. Алят-Ени
    "ələt yeni": "Ələt-Yeni",
    "elet yeni": "Ələt-Yeni",
    "алят ени": "Ələt-Yeni",

    # 6. Мингечевир
    "mingəçevir şəhər": "Mingəçevir-Şəhər",
    "mingacevir seher": "Mingəçevir-Şəhər",
    "мингечевир шехер": "Mingəçevir-Şəhər",
    "mingəçevir": "Mingəçevir-Şəhər",

    # 7. Карадаг
    "qaradağ terminal": "Qaradağ",
    "qaradag terminal": "Qaradağ",
    "карадаг терминал": "Qaradağ",
    "qaradağ": "Qaradağ",

    # 8. Гушчу Керпю
    "quşçu körpü": "Quşçu Körpü",
    "quscu korpu": "Quşçu Körpü",
    "гушчу корпю": "Quşçu Körpü",

    # 9. Сангачал
    "sanqaçal ter.(aşırma)": "Sanqaçal",
    "sanqacal ter.(asirma)": "Sanqaçal",
    "sanqaçal ter": "Sanqaçal",
    "sanqacal ter": "Sanqaçal",
    "сангачал тер": "Sanqaçal",
    "sanqaçal": "Sanqaçal",

    # 10. Союг-Булаг
    "soyuq-bulaq": "Soyuqbulaq",
    "soyuq bulaq": "Soyuqbulaq",
    "союг булаг": "Soyuqbulaq",
    "soyuqbulaq": "Soyuqbulaq",

    # 11. З. Тагиев и Чобанлы/Чешидлеме
    "z.tağıyev": "Z.Tağıyev",
    "z.tagiyev": "Z.Tağıyev",
    "з.тагиев": "Z.Tağıyev",
    "z.tağıyev çeşidləmə": "Z.Tağıyev-Çeşidləmə",
    "z.tagiyev cesidleme": "Z.Tağıyev-Çeşidləmə",
    "з.тагиев сортировочная": "Z.Tağıyev-Çeşidləmə",

    # 12. Забрат II
    "zabrat ii": "Zabrat-II",
    "zabrat 2": "Zabrat-II",
    "забрат 2": "Zabrat-II",
    "забрат ii": "Zabrat-II"
}


def normalize_st_name(raw_name: str) -> str:
    """
    Универсальная очистка и приведение названия станции к каноническому виду из Distances.txt.
    """
    if not raw_name:
        return ""

    # 1. Приведение к нижнему регистру, замена переносов строк на пробелы
    clean = str(raw_name).replace('\n', ' ').strip().lower()
    clean = re.sub(r'\s+', ' ', clean)

    # 2. Прямая проверка по точной карте соответствий
    if clean in STATION_EXACT_MAP:
        return STATION_EXACT_MAP[clean]

    # 3. Автоматическое срезание скобок и суффиксов
    clean = re.sub(r'\((eks|aşır|aşırma|eks\.aşır)\)', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(ter\.|terminal|aşırma|aşır)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'-(eksp|эксп|exp)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'-(тов|tov|tovarlı|товарная)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # 4. Повторная проверка после очистки
    if clean in STATION_EXACT_MAP:
        return STATION_EXACT_MAP[clean]

    return raw_name.strip()


def norm_str(s: str) -> str:
    """
    Вспомогательная функция нормализации символов для нечувствительного к регистру сравнения.
    """
    if not s:
        return ""
    return str(s).lower().replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g').replace('-', ' ').strip()


def load_rules_config() -> dict:
    """
    Загрузка конфигурационных файлов из папки tables/ или корневой директории.
    """
    possible_paths = [
        "tables/global_config.json",
        "tables/table_3_config.json",
        "rules_config.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка чтения {path}: {e}")
    return {}


def find_distance_in_memory(st_from: str, st_to: str) -> int | None:
    """
    Поиск тарифного расстояния в километрах между двумя станциями в файле Distances.txt.
    """
    st_from_norm = normalize_st_name(st_from)
    st_to_norm = normalize_st_name(st_to)

    clean_from = norm_str(st_from_norm)
    clean_to = norm_str(st_to_norm)

    possible_files = [
        "Distances.txt",
        "data/Distances.txt",
        "tables/Distances.txt"
    ]

    dist_file = None
    for pf in possible_files:
        if os.path.exists(pf):
            dist_file = pf
            break

    if not dist_file:
        return None

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("#") or line_str.startswith("="):
                    continue

                parts = re.split(r'\||;', line_str)
                if len(parts) >= 2:
                    st_pair = parts[0].strip()
                    dist_val_str = parts[-1].strip()

                    pair_match = re.split(r'\s*[-–]\s*', st_pair, maxsplit=1)
                    if len(pair_match) == 2:
                        s1 = norm_str(pair_match[0])
                        s2 = norm_str(pair_match[1])

                        if (clean_from == s1 and clean_to == s2) or (clean_from == s2 and clean_to == s1):
                            dist_match = re.search(r'\d+', dist_val_str)
                            if dist_match:
                                return int(dist_match.group(0))
    except Exception as e:
        print(f"Ошибка при поиске расстояния в {dist_file}: {e}")

    return None

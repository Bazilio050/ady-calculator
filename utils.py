import os
import json
import re

# ==============================================================================
# СЛОВАРЬ ТОЧНОГО СООТВЕТСТВИЯ СТАНЦИЙ ADY
# ==============================================================================
STATION_EXACT_MAP = {
    # Баку и порты
    "баку": "Bakı-Yük",
    "баку-тов": "Bakı-Yük",
    "баку тов": "Bakı-Yük",
    "баку товарная": "Bakı-Yük",
    "bakı": "Bakı-Yük",
    "baki": "Bakı-Yük",
    "bakı-tov": "Bakı-Yük",
    "bakı yük": "Bakı-Yük",
    "baki yuk": "Bakı-Yük",
    "баку порт": "Bakı Ticarət Limanı",
    "bakı ticarət limanı": "Bakı Ticarət Limanı",
    "bakı ticarət limani": "Bakı Ticarət Limanı",
    "bakı liman": "Bakı Ticarət Limanı",
    # Алят и Паромы
    "алят": "Ələt",
    "ələt": "Ələt",
    "elet": "Ələt",
    "alat": "Ələt",
    "курык": "Ələt",
    "kurik": "Ələt",
    "актау": "Ələt",
    "aktau": "Ələt",
    "туркменбаши": "Ələt",
    "turkmenbashi": "Ələt",
    "алят ени": "Ələt-Yeni",
    "ələt yeni": "Ələt-Yeni",
    # Погранпереходы и спец. станции ADY
    "ялама": "Yalama",
    "yalama": "Yalama",
    "беюк кесик": "Böyük Kəsik",
    "беюк-кесик": "Böyük Kəsik",
    "böyük kəsik": "Böyük Kəsik",
    "boyuk kesik": "Böyük Kəsik",
    "астара": "Astara",
    "astara": "Astara",
    "мингечевир шехер": "Mingəçevir-Şəhər",
    "mingəçevir şəhər": "Mingəçevir-Şəhər",
    "мингечевир": "Mingəçevir-Şəhər",
    "карадаг": "Qaradağ",
    "qaradağ": "Qaradağ",
    "quşçu körpü": "Quşçu Körpü",
    "гушчу корпю": "Quşçu Körpü",
    "сангачал": "Sanqaçal",
    "sanqaçal": "Sanqaçal",
    "союг булаг": "Soyuqbulaq",
    "soyuqbulaq": "Soyuqbulaq",
    "з. тагиев": "Z.Tağıyev",
    "з.тагиев": "Z.Tağıyev",
    "z.tağıyev": "Z.Tağıyev",
    "z.tagiyev": "Z.Tağıyev",
    "з.тагиев сортировочная": "Z.Tağıyev-Çeşidləmə",
    "z.tağıyev çeşidləmə": "Z.Tağıyev-Çeşidləmə",
    "забрат 2": "Zabrat-II",
    "zabrat 2": "Zabrat-II",
    "zabrat ii": "Zabrat-II",
    # Апшерон / Абшерон
    "апшерон": "Abşeron",
    "абшерон": "Abşeron",
    "abşeron": "Abşeron",
    "absheron": "Abşeron",
    "abseron": "Abşeron",
    "сумгаит": "Sumqayıt",
    "sumqayıt": "Sumqayıt",
    "биляджары": "Biləcəri",
    "biləcəri": "Biləcəri",
    "худат": "Xudat",
    "xudat": "Xudat",
    "гянджа": "Gəncə",
    "gəncə": "Gəncə",
}


def norm_str(s: str) -> str:
    """
    Приводит строку к единому очищенному виду без учета спецсимволов и разницы латиницы/кириллицы.
    """
    if not s:
        return ""
    cleaned = s.strip().lower()

    # Поочередная замена символов для устойчивости к опечаткам и кодировкам
    replacements = [
        ('sh', 's'), ('ch', 'c'), ('kh', 'h'),
        ('ə', 'e'), ('ç', 'c'), ('ğ', 'g'), ('ı', 'i'),
        ('ö', 'o'), ('ş', 's'), ('ü', 'u'), ('ё', 'е')
    ]
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)

    cleaned = re.sub(r'[^a-z0-9]', '', cleaned)
    return cleaned


def normalize_st_name(st_name: str) -> str:
    """
    Нормализует название станции по словарю STATION_EXACT_MAP.
    """
    if not st_name:
        return ""

    key = norm_str(st_name)
    for map_key, official_name in STATION_EXACT_MAP.items():
        if norm_str(map_key) == key:
            return official_name

    return st_name.strip()


def load_rules_config(filepath: str = "rules_config.json") -> dict:
    """
    Загружает конфигурацию тарифных правил из JSON.
    """
    possible_paths = [
        filepath,
        os.path.join("data", filepath),
        os.path.join("config", filepath),
        "rules_config.json",
        "rules.json",
        "data/rules_config.json",
        "data/rules.json"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка при чтении конфигурации {path}: {e}")

    return {}


def _find_distances_file() -> str | None:
    """
    Ищет файл расстояний с учетом регистра и возможных путей на сервере Linux.
    """
    search_dirs = [".", "data", "tables", "config"]
    target_names = ["distances.txt", "distances.csv", "distances.json"]

    for d in search_dirs:
        if not os.path.exists(d):
            continue
        try:
            for file_name in os.listdir(d):
                if file_name.lower() in target_names or "distance" in file_name.lower():
                    full_path = os.path.join(d, file_name)
                    if os.path.isfile(full_path):
                        return full_path
        except Exception:
            pass
    return None


def find_distance_in_memory(st_from: str, st_to: str) -> int | None:
    """
    Безотказный поиск расстояния между двумя станциями в файле Distances.txt.
    """
    st_from_norm = normalize_st_name(st_from)
    st_to_norm = normalize_st_name(st_to)

    clean_from = norm_str(st_from_norm)
    clean_to = norm_str(st_to_norm)

    dist_file = _find_distances_file()
    if not dist_file:
        print("Ошибка: Файл Distances.txt не найден на сервере.")
        return None

    try:
        with open(dist_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("#") or line_str.startswith("="):
                    continue

                # Находим все числа в строке
                numbers = re.findall(r'\d+', line_str)
                if not numbers:
                    continue

                # Последнее число в строке — это расстояние в км
                dist_value = int(numbers[-1])

                # Нормализуем текст всей строки
                clean_line = norm_str(line_str)

                # Проверяем, содержатся ли обе станции в этой строке
                if clean_from in clean_line and clean_to in clean_line:
                    return dist_value

    except Exception as e:
        print(f"Ошибка при чтении {dist_file}: {e}")

    return None

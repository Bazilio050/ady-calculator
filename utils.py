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
    Приводит строку к единому виду с заменой специфических букв (латиница/кириллица),
    чтобы убрать чувствительность к написанию (например, ş -> s, ə -> e).
    """
    if not s:
        return ""
    cleaned = s.strip().lower()

    replacements = {
        'ə': 'e', 'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'ё': 'е', 'sh': 's', 'ch': 'c', 'kh': 'h'
    }
    for old, new in replacements.items():
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
    Загружает конфигурацию тарифных правил и коэффициентов из JSON.
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


def find_distance_in_memory(st_from: str, st_to: str) -> int | None:
    """
    Безотказный поиск расстояния между двумя станциями в файле Distances.txt.
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

                # 1. Извлекаем числовое значение расстояния
                dist_match = re.search(r'(\d+)\s*$', line_str)
                if not dist_match:
                    dist_match = re.search(r'[:|;\t]\s*(\d+)', line_str)

                if not dist_match:
                    continue

                dist_value = int(dist_match.group(1))

                # 2. Берем текстовую часть строки со станциями
                st_part = line_str[:dist_match.start()].strip()
                clean_st_part = norm_str(st_part)

                # 3. Прямое совпадение: обе станции присутствуют в этой строке
                if clean_from in clean_st_part and clean_to in clean_st_part:
                    return dist_value

                # 4. Резервная проверка через разделение по токенам
                tokens = re.split(r'\s+[-–—]\s+|\s*[-–—]\s*|\s*;\s*|\s*\|\s*|\t+', st_part)
                if len(tokens) >= 2:
                    s1 = norm_str(normalize_st_name(tokens[0]))
                    s2 = norm_str(normalize_st_name(tokens[1]))
                    if (clean_from == s1 and clean_to == s2) or (clean_from == s2 and clean_to == s1):
                        return dist_value
    except Exception as e:
        print(f"Ошибка при поиске расстояния в {dist_file}: {e}")

    return None

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
    Очистка и приведение строки к нижнему регистру для корректного сравнения.
    """
    if not s:
        return ""
    cleaned = s.strip().lower()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned


def normalize_st_name(st_name: str) -> str:
    """
    Нормализует название станции по словарю STATION_EXACT_MAP.
    """
    if not st_name:
        return ""

    key = norm_str(st_name)
    if key in STATION_EXACT_MAP:
        return STATION_EXACT_MAP[key]

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

                parts = re.split(r'\||;|\:', line_str)
                if len(parts) >= 2:
                    st_pair = parts[0].strip()
                    dist_val_str = parts[-1].strip()

                    pair_match = re.split(r'\s+[-–—]\s+|\s*;\s*', st_pair, maxsplit=1)
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

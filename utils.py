import os
import json
import re

# ==============================================================================
# СЛОВАРЬ СИНОНИМОВ И НОРМАЛИЗАЦИИ СТАНЦИЙ ADY
# ==============================================================================
STATION_ALIASES = {
    # Апшерон / Абшерон
    "апшерон": "abşeron",
    "абшерон": "abşeron",
    "absheron": "abşeron",
    "abseron": "abşeron",
    # Баку
    "баку": "bakı-yük",
    "баку-тов": "bakı-yük",
    "баку тов": "bakı-yük",
    "баку товарная": "bakı-yük",
    "bakı": "bakı-yük",
    "baki": "bakı-yük",
    "bakı-tov": "bakı-yük",
    "bakı yük": "bakı-yük",
    "baki yuk": "bakı-yük",
    # Порт
    "баку порт": "bakı ticarət limanı",
    "bakı ticarət limanı": "bakı ticarət limanı",
    "bakı ticarət limani": "bakı ticarət limanı",
    # Алят и паромы
    "алят": "ələt",
    "elet": "ələt",
    "alat": "ələt",
    "курык": "ələt",
    "kurik": "ələt",
    "актау": "ələt",
    "aktau": "ələt",
    # Прочие станции
    "ялама": "yalama",
    "беюк кесик": "böyük kəsik",
    "беюк-кесик": "böyük kəsik",
    "boyuk kesik": "böyük kəsik",
    "астара": "astara",
    "мингечевир": "mingəçevir-şəhər",
    "з.тагиев": "z.tağıyev",
    "з. тагиев": "z.tağıyev"
}


def load_rules_config():
    """
    Автоматически собирает глобальный конфиг и специфичные правила таблиц 
    из отдельных JSON-файлов в единый словарь в памяти.
    """
    config = {}

    config_files = [
        "config/global_config.json",
        "tables/table_3_config.json",
        "tables/table_4_config.json",
        "tables/table_5_config.json"
    ]

    for file_path in config_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for key, val in data.items():
                            if key in config and isinstance(config[key], dict) and isinstance(val, dict):
                                config[key].update(val)
                            else:
                                config[key] = val
            except Exception as e:
                print(f"Ошибка загрузки файла {file_path}: {e}")

    if not config and os.path.exists("rules_config.json"):
        try:
            with open("rules_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки rules_config.json: {e}")

    return config


def normalize_st_name(name):
    """
    Нормализует название станции для точного сопоставления.
    """
    if not name:
        return ""
    cleaned = re.sub(r'-(eksp|эксп|exp)\b', '', str(name), flags=re.IGNORECASE)
    cleaned = re.sub(r'[^\w\s\-]', '', cleaned)
    cleaned = cleaned.strip().lower()
    return STATION_ALIASES.get(cleaned, cleaned)


def find_distance_in_memory(st_from, st_to):
    """
    Точный матричный поиск расстояния в Distances.txt.
    Учитывает приоритет экспортных станций (например, Böyük Kəsik (eksport) = 680 km).
    """
    if not st_from or not st_to:
        return None

    def clean_name(s):
        s = str(s).replace('*', '')
        s = re.sub(r'-(eksp|эксп|exp)\b', '', s, flags=re.IGNORECASE)
        s = re.sub(r'\b(eksport|aşırma|terminal|şəhər)\b', '', s, flags=re.IGNORECASE)
        s = s.strip().lower()
        return STATION_ALIASES.get(s, s)

    norm_from = clean_name(st_from)
    norm_to = clean_name(st_to)

    possible_paths = ["Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = None
    for p in possible_paths:
        if os.path.exists(p):
            dist_file = p
            break

    if not dist_file:
        return None

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        header_cols = []
        header_idx = -1
        for idx, line in enumerate(lines):
            if "|" in line and any(k in line.lower() for k in ["yalama", "astara", "kəsik", "kesik", "culfa", "ələt", "alat"]):
                parts = [clean_name(p) for p in line.split("|")]
                header_cols = [p for p in parts if p]
                header_idx = idx
                break

        if header_idx == -1:
            return None

        matched_distance = None

        for line in lines[header_idx + 1:]:
            if "|" not in line or ":---" in line:
                continue

            parts = [clean_name(p) for p in line.split("|") if p.strip() != ""]
            if len(parts) < 3:
                continue

            raw_row_st = line.split("|")[1].replace('*', '').strip() if line.split("|")[1].strip() != "" else ""
            row_st_name = clean_name(raw_row_st)

            target_border_st = None
            if norm_from == row_st_name or norm_from in row_st_name or row_st_name in norm_from:
                target_border_st = norm_to
            elif norm_to == row_st_name or norm_to in row_st_name or row_st_name in norm_to:
                target_border_st = norm_from

            if target_border_st:
                for col_idx, hdr in enumerate(header_cols):
                    if hdr and (target_border_st in hdr or hdr in target_border_st):
                        if col_idx < len(parts):
                            val_str = re.sub(r'\D', '', parts[col_idx])
                            if val_str:
                                dist_val = int(val_str)
                                if "eksport" in raw_row_st.lower() or "eks" in raw_row_st.lower():
                                    return dist_val
                                matched_distance = dist_val

        return matched_distance

    except Exception as e:
        print(f"Ошибка при чтении {dist_file}: {e}")

    return None

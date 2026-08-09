import os
import json
import re


def load_rules_config():
    """
    Автоматически собирает глобальный конфиг и специфичные правила таблиц 
    из отдельных JSON-файлов в единый словарь в памяти.
    """
    config = {}

    # Пути к нашим файлам конфигураций
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
                        # Глубокое обновление/объединение ключей
                        for key, val in data.items():
                            if key in config and isinstance(config[key], dict) and isinstance(val, dict):
                                config[key].update(val)
                            else:
                                config[key] = val
            except Exception as e:
                print(f"Ошибка загрузки файла {file_path}: {e}")

    # Резервный вариант: если новые файлы еще не найдены, читаем старый файл
    if not config and os.path.exists("rules_config.json"):
        with open("rules_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

    return config


def normalize_st_name(name):
    """
    Нормализует название станции для точного сопоставления.
    """
    if not name:
        return ""
    cleaned = re.sub(r'-(eksp|эксп|exp)\b', '', str(name), flags=re.IGNORECASE)
    cleaned = re.sub(r'[^\w\s]', '', cleaned)
    return cleaned.strip().lower()


def find_distance_in_memory(st_from, st_to):
    """
    Умный поиск расстояния в матричном формате Distances.txt.
    Ищет пересечение строки станции и столбца погранперехода.
    """
    if not st_from or not st_to:
        return None

    norm_from = normalize_st_name(st_from)
    norm_to = normalize_st_name(st_to)

    dist_file = "Distances.txt"
    if not os.path.exists(dist_file):
        return None

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            return None

        # 1. Находим строку заголовка с пограничными станциями
        header_col_names = []
        header_line_idx = -1
        for idx, line in enumerate(lines):
            if "|" in line and any(k in line.lower() for k in ["yalama", "astara", "kəsik", "kesik", "culfa", "ələt", "alat"]):
                parts = [p.strip() for p in line.split("|")]
                header_col_names = [normalize_st_name(p) for p in parts]
                header_line_idx = idx
                break

        if header_line_idx == -1:
            return None

        # 2. Ищем совпадение в строках станций
        for line in lines[header_line_idx + 1:]:
            if "|" not in line or "---" in line:
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                continue

            row_st_name = normalize_st_name(parts[0])

            # Определяем, какая из станций находится в строке, а какая — в заголовке столбца
            target_border_st = None
            if norm_from == row_st_name or norm_from in row_st_name or row_st_name in norm_from:
                target_border_st = norm_to
            elif norm_to == row_st_name or norm_to in row_st_name or row_st_name in norm_to:
                target_border_st = norm_from

            if target_border_st:
                # Ищем заголовок нужного столбца
                for col_idx, border_hdr in enumerate(header_col_names):
                    if border_hdr and (target_border_st in border_hdr or border_hdr in target_border_st):
                        if col_idx < len(parts):
                            val_str = parts[col_idx].strip()
                            digits = re.sub(r'\D', '', val_str)
                            if digits:
                                return int(digits)

    except Exception as e:
        print(f"Ошибка при чтении матричного {dist_file}: {e}")

    return None

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
    Находит тарифное расстояние между станциями из файла Distances.txt.
    """
    if not st_from or not st_to:
        return None

    norm_from = normalize_st_name(st_from)
    norm_to = normalize_st_name(st_to)

    dist_file = "Distances.txt"
    if os.path.exists(dist_file):
        try:
            with open(dist_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "|" not in line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        s1 = normalize_st_name(parts[0])
                        s2 = normalize_st_name(parts[1])
                        
                        if (s1 == norm_from and s2 == norm_to) or (s1 == norm_to and s2 == norm_from):
                            try:
                                return int(parts[2])
                            except ValueError:
                                pass
        except Exception as e:
            print(f"Ошибка при чтении {dist_file}: {e}")

    return None

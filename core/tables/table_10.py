# core/tables/table_10.py

import os
from typing import Dict, Any, Tuple

class Table10Calculator:
    """Вычислитель тарифных ставок Таблицы 10 с динамическим парсингом Table_10_Tariffs.txt"""

    _data_cache: Dict[Tuple[int, int], Dict[str, float]] = {}

    @classmethod
    def _load_data_if_needed(cls):
        """Парсит текстовый файл Таблицы 10 при первом обращении."""
        if cls._data_cache:
            return

        file_path = os.path.join("data", "Table_10_Tariffs.txt")
        if not os.path.exists(file_path):
            file_path = "Table_10_Tariffs.txt"

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("| **"):
                    continue

                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) < 11:
                    continue

                # Извлечение диапазона км (например: "**1-10 km**" -> 1, 10)
                dist_str = parts[0].replace("*", "").replace("km", "").strip()
                if "-" not in dist_str:
                    continue
                
                min_km, max_km = map(int, dist_str.split("-"))

                # Маппинг колонок по порядку из файла
                cls._data_cache[(min_km, max_km)] = {
                    "tank_20_loaded": float(parts[1]),
                    "tank_20_empty": float(parts[2]),
                    "tank_40_loaded": float(parts[3]),
                    "tank_40_empty": float(parts[4]),
                    "wine_20": float(parts[5]),
                    "wine_40": float(parts[6]),
                    "ref_20_loaded": float(parts[7]),
                    "ref_20_empty": float(parts[8]),
                    "ref_40_loaded": float(parts[9]),
                    "ref_40_empty": float(parts[10]),
                }

    @classmethod
    def get_base_rate(
        cls,
        distance_km: float,
        container_type: str,
        feet_size: int = 20,
        is_empty: bool = False
    ) -> Dict[str, Any]:
        """Возвращает базовую ставку в CHF, прочитанную из файла Таблицы 10."""
        cls._load_data_if_needed()

        dist = int(distance_km)
        matched_rates = None
        for (min_km, max_km), rates in cls._data_cache.items():
            if min_km <= dist <= max_km:
                matched_rates = rates
                break

        if not matched_rates and cls._data_cache:
            # Свыше 1000 км берем максимальный интервал
            max_range = max(cls._data_cache.keys(), key=lambda x: x[1])
            matched_rates = cls._data_cache[max_range]

        state_str = "empty" if is_empty else "loaded"
        if container_type in ("wine", "wine_juice"):
            col_key = f"wine_{feet_size}"
        elif container_type == "ref":
            col_key = f"ref_{feet_size}_{state_str}"
        else:
            col_key = f"tank_{feet_size}_{state_str}"

        base_rate = matched_rates.get(col_key, 0.0) if matched_rates else 0.0

        return {
            "base_rate": base_rate,
            "column_key": col_key,
            "applied_rules": [{
                "rule_code": "SPECIAL_CONTAINER_TANK_REF_RULE_3_4_3_1",
                "calculated_value": 1.0,
                "params": {
                    "container_type": container_type,
                    "feet_size": feet_size,
                    "is_empty": is_empty
                }
            }]
        }

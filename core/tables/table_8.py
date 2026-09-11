import os
from typing import Dict, Any, Tuple


class Table8Calculator:
    """Вычислитель тарифных ставок Таблицы 8 (Универсальные контейнеры)"""

    _data_cache: Dict[Tuple[int, int], Dict[str, float]] = {}

    @classmethod
    def _load_data_if_needed(cls):
        """Парсит текстовый файл Таблицы 8 при первом обращении."""
        if cls._data_cache:
            return

        file_path = os.path.join("data", "Table_8_Tariffs.txt")
        if not os.path.exists(file_path):
            file_path = "Table_8_Tariffs.txt"

        if not os.path.exists(file_path):
            return

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("Məsafə"):
                    continue

                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) < 15:
                    continue

                dist_str = parts[0]
                if "-" not in dist_str:
                    continue

                min_km, max_km = map(int, dist_str.split("-"))
                cls._data_cache[(min_km, max_km)] = {
                    "mid_3t_loaded": float(parts[1]),
                    "mid_5t_loaded": float(parts[2]),
                    "mid_3t_empty": float(parts[3]),
                    "mid_5t_empty": float(parts[4]),
                    "inv_10ft_loaded": float(parts[5]),
                    "inv_20ft_loaded": float(parts[6]),
                    "inv_30ft_loaded": float(parts[7]),
                    "inv_40ft_loaded": float(parts[8]),
                    "inv_45ft_loaded": float(parts[9]),
                    "ozel_10ft_empty": float(parts[10]),
                    "ozel_20ft_empty": float(parts[11]),
                    "ozel_30ft_empty": float(parts[12]),
                    "ozel_40ft_empty": float(parts[13]),
                    "ozel_45ft_empty": float(parts[14]),
                }

    @classmethod
    def get_base_rate(
        cls,
        distance_km: float,
        feet_size: int = 20,
        is_empty: bool = False,
        is_private: bool = True,
        is_generator_container: bool = False,
        is_container_platform: bool = False,
        is_open_top_container: bool = False
    ) -> Dict[str, Any]:
        """Возвращает базовую ставку в CHF по Таблице 8."""
        cls._load_data_if_needed()
        dist = int(distance_km)
        applied_rules = []

        matched_rates = None
        for (min_km, max_km), rates in cls._data_cache.items():
            if min_km <= dist <= max_km:
                matched_rates = rates
                break

        if not matched_rates and cls._data_cache:
            max_range = max(cls._data_cache.keys(), key=lambda x: x[1])
            matched_rates = cls._data_cache[max_range]

        if is_empty:
            prefix = "ozel" if is_private else "inv"
            col_key = f"{prefix}_{feet_size}ft_empty"
        else:
            col_key = f"inv_{feet_size}ft_loaded"

        base_rate = matched_rates.get(col_key, 0.0) if matched_rates else 0.0

        # П. 3.4.5: Коэффициент 1.35 за контейнер-дизель-генератор
        if is_generator_container:
            base_rate = round(base_rate * 1.35, 2)
            applied_rules.append({
                "rule_code": "DIESEL_GENERATOR_CONTAINER_COEFF_1_35",
                "calculated_value": 1.35,
                "params": {}
            })
        # П. 3.4.6: Коэффициент 1.40 за контейнеры-платформы (Flatrack)
        elif is_container_platform:
            base_rate = round(base_rate * 1.40, 2)
            applied_rules.append({
                "rule_code": "CONTAINER_PLATFORM_COEFF_1_40",
                "calculated_value": 1.40,
                "params": {}
            })
        # П. 3.4.7: Коэффициент 1.40 за открытые контейнеры (Open Top)
        elif is_open_top_container:
            base_rate = round(base_rate * 1.40, 2)
            applied_rules.append({
                "rule_code": "OPEN_TOP_CONTAINER_COEFF_1_40",
                "calculated_value": 1.40,
                "params": {}
            })

        return {
            "base_rate": base_rate,
            "column_key": col_key,
            "applied_rules": applied_rules
        }

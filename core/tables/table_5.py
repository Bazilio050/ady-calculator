# core/tables/table_5.py

import os
from typing import Dict, Tuple, Optional


class Table5Calculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Считывает тарифные ставки Таблицы 5 из файла data/Table_5_Tariffs.txt 
    и вычисляет базовую ставку для специализированного подвижного состава (СПС).
    """

    DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Table_5_Tariffs.txt")

    _rates_cache: Optional[Dict[Tuple[int, int], Dict[str, float]]] = None

    @classmethod
    def _parse_distance_range(cls, raw_dist: str) -> Tuple[int, int]:
        """Разбирает строку диапазона '1-10' в кортеж (1, 10)."""
        parts = raw_dist.strip().split("-")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        raise ValueError(f"Некорректный формат диапазона расстояний в Таблице 5: {raw_dist}")

    @classmethod
    def _load_data(cls) -> Dict[Tuple[int, int], Dict[str, float]]:
        """Считывает и кэширует данные из Table_5_Tariffs.txt один раз."""
        if cls._rates_cache is not None:
            return cls._rates_cache

        file_path = os.path.abspath(cls.DATA_FILE_PATH)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл Таблицы 5 не найден по пути: {file_path}")

        tariffs: Dict[Tuple[int, int], Dict[str, float]] = {}

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("#") or line_str.startswith("=") or "Məsafə" in line_str or "Колонки:" in line_str:
                    continue

                parts = [p.strip() for p in line_str.split("|")]
                if len(parts) < 8:
                    continue

                try:
                    dist_range = cls._parse_distance_range(parts[0])
                    tariffs[dist_range] = {
                        "col_2": float(parts[1]),  # Рефрижераторы <25т (за вагон)
                        "col_3": float(parts[2]),  # Рефрижераторы >=25т (за 1т)
                        "col_4": float(parts[3]),  # Термосы/ледники <25т (за вагон)
                        "col_5": float(parts[4]),  # Термосы/ледники >=25т (за 1т)
                        "col_6": float(parts[5]),  # Автовозы >=10т (за 1т)
                        "col_7": float(parts[6]),  # ИНВ / АНВ груженый (за 1т)
                        "col_8": float(parts[7]),  # ИНВ / АНВ порожний (за вагон)
                    }
                except (ValueError, IndexError):
                    continue

        cls._rates_cache = tariffs
        return cls._rates_cache

    @classmethod
    def get_base_rate(
        cls,
        distance_km: float,
        weight_tons: float = 0.0,
        equipment_type: str = "refrigerator",
        is_empty: bool = False,
        ref_section_wagons_count: Optional[int] = None
    ) -> float:
        """
        Возвращает базовую ставку в CHF по Таблице 5.
        Учитывает коэффициенты количества вагонов в рефсекции (1+1 -> 1.7, 2+1 -> 1.4, 3+1 -> 1.1, 4+1 -> 1.0, 5+1/6+1 -> 0.85).
        """
        tariffs = cls._load_data()
        dist = int(round(distance_km))

        matched_rates = None
        for (min_dist, max_dist), rates in tariffs.items():
            if min_dist <= dist <= max_dist:
                matched_rates = rates
                break

        if matched_rates is None:
            raise ValueError(f"Расстояние {dist} км выходит за пределы Таблицы 5.")

        eq_lower = equipment_type.lower()

        # 1. Рефрижераторы и ARV
        if eq_lower in ("refrigerator", "arv", "ref_section"):
            if weight_tons < 25.0:
                base_rate = matched_rates["col_2"]
            else:
                base_rate = matched_rates["col_3"]

            # Применение коэффициента от количества вагонов в рефсекции (п. 3.1.2.1)
            if ref_section_wagons_count is not None:
                if ref_section_wagons_count == 1:
                    base_rate *= 1.7
                elif ref_section_wagons_count == 2:
                    base_rate *= 1.4
                elif ref_section_wagons_count == 3:
                    base_rate *= 1.1
                elif ref_section_wagons_count >= 5:
                    base_rate *= 0.85

            return base_rate

        # 2. Вагоны-термосы и ледники
        elif eq_lower in ("thermos", "ice_wagon"):
            if weight_tons < 25.0:
                return matched_rates["col_4"]
            else:
                return matched_rates["col_5"]

        # 3. Автовозы (Колонка 6: За 1 тонну)
        elif eq_lower == "car_carrier":
            return matched_rates["col_6"]

        # 4. ИНВ / АНВ
        elif eq_lower in ("inv", "anv", "inv_anv"):
            if is_empty:
                return matched_rates["col_8"]
            else:
                return matched_rates["col_7"]

        else:
            raise ValueError(f"Неизвестный тип подвижного состава для Таблицы 5: {equipment_type}")

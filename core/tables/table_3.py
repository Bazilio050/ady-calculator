# core/tables/table_3.py

import os
from typing import Dict, Tuple, List


class Table3Calculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Считывает тарифные ставки Таблицы 3 из файла data/Table_3_Tariffs.txt 
    и находит базовую ставку за 1 тонну в CHF.
    """

    # Динамический путь к файлу с данными Таблицы 3
    DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Table_3_Tariffs.txt")

    # Границы весовых категорий: (мин_вес, макс_вес): индекс_колонки
    WEIGHT_COLUMNS = [
        (0.0, 12.0, 0),    # 10 t (до 12 t)
        (12.01, 16.0, 1),  # 15 t (13-16 t)
        (16.01, 23.0, 2),  # 20 t (17-23 t)
        (23.01, 26.0, 3),  # 25 t (24-26 t)
        (26.01, 31.0, 4),  # 30 t (27-31 t)
        (31.01, 36.0, 5),  # 35 t (32-36 t)
        (36.01, 40.0, 6),  # 40 t (37-40 t)
        (40.01, 46.0, 7),  # 45 t (41-46 t)
        (46.01, 51.0, 8),  # 50 t (47-51 t)
        (51.01, 55.0, 9),  # 55 t (52-55 t)
        (55.01, 999.0, 10) # 60 t (56 t и выше)
    ]

    _rates_data: Dict[Tuple[int, int], List[float]] = {}

    @classmethod
    def _load_data(cls) -> None:
        """Считывает и парсит данные из Table_3_Tariffs.txt один раз."""
        if cls._rates_data:
            return

        file_path = os.path.abspath(cls.DATA_FILE_PATH)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл Таблицы 3 не найден по пути: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("=") or line.startswith("CƏDVƏL") or line.startswith("Universal") or line.startswith("(") or line.startswith("Məsafə"):
                    continue

                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 12:
                    dist_range = parts[0].split("-")
                    min_dist, max_dist = int(dist_range[0]), int(dist_range[1])
                    rates = [float(p) for p in parts[1:]]
                    cls._rates_data[(min_dist, max_dist)] = rates

    @classmethod
    def _get_weight_column_index(cls, weight_tons: float) -> int:
        """Определяет индекс колонки по весу груза."""
        for min_w, max_w, col_idx in cls.WEIGHT_COLUMNS:
            if min_w <= weight_tons <= max_w:
                return col_idx
        return 10

    @classmethod
    def get_base_rate(cls, distance_km: float, weight_tons: float) -> float:
        """
        Возвращает базовую ставку за 1 тонну в CHF из распарсенного файла.
        """
        cls._load_data()
        dist = int(round(distance_km))
        col_idx = cls._get_weight_column_index(weight_tons)

        for (min_d, max_d), rates in cls._rates_data.items():
            if min_d <= dist <= max_d:
                return rates[col_idx]

        raise ValueError(f"Расстояние {dist} км выходит за пределы Таблицы 3 (1-1000 км).")

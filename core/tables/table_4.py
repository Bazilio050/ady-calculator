# core/tables/table_4.py

import os
from typing import Dict, List, Tuple


class Table4Calculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Калькулятор базовых ставок Таблицы 4 (Транзит в универсальных вагонах).
    Считывает тарифную сетку напрямую из файла data/Table_4_Tariffs.txt.
    """

    _rates_cache: Dict[Tuple[int, int], List[float]] = {}
    _weight_columns: List[int] = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

    @classmethod
    def _load_rates_from_file(cls, file_path: str = "data/Table_4_Tariffs.txt") -> None:
        """Считывает и парсит данные из текстового файла ставок."""
        if cls._rates_cache:
            return

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл со ставками Таблицы 4 не найден: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Пропускаем разделители, шапку и пустые строки
                if not line or line.startswith("=") or line.startswith("CƏDVƏL") or line.startswith("Universal") or line.startswith("Məsafə"):
                    continue

                parts = line.split("|")
                if len(parts) >= 12:
                    dist_part = parts[0].strip()
                    if "-" in dist_part:
                        min_d, max_d = map(int, dist_part.split("-"))
                        rates = [float(p.strip()) for p in parts[1:12]]
                        cls._rates_cache[(min_d, max_d)] = rates

    @classmethod
    def get_base_rate(cls, distance_km: float, weight_tons: float, file_path: str = "data/Table_4_Tariffs.txt") -> float:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Возвращает базовую ставку в CHF за 1 тонну по Таблице 4.
        """
        cls._load_rates_from_file(file_path)

        dist = float(distance_km)
        w = float(weight_tons)

        # 1. Поиск индекса весовой категории
        target_col_idx = 0
        for idx, col_val in enumerate(cls._weight_columns):
            if w <= col_val:
                target_col_idx = idx
                break
            target_col_idx = len(cls._weight_columns) - 1

        # 2. Поиск строки расстояния
        for (min_d, max_d), rates in cls._rates_cache.items():
            if min_d <= dist <= max_d:
                return rates[target_col_idx]

        # Если расстояние > 1000 км, берем крайний интервал
        if dist > 1000 and (991, 1000) in cls._rates_cache:
            return cls._rates_cache[(991, 1000)][target_col_idx]

        return 0.0

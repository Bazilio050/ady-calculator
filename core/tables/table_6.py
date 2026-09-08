# core/tables/table_6.py

import os
from typing import Dict, Tuple, Optional, Any, List


class Table6Calculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Считывает тарифные ставки Таблицы 6 из файла data/Table_6_Tariffs.txt
    и вычисляет базовую ставку за 1 тонну в CHF для наливных грузов в цистернах.
    """

    DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Table_6_Tariffs.txt")

    # Справочник префиксов ГНГ для колонок Таблицы 6
    COL_2_PREFIXES = [
        "27090010", "27090090", "2710", "2712", "2713", "27149000",
        "2715", "340319", "340399", "3404", "381121", "381129",
        "38170050", "38241000"
    ]
    COL_3_PREFIXES = ["2705", "2711"]
    COL_4_PREFIXES = [
        "27071", "27072", "27073", "27074", "27075", "27079920",
        "28011", "28013000", "28013010", "28041", "28042", "28043", "28044",
        "28112100", "28121100", "28141", "2814", "28539030", "2901", "2902",
        "29321200", "29333100", "29333955", "3817"
    ]
    COL_5_PREFIXES = [
        "1520", "270779980", "2905", "2906", "2907", "2908",
        "29094100", "29321300", "3820", "38237", "3826", "39053"
    ]
    COL_6_PREFIXES = [
        "0401", "0403", "0404", "0405", "0406", "1501", "1502", "1503",
        "1504", "1505", "1506", "1507", "1516", "1517", "1518", "2009",
        "2105", "2201", "2202", "2203", "2204", "2205", "2206"
    ]
    COL_8_PREFIXES = [
        "27071", "27072", "27073", "2707", "290211", "29022", "29023",
        "290241", "290242", "290243", "290244", "29026", "29027", "29029"
    ]

    _rates_cache: Optional[Dict[Tuple[int, int], Dict[str, float]]] = None

    @classmethod
    def _parse_distance_range(cls, raw_dist: str) -> Tuple[int, int]:
        """Разбирает строку диапазона '1-10' в кортеж (1, 10)."""
        parts = raw_dist.strip().split("-")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        raise ValueError(f"Некорректный формат диапазона расстояний в Таблице 6: {raw_dist}")

    @classmethod
    def _load_data(cls) -> Dict[Tuple[int, int], Dict[str, float]]:
        """Считывает и кэширует данные из Table_6_Tariffs.txt один раз."""
        if cls._rates_cache is not None:
            return cls._rates_cache

        file_path = os.path.abspath(cls.DATA_FILE_PATH)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл Таблицы 6 не найден по пути: {file_path}")

        tariffs: Dict[Tuple[int, int], Dict[str, float]] = {}

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("=") or line_str.startswith("CƏDVƏL") or "Məsafə" in line_str or "Колонки:" in line_str:
                    continue

                parts = [p.strip() for p in line_str.split("|")]
                if len(parts) < 8:
                    continue

                try:
                    dist_range = cls._parse_distance_range(parts[0])
                    tariffs[dist_range] = {
                        "col_2": float(parts[1]),
                        "col_3": float(parts[2]),
                        "col_4": float(parts[3]),
                        "col_5": float(parts[4]),
                        "col_6": float(parts[5]),
                        "col_7": float(parts[6]),
                        "col_8": float(parts[7]),
                    }
                except (ValueError, IndexError):
                    continue

        cls._rates_cache = tariffs
        return cls._rates_cache

    @classmethod
    def determine_column(cls, gng_code: str, is_private_wagon: bool = False) -> str:
        """Динамически определяет колонку (col_2 ... col_8) по коду ГНГ."""
        clean_gng = str(gng_code).strip()

        # 1. Проверка колонки 8 (Приватные цистерны)
        if is_private_wagon and any(clean_gng.startswith(p) for p in cls.COL_8_PREFIXES):
            return "col_8"

        # 2. Проверка колонок со 2 по 6
        if any(clean_gng.startswith(p) for p in cls.COL_2_PREFIXES):
            return "col_2"
        if any(clean_gng.startswith(p) for p in cls.COL_3_PREFIXES):
            return "col_3"
        if any(clean_gng.startswith(p) for p in cls.COL_4_PREFIXES):
            return "col_4"
        if any(clean_gng.startswith(p) for p in cls.COL_5_PREFIXES):
            return "col_5"
        if any(clean_gng.startswith(p) for p in cls.COL_6_PREFIXES):
            return "col_6"

        # 3. По умолчанию — колонка 7 (Прочие наливные грузы)
        return "col_7"

    @classmethod
    def calculate(
        cls,
        distance_km: float,
        gng_code: str,
        is_private_wagon: bool = False
    ) -> Dict[str, Any]:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Находит базовую ставку CHF за 1 тонну по Таблице 6.
        """
        dist = int(round(distance_km))
        tariffs = cls._load_data()

        matched_rates = None
        for (min_dist, max_dist), rates in tariffs.items():
            if min_dist <= dist <= max_dist:
                matched_rates = rates
                break

        if matched_rates is None:
            if dist > 1000 and (991, 1000) in tariffs:
                matched_rates = tariffs[(991, 1000)]
            else:
                raise ValueError(f"Расстояние {dist} км выходит за пределы Таблицы 6.")

        column_name = cls.determine_column(gng_code=gng_code, is_private_wagon=is_private_wagon)
        base_rate = matched_rates[column_name]

        is_private_discount_included = (column_name == "col_8")

        return {
            "base_rate": base_rate,
            "column_name": column_name,
            "is_private_discount_included": is_private_discount_included,
            "applied_rules": []
        }

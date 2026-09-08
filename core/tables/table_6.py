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

    _rates_cache: Optional[Dict[Tuple[int, int], Dict[str, float]]] = None
    _column_gng_map: Dict[str, List[str]] = {}

    @classmethod
    def _parse_distance_range(cls, raw_dist: str) -> Tuple[int, int]:
        """Разбирает строку диапазона '1-10' в кортеж (1, 10)."""
        parts = raw_dist.strip().split("-")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        raise ValueError(f"Некорректный формат диапазона расстояний в Таблице 6: {raw_dist}")

    @classmethod
    def _extract_gng_codes_from_header(cls, header_text: str) -> List[str]:
        """Извлекает коды ГНГ из текстового описания колонки в шапке файла."""
        if "(" not in header_text or ")" not in header_text:
            return []
        
        raw_codes = header_text.split("(")[1].split(")")[0]
        raw_codes = raw_codes.replace("GNG", "").replace("GNG:", "").strip()
        
        codes = []
        for part in raw_codes.split(","):
            cleaned = part.strip()
            if cleaned:
                codes.append(cleaned)
        return codes

    @classmethod
    def _load_data(cls) -> Dict[Tuple[int, int], Dict[str, float]]:
        """Считывает и кэширует данные и шапку ГНГ из Table_6_Tariffs.txt один раз."""
        if cls._rates_cache is not None:
            return cls._rates_cache

        file_path = os.path.abspath(cls.DATA_FILE_PATH)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл Таблицы 6 не найден по пути: {file_path}")

        tariffs: Dict[Tuple[int, int], Dict[str, float]] = {}

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("=") or line_str.startswith("CƏDVƏL") or "Məsafə" in line_str:
                    continue

                # Парсинг кодов ГНГ из мета-шапки
                if line_str.startswith("Колонки:") or any(line_str.startswith(f"{i}:") for i in range(2, 9)):
                    for col_num in range(2, 9):
                        prefix = f"{col_num}:"
                        if prefix in line_str:
                            col_key = f"col_{col_num}"
                            cls._column_gng_map[col_key] = cls._extract_gng_codes_from_header(line_str)
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
        """Динамически определяет колонку (col_2 ... col_8) по коду ГНГ и шапке файла."""
        cls._load_data()
        clean_gng = str(gng_code).strip()

        # 1. Проверка колонки 8 (Приватные цистерны)
        if is_private_wagon:
            col_8_codes = cls._column_gng_map.get("col_8", [])
            if any(clean_gng.startswith(code) for code in col_8_codes):
                return "col_8"

        # 2. Проверка колонок со 2 по 6
        for col_num in range(2, 7):
            col_key = f"col_{col_num}"
            codes = cls._column_gng_map.get(col_key, [])
            if any(clean_gng.startswith(code) for code in codes):
                return col_key

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

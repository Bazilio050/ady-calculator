import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

# ------------------------------------------------------------------------------
# БЛОК 1: ПУТИ И КЭШ ДАННЫХ
# ------------------------------------------------------------------------------
TABLE_5_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "Table_5_Tariffs.txt"
)

_TABLE_5_CACHE: Optional[Dict[Tuple[int, int], Dict[str, float]]] = None


# ------------------------------------------------------------------------------
# БЛОК 2: ПАРСИНГ И КЭШИРОВАНИЕ ФАЙЛА ТАРИФОВ (Таблица 5)
# ------------------------------------------------------------------------------
def _parse_distance_range(raw_dist: str) -> Tuple[int, int]:
    """Преобразует строку диапазона '1-10' в кортеж целых чисел (1, 10)."""
    parts = raw_dist.strip().split("-")
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    raise ValueError(f"Некорректный формат интервала расстояния в Таблице 5: {raw_dist}")


def load_table_5_data(force_reload: bool = False) -> Dict[Tuple[int, int], Dict[str, float]]:
    """
    Загружает и кэширует базовые тарифные ставки Таблицы 5 (в CHF) из текстового файла.
    """
    global _TABLE_5_CACHE

    if _TABLE_5_CACHE is not None and not force_reload:
        return _TABLE_5_CACHE

    if not os.path.exists(TABLE_5_DATA_PATH):
        raise FileNotFoundError(f"Файл с тарифами Таблицы 5 не найден: {TABLE_5_DATA_PATH}")

    tariffs: Dict[Tuple[int, int], Dict[str, float]] = {}

    with open(TABLE_5_DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or line_str.startswith("=") or "Məsafə" in line_str or "Колонки:" in line_str:
                continue

            parts = [p.strip() for p in line_str.split("|")]
            if len(parts) < 8:
                continue

            try:
                dist_range = _parse_distance_range(parts[0])
                tariffs[dist_range] = {
                    "col_2": float(parts[1]),  # Рефрижераторы / ARV (<25т за вагон)
                    "col_3": float(parts[2]),  # Рефрижераторы / ARV (>=25т за 1т)
                    "col_4": float(parts[3]),  # Термосы / ледники (<25т за вагон)
                    "col_5": float(parts[4]),  # Термосы / ледники (>=25т за 1т)
                    "col_6": float(parts[5]),  # Автовозы (>=10т за 1т)
                    "col_7": float(parts[6]),  # ИНВ / АНВ груженый (за 1т)
                    "col_8": float(parts[7]),  # ИНВ / АНВ порожний (за вагон)
                }
            except (ValueError, IndexError):
                continue

    _TABLE_5_CACHE = tariffs
    return _TABLE_5_CACHE

# ------------------------------------------------------------------------------
# БЛОК: Загрузка и расчет ставок по Таблице 11 (Негабаритные грузы)
# ------------------------------------------------------------------------------
import os
from typing import Dict, Tuple, Optional

def _load_table_11_data() -> Dict[Tuple[int, int], Dict[str, float]]:
    """
    Загружает тарифные ставки из data/Table_11_Tariffs.txt.
    Возвращает словарь с ключом (min_km, max_km) и значением {col_name: rate}.
    """
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "Table_11_Tariffs.txt"
    )
    table_data = {}
    
    if not os.path.exists(file_path):
        return table_data

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Məsafə") or line.startswith("Distance"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 11:
                continue
            
            dist_range = parts[0].split("-")
            min_km, max_km = int(dist_range[0]), int(dist_range[1])
            
            rates = {}
            for idx in range(1, 11):
                col_key = f"Col {idx}"
                rates[col_key] = float(parts[idx])
                
            table_data[(min_km, max_km)] = rates
            
    return table_data

_TABLE_11_DATA = _load_table_11_data()


def get_table_11_rate(distance_km: int, column_number: int) -> float:
    """
    Возвращает базовую ставку CHF из Таблицы 11 по расстоянию и номеру колонки (1..10).
    Колонки 1-5 соответствуют 3-й верхней степени (Col 1 - вагон, Col 2..5 - за тонну).
    Колонки 6-10 соответствуют 3-5 нижней / 4-5 боковой степеням (Col 6 - вагон, Col 7..10 - за тонну).
    """
    col_key = f"Col {column_number}"
    
    for (min_km, max_km), rates in _TABLE_11_DATA.items():
        if min_km <= distance_km <= max_km:
            return rates.get(col_key, 0.0)
            
    # Для расстояний свыше 1000 км берется интервал 991-1000 км
    max_range = max(_TABLE_11_DATA.keys(), key=lambda x: x[1]) if _TABLE_11_DATA else (991, 1000)
    return _TABLE_11_DATA.get(max_range, {}).get(col_key, 0.0)

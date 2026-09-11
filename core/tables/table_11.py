# ------------------------------------------------------------------------------
# БЛОК: Расчёт тарифных ставок по Таблице 11 (Негабаритные грузы)
# ------------------------------------------------------------------------------
import os
from typing import Dict, Tuple, Optional, Any

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
            
    if _TABLE_11_DATA:
        max_range = max(_TABLE_11_DATA.keys(), key=lambda x: x[1])
        return _TABLE_11_DATA.get(max_range, {}).get(col_key, 0.0)
    return 0.0


def calculate_table_11_tariff(
    distance_km: int,
    actual_weight: float,
    oversized_degree: str
) -> Dict[str, Any]:
    """
    Выполняет расчёт по Таблице 11 согласно п. 3.5.1.2.
    - 3-я верхняя степень: колонки 1..5 + коэффициент 1.50
    - 3-5 нижняя / 4-5 боковая: колонки 6..10 + коэффициент 2.00
    """
    applied_rules = []
    billable_weight = actual_weight
    
    if actual_weight < 10.0:
        billable_weight = 10.0

    if oversized_degree == "3_top":
        if actual_weight < 10.0:
            column = 1
        elif actual_weight <= 10.0:
            column = 2
        elif actual_weight <= 15.0:
            column = 3
        elif actual_weight <= 20.0:
            column = 4
        else:
            column = 5
            
        coeff = 1.50
        applied_rules.append({
            "rule_code": "OVERSIZED_TABLE_11_TOP_3_RULE_3_5_1_2",
            "params": {"coeff": 1.50, "column": column}
        })

    elif oversized_degree in ["3-5_bottom", "4-5_side", "3-5_bottom_side"]:
        if actual_weight < 10.0:
            column = 6
        elif actual_weight <= 10.0:
            column = 7
        elif actual_weight <= 15.0:
            column = 8
        elif actual_weight <= 20.0:
            column = 9
        else:
            column = 10
            
        coeff = 2.00
        applied_rules.append({
            "rule_code": "OVERSIZED_TABLE_11_HIGH_DEGREE_RULE_3_5_1_2",
            "params": {"coeff": 2.00, "column": column}
        })
    else:
        raise ValueError(f"Степень негабаритности {oversized_degree} не относится к Таблице 11.")

    base_rate_chf = get_table_11_rate(distance_km, column)

    return {
        "base_rate_chf": base_rate_chf,
        "billable_weight": billable_weight,
        "column": column,
        "coeff": coeff,
        "applied_rules": applied_rules
    }

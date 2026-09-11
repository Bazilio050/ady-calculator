# ------------------------------------------------------------------------------
# БЛОК: Загрузка и расчет ставок по Таблице 12 (Опасные грузы)
# ------------------------------------------------------------------------------
import os
from typing import Dict, Tuple, Any

def _load_table_12_data() -> Dict[Tuple[int, int], Dict[str, float]]:
    """
    Загружает тарифные ставки из data/Table_12_Tariffs.txt.
    Возвращает словарь с ключом (min_km, max_km) и значениями по категориям веса.
    """
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "Table_12_Tariffs.txt"
    )
    table_data = {}
    
    if not os.path.exists(file_path):
        return table_data

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Пропускаем пустые строки, заголовки и Markdown-разделители (| :--- | ...)
            if not line or "Məsafə" in line or ":" in line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            # Фильтруем пустые элементы
            parts = [p for p in parts if p]
            if len(parts) < 6:
                continue
            
            # Удаляем форматирование Markdown (**1-10 km**)
            raw_dist = parts[0].replace("*", "").replace("km", "").strip()
            dist_range = raw_dist.split("-")
            if len(dist_range) < 2:
                continue
                
            min_km, max_km = int(dist_range[0]), int(dist_range[1])
            
            rates = {
                "5t": float(parts[1]),
                "10t": float(parts[2]),
                "15t": float(parts[3]),
                "20t": float(parts[4]),
                "20_60t": float(parts[5]),
            }
            table_data[(min_km, max_km)] = rates
            
    return table_data

_TABLE_12_DATA = _load_table_12_data()


def get_table_12_rate(distance_km: int, weight_tons: float) -> float:
    """
    Возвращает базовую ставку CHF за 1 тонну из Таблицы 12.
    Выбор колонки по весу:
    - weight <= 5 -> '5t'
    - weight <= 10 -> '10t'
    - weight <= 15 -> '15t'
    - weight <= 20 -> '20t'
    - weight > 20 -> '20_60t'
    """
    if weight_tons <= 5.0:
        weight_col = "5t"
    elif weight_tons <= 10.0:
        weight_col = "10t"
    elif weight_tons <= 15.0:
        weight_col = "15t"
    elif weight_tons <= 20.0:
        weight_col = "20t"
    else:
        weight_col = "20_60t"

    for (min_km, max_km), rates in _TABLE_12_DATA.items():
        if min_km <= distance_km <= max_km:
            return rates.get(weight_col, 0.0)

    if _TABLE_12_DATA:
        max_range = max(_TABLE_12_DATA.keys(), key=lambda x: x[1])
        return _TABLE_12_DATA.get(max_range, {}).get(weight_col, 0.0)
    return 0.0


class Table12Calculator:
    """Калькулятор базовых ставок Таблицы 12 для опасных грузов."""

    @classmethod
    def calculate(cls, distance_km: float, weight_tons: float) -> Dict[str, Any]:
        dist_int = int(distance_km)
        base_rate = get_table_12_rate(dist_int, weight_tons)
        
        return {
            "base_rate": base_rate,
            "billable_weight": weight_tons,
            "applied_rules": [
                {
                    "rule_code": "DANGEROUS_CARGO_COEFF_2_00_RULE_3_6_1",
                    "params": {"distance_km": dist_int, "weight": weight_tons}
                }
            ]
        }

# core/tables/table_transporter.py

from typing import Dict, Any

def get_empty_transporter_axle_rate(axle_count: int) -> float:
    """
    Возвращает ставку CHF за 1 ось-км для порожнего транспортера (п. 3.7.8).
    - 4 оси -> 0.12 CHF/ось-км
    - 6-8 осей -> 0.23 CHF/ось-км
    - 12-20 осей -> 0.35 CHF/ось-км
    - >20 осей -> 0.40 CHF/ось-км
    """
    if axle_count <= 4:
        return 0.12
    elif axle_count <= 8:
        return 0.23
    elif axle_count <= 20:
        return 0.35
    else:
        return 0.40


class EmptyTransporterCalculator:
    """Калькулятор провозной платы за порожний транспортер (п. 3.7.8)."""

    @classmethod
    def calculate(cls, distance_km: float, axle_count: int) -> Dict[str, Any]:
        rate = get_empty_transporter_axle_rate(axle_count)
        # Расчет: Расстояние * оси * ставка CHF
        base_rate_chf = round(distance_km * axle_count * rate, 2)
        
        return {
            "base_rate_chf": base_rate_chf,
            "rate_per_axle_km": rate,
            "applied_rules": [
                {
                    "rule_code": "TRANSPORTER_AXLE_KM_RATES_RULE_3_7_8",
                    "params": {"axles": axle_count, "rate": rate}
                }
            ]
        }

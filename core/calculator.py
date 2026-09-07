# core/calculator.py

from typing import Dict, Any, List
from core.tables.table_1_weight import Table1Calculator
from core.tables.table_min_load import TableMinLoadCalculator
from core.tables.table_3 import Table3Calculator
from core.main_rules import apply_main_rules


class TariffCalculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Центральный модуль расчета провозной платы. 
    Объединяет данные весовых таблиц, базовых ставок и сквозных коэффициентов.
    """

    @classmethod
    def calculate(
        cls,
        shipment_type: str,
        gng_code: str,
        actual_weight: float,
        distance_km: float,
        wagon_type: str,
        from_canonical_name: str,
        to_canonical_name: str,
        is_private_wagon: bool = False
    ) -> dict:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Выполняет полный расчет тарифа. Применяет коэффициенты последовательно к базовой ставке.
        """
        # 1. Расчет billable_weight (Таблица 1 / Минимальные нормы)
        weight_res = Table1Calculator.calculate_billable_weight(
            gng_code=gng_code,
            actual_weight=actual_weight,
            wagon_type=wagon_type
        )
        billable_weight = weight_res["billable_weight"]

        # 2. Проверка применимости Таблицы 3 (только Import / Export)
        is_table_3_applicable = shipment_type.lower() in ["import", "export", "импорт", "экспорт", "idxal", "ixrac"]

        # 3. Расчет коэффициентов
        rules_res = apply_main_rules(
            shipment_type=shipment_type,
            from_station=from_canonical_name,
            to_station=to_canonical_name,
            gng_code=gng_code,
            wagon_type=wagon_type,
            is_private_wagon=is_private_wagon
        )
        
        notifications = rules_res.get("notifications", [])
        if weight_res.get("applied_rule"):
            notifications.insert(0, {
                "rule_code": "MIN_LOAD_NORM",
                "params": {"actual": actual_weight, "applied": billable_weight}
            })

        # 4. Поиск базовой ставки и последовательное применение коэффициентов по правилам ЖД
        base_rate_per_ton = 0.0
        if is_table_3_applicable:
            base_rate_per_ton = Table3Calculator.get_base_rate(
                distance_km=distance_km,
                weight_tons=billable_weight
            )

        applied_coeffs = rules_res.get("applied_coefficients", [])
        running_rate = base_rate_per_ton

        if applied_coeffs:
            for coeff in applied_coeffs:
                running_rate *= coeff
            final_rate_per_ton = round(running_rate, 2)
        else:
            final_coeff = rules_res.get("calculated_value", 1.0)
            final_rate_per_ton = round(base_rate_per_ton * final_coeff, 2)

        return {
            "actual_weight": actual_weight,
            "billable_weight": billable_weight,
            "distance_km": distance_km,
            "base_rate_chf_per_ton": base_rate_per_ton,
            "final_coeff": rules_res.get("calculated_value", 1.0),
            "final_rate_chf_per_ton": final_rate_per_ton,
            "notifications": notifications
        }

# core/calculator.py

from typing import Dict, Any, List
from core.tables.table_1_weight import Table1Calculator
from core.tables.table_min_load import TableMinLoadCalculator
from core.tables.table_3 import Table3Calculator
from core.main_rules import apply_main_rules


class TariffCalculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Центральный модуль расчета провозной платы ADY.
    Последовательно применяет коэффициенты правила за правилом.
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
        act_w = int(actual_weight)
        notifications = []

        # 1.1. Минимальная норма по ГНГ
        min_load_res = TableMinLoadCalculator.get_min_load_weight(
            gng_code=gng_code,
            actual_weight=act_w
        )
        weight_after_min_norm = min_load_res["calculated_weight"]

        if min_load_res.get("rule_code"):
            notifications.append({
                "rule_code": min_load_res["rule_code"],
                "params": min_load_res.get("params", {})
            })

        # 1.2. Округление по Таблице 1
        weight_res = Table1Calculator.calculate_billable_weight(weight_after_min_norm)
        billable_weight = weight_res["calculated_weight"]

        if weight_res.get("rule_code"):
            notifications.append({
                "rule_code": weight_res["rule_code"],
                "params": weight_res.get("params", {})
            })

        # 2. Проверка применимости Таблицы 3
        is_table_3_applicable = shipment_type.lower() in ["import", "export", "импорт", "экспорт", "idxal", "ixrac"]

        # 3. Получение списка правил
        rules_res = apply_main_rules(
            shipment_type=shipment_type,
            gng_code=gng_code,
            wagon_type=wagon_type,
            from_canonical_name=from_canonical_name,
            to_canonical_name=to_canonical_name,
            is_table_3=is_table_3_applicable,
            is_private_wagon=is_private_wagon
        )
        
        applied_rules_list = rules_res.get("rules", [])

        for rule in applied_rules_list:
            notifications.append({
                "rule_code": rule["rule_code"],
                "params": rule.get("params", {})
            })

        # 4. Базовая ставка
        base_rate_per_ton = 0.0
        if is_table_3_applicable:
            base_rate_per_ton = Table3Calculator.get_base_rate(
                distance_km=distance_km,
                weight_tons=billable_weight
            )

        # 5. ПОСЛЕДОВАТЕЛЬНОЕ ПРИМЕНЕНИЕ КОЭФФИЦИЕНТОВ
        current_rate = base_rate_per_ton
        for rule in applied_rules_list:
            coeff_val = rule["calculated_value"]
            current_rate = current_rate * coeff_val

        final_rate_per_ton = round(current_rate, 2)

        return {
            "actual_weight": act_w,
            "billable_weight": billable_weight,
            "distance_km": distance_km,
            "base_rate_chf_per_ton": base_rate_per_ton,
            "final_coeff": rules_res.get("calculated_value", 1.0),
            "final_rate_chf_per_ton": final_rate_per_ton,
            "is_private_wagon": is_private_wagon,
            "notifications": notifications
        }

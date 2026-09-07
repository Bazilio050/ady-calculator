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
        shipment_type: str,           # 'import', 'export', 'transit', 'local'
        gng_code: str,                # Код ГНГ
        actual_weight: int,           # Фактический вес в тоннах
        distance_km: float,           # Тарифное расстояние в км
        wagon_type: str,              # Тип вагона
        from_canonical_name: str,     # Станция отправления
        to_canonical_name: str,       # Станция назначения
        is_private_wagon: bool = False,# Собственный/приватный вагон (0.85)
        is_empty: bool = False,       # Порожний пробег
        is_methanol: bool = False,    # Метанол
        is_oil_product: bool = False  # Нефть/нефтепродукты
    ) -> Dict[str, Any]:
        """
        Главный метод расчета итогового тарифа.
        """
        notifications: List[Dict[str, Any]] = []

        # 1. Проверка минимальной нормы загрузки
        min_load_res = TableMinLoadCalculator.get_min_load_weight(gng_code, actual_weight)
        weight_after_min_norm = min_load_res["calculated_weight"]
        if min_load_res["rule_code"]:
            notifications.append({
                "rule_code": min_load_res["rule_code"],
                "params": min_load_res["params"]
            })

        # 2. Определение расчетной категории веса по Таблице 1
        table1_res = Table1Calculator.calculate_billable_weight(weight_after_min_norm)
        billable_weight = table1_res["calculated_weight"]
        if table1_res["rule_code"]:
            notifications.append({
                "rule_code": table1_res["rule_code"],
                "params": table1_res["params"]
            })

        # 3. Расчет коэффициентов по Главным правилам
        is_table_3_applicable = shipment_type.lower() in ["import", "export"]
        rules_res = apply_main_rules(
            shipment_type=shipment_type,
            gng_code=gng_code,
            wagon_type=wagon_type,
            from_canonical_name=from_canonical_name,
            to_canonical_name=to_canonical_name,
            is_table_3=is_table_3_applicable,
            is_methanol=is_methanol,
            is_oil_product=is_oil_product,
            is_empty=is_empty,
            is_private_wagon=is_private_wagon
        )

        for rule in rules_res["rules"]:
            notifications.append({
                "rule_code": rule["rule_code"],
                "params": rule.get("params", {})
            })

        return {
            "billable_weight": billable_weight,
            "final_coeff": rules_res["calculated_value"],
            "notifications": notifications
        }

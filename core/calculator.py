# core/calculator.py

from typing import Dict, Any, List
from core.tables.table_1_weight import Table1Calculator
from core.tables.table_min_load import TableMinLoadCalculator
from core.tables.table_3 import Table3Calculator
from core.tables.table_4 import Table4Calculator
from core.tables.table_5 import Table5Calculator
from core.tables.table_6 import Table6Calculator
from typing import Dict, Any, List, Optional
from core.main_rules import apply_main_rules
from data.currency_rates import get_exchange_rate


class TariffCalculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Центральный модуль расчета провозной платы ADY.
    Выполняет выбор базовой таблицы (Таблица 3 или Таблица 4),
    конвертацию ставки в USD и последовательно применяет правила.
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
        is_private_wagon: bool = False,
        shipment_date: Optional[str] = None,
        ref_section_wagons_count: Optional[int] = None,
        is_tariff_agreement_origin: bool = False,
        axle_count: int = 4,
        is_in_loaded_ref_section: bool = False
    ) -> Dict[str, Any]:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Выполняет полный цикл расчета тарифа с учетом спецвагонов, правил и валютной конвертации.
        """
        
        act_w = int(actual_weight)
        notifications = []
        ship_type_lower = shipment_type.lower()
        wagon_type_lower = wagon_type.lower()

        # Определение типа вагона (Спецвагон / Цистерна / Универсальный)
        ref_wagon_types = [
            "refrigerator", "arv", "ref_section", "thermos", "ice_wagon",
            "car_carrier", "two_tier_platform", "двухъярусная_платформа",
            "diesel_generator", "diesel_gen", "дизель_генератор",
            "inv", "anv", "inv_anv"
        ]
        tank_wagon_types = ["cistern", "tank", "цистерна", "бункер", "bunker"]

        is_ref_wagon = wagon_type_lower in ref_wagon_types
        is_tank_wagon = wagon_type_lower in tank_wagon_types

        # 1.1. Минимальная норма загрузки по ГНГ
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

        # 1.2. Округление категории веса по Таблице 1
        weight_res = Table1Calculator.calculate_billable_weight(weight_after_min_norm)
        billable_weight = weight_res["calculated_weight"]

        if weight_res.get("rule_code"):
            notifications.append({
                "rule_code": weight_res["rule_code"],
                "params": weight_res.get("params", {})
            })

        # 2. Проверка применимости Таблиц 3 и 4
        is_table_3_applicable = ship_type_lower in ["import", "export", "импорт", "экспорт", "idxal", "ixrac"]
        is_table_4_applicable = ship_type_lower in ["transit", "транзит", "tranzit"]

        # 3. Расчет правил и коэффициентов
        ref_wagon_types = [
            "refrigerator", "arv", "ref_section", "thermos", "ice_wagon",
            "car_carrier", "two_tier_platform", "двухъярусная_платформа",
            "diesel_generator", "diesel_gen", "дизель_генератор",
            "inv", "anv", "inv_anv"
        ]
        is_ref_wagon = wagon_type.lower() in ref_wagon_types

        rules_res = apply_main_rules(
            shipment_type=shipment_type,
            gng_code=gng_code,
            wagon_type=wagon_type,
            from_canonical_name=from_canonical_name,
            to_canonical_name=to_canonical_name,
            is_table_3=is_table_3_applicable and not is_ref_wagon,
            is_private_wagon=is_private_wagon
        )
        
        applied_rules_list = rules_res.get("rules", [])

        for rule in applied_rules_list:
            notifications.append({
                "rule_code": rule["rule_code"],
                "params": rule.get("params", {})
            })

        # 4. Получение базовой ставки в CHF
        base_rate_chf = 0.0
        table_name = "Таблица 3"

        if is_ref_wagon:
            table_name = "Таблица 5"
            t5_res = Table5Calculator.calculate(
                distance_km=distance_km,
                weight_tons=billable_weight,
                equipment_type=wagon_type,
                is_empty=(actual_weight == 0),
                ref_section_wagons_count=ref_section_wagons_count,
                gng_code=gng_code,
                is_tariff_agreement_origin=is_tariff_agreement_origin,
                axle_count=axle_count,
                is_in_loaded_ref_section=is_in_loaded_ref_section
            )
            base_rate_chf = t5_res["base_rate"]

            # Переносим правила из Таблицы 5 ровно один раз без дублирования
            t5_rules = t5_res.get("applied_rules", [])
            for r in t5_rules:
                applied_rules_list.append(r)
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })
        elif is_table_3_applicable:
            table_name = "Таблица 3"
            base_rate_chf = Table3Calculator.get_base_rate(
                distance_km=distance_km,
                weight_tons=billable_weight
            )
        elif is_table_4_applicable:
            table_name = "Таблица 4"
            base_rate_chf = Table4Calculator.get_base_rate(
                distance_km=distance_km,
                weight_tons=billable_weight
            )

        # 5. Получение курса валюты и перевод базовой ставки в USD (база / курс)
        exchange_rate = get_exchange_rate(shipment_date)
        base_rate_usd = (base_rate_chf / exchange_rate) if exchange_rate > 0 else base_rate_chf

        # 6. Последовательное применение коэффициентов:
        # Сначала спец-правила, затем 1.015, в самом конце 0.85
        specific_rules = [r for r in applied_rules_list if r["rule_code"] not in ["MAIN_COEFF_1_015_INTERNATIONAL_LOADED", "MAIN_COEFF_0_85_PRIVATE_WAGON"]]
        loaded_rule = [r for r in applied_rules_list if r["rule_code"] == "MAIN_COEFF_1_015_INTERNATIONAL_LOADED"]
        private_rule = [r for r in applied_rules_list if r["rule_code"] == "MAIN_COEFF_0_85_PRIVATE_WAGON"]

        ordered_rules = specific_rules + loaded_rule + private_rule

        running_rate = base_rate_usd
        for rule in ordered_rules:
            running_rate = running_rate * rule["calculated_value"]

        final_rate_per_ton_usd = round(running_rate, 2)

        return {
            "actual_weight": act_w,
            "billable_weight": billable_weight,
            "distance_km": distance_km,
            "base_rate_chf_per_ton": base_rate_chf,
            "exchange_rate": exchange_rate,
            "exchange_rate_chf_to_usd": exchange_rate,
            "base_rate_usd_per_ton": round(base_rate_usd, 2),
            "table_name": table_name,
            "applied_table": table_name,
            "final_coeff": rules_res.get("calculated_value", 1.0),
            "final_rate_usd_per_ton": final_rate_per_ton_usd,
            "is_private_wagon": is_private_wagon,
            "notifications": notifications
        }

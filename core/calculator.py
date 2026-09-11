# core/calculator.py

import math
from typing import Dict, Any, List, Optional
from core.tables.table_1_weight import Table1Calculator
from core.tables.table_min_load import TableMinLoadCalculator
from core.tables.table_3 import Table3Calculator
from core.tables.table_4 import Table4Calculator
from core.tables.table_5 import Table5Calculator
from core.tables.table_6 import Table6Calculator
from core.tables.table_7 import Table7Calculator
from core.tables.table_8 import Table8Calculator
from core.tables.table_10 import Table10Calculator
from core.main_rules import apply_main_rules
from data.currency_rates import get_exchange_rate

# Константа префиксов ГНГ для порожних вагонов
EMPTY_WAGON_GNG_PREFIXES = ("9921", "9922")


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
        is_in_loaded_ref_section: bool = False,
        calc_type_table_7: Optional[str] = None,             # "wagon_small_tonnage" или "medium_container"
        weight_category_table_7: Optional[int] = None,       # 5, 10, 15, 20, 25 тонн
        container_category_tons: Optional[int] = None,       # 3 или 5 тонн
        is_loaded_container: bool = True,                    # True = гружёный, False = порожний
        is_passenger_wagon: bool = False,                    # Флаг пассажирского вагона
        is_specialized_platform: bool = False,               # Флаг специализированной платформы
        coupling_distance_over_19m: bool = False,            # Расстояние между осями сцепа > 19 м
        is_oversized_cargo: bool = False,                    # Флаг габаритного груза (əndazəli)
        is_empty_wagon: bool = False,                        # Флаг порожнего вагона (boş вагон)
        attendants_count: int = 0,                           # Количество проводников (п. 3.4.3.2)
        is_service_crew: bool = False                        # Флаг сервисной бригады (бесплатно по п. 3.4.3.2)
    ) -> Dict[str, Any]:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Выполняет полный цикл расчета тарифа с учетом спецвагонов, правил и валютной конвертации.
        """
        
        act_w = int(actual_weight)
        notifications = []
        ship_type_lower = shipment_type.lower()
        wagon_type_lower = wagon_type.lower()

        # ------------------------------------------------------------------------------
        # Списки типов вагонов и контейнеров (ДОЛЖНЫ БЫТЬ В САМОМ НАЧАЛЕ)
        # ------------------------------------------------------------------------------
        ref_wagon_types = [
            "refrigerator", "arv", "ref_section", "thermos", "ice_wagon",
            "car_carrier", "two_tier_platform", "двухъярусная_платформа",
            "diesel_generator", "diesel_gen", "дизель_генератор", "diesel_generator_wagon",
            "inv", "anv", "inv_anv",
            "road_train", "semi_trailer", "road_train_platform", "автопоезд", "полуприцеп",
            "auto_body", "detachable_body", "кузов"
        ]
        tank_wagon_types = ["cistern", "tank", "цистерна", "бункер", "bunker"]
        generator_container_types = [
            "diesel_generator_container", 
            "generator_container", 
            "дизель_генераторный_контейнер"
        ]

        # Карта правил с коэффициентом 1.40 к Таблице 8 (пп. 3.4.6, 3.4.7, 3.4.8)
        coeff_1_40_map = {
            "CONTAINER_PLATFORM_COEFF_1_40": [
                "container_platform", "flatrack_container", "flatrack", 
                "контейнер_платформа", "платформа_контейнер"
            ],
            "OPEN_TOP_CONTAINER_COEFF_1_40": [
                "open_top_container", "open_top", 
                "открытый_контейнер", "контейнер_open_top"
            ],
            "SPECIAL_PURPOSE_CONTAINER_COEFF_1_40": [
                "special_purpose_container", "special_container", 
                "спец_контейнер", "специальный_контейнер"
            ]
        }

        active_1_40_rule = None
        for rule_code, types_list in coeff_1_40_map.items():
            if wagon_type_lower in types_list:
                active_1_40_rule = rule_code
                break

        is_ref_wagon = wagon_type_lower in ref_wagon_types
        is_tank_wagon = wagon_type_lower in tank_wagon_types
        is_special_container = wagon_type_lower in ("tank_container", "reefer_container", "wine_juice_container")
        is_generator_container = wagon_type_lower in generator_container_types
        is_universal_container = wagon_type_lower in ("container", "universal_container", "контейнер")

        # Автоматическое определение порожнего состояния по префиксу ГНГ (9921 / 9922) или весу = 0
        clean_gng = str(gng_code).strip() if gng_code else ""
        if clean_gng.startswith(EMPTY_WAGON_GNG_PREFIXES) or act_w == 0:
            is_empty_wagon = True

        # ------------------------------------------------------------------------------
        # БЛОК 1.1: Определение минимальной нормы загрузки (Цистерны / Транспортеры / ГНГ)
        # ------------------------------------------------------------------------------
        if is_tank_wagon:
            weight_after_min_norm = 25.0
        elif wagon_type_lower in ("transporter", "транспортер"):
            weight_after_min_norm, transp_rule = Table7Calculator.check_transporter_min_weight(
                actual_weight=actual_weight,
                axle_count=axle_count
            )
            if transp_rule:
                notifications.append(transp_rule)
        else:
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

        is_table_7 = (calc_type_table_7 is not None) or is_passenger_wagon or (str(gng_code).strip() == "99910000")
        is_inv_anv = wagon_type_lower in ("inv", "anv", "inv_anv")
        is_auto_special = wagon_type_lower in ("auto_body", "detachable_body", "кузов", "road_train", "semi_trailer", "road_train_platform", "автопоезд", "полуприцеп")

        if is_tank_wagon:
            billable_weight = 25.0
        elif is_auto_special and is_empty_wagon:
            # Для п. 3.3.2 в порожнем состоянии фиксируем вес: 5т для кузовов, 7т для автопоездов
            billable_weight = 5.0 if wagon_type_lower in ("auto_body", "detachable_body", "кузов") else 7.0
        elif is_table_7 or is_inv_anv:
            # Для Таблицы 7 и İNV/ANV берем фактический вес пользователя без округления по Таблице 1
            billable_weight = float(actual_weight)
        else:
            weight_res = Table1Calculator.calculate_billable_weight(weight_after_min_norm)
            billable_weight = weight_res["calculated_weight"]

            if weight_res.get("rule_code"):
                notifications.append({
                    "rule_code": weight_res["rule_code"],
                    "params": weight_res.get("params", {})
                })

        # 2. Проверка применимости Таблиц 3 и 4 (исключаем спецтаблицы, контейнеры и порожние вагоны)
        is_table_3_applicable = ship_type_lower in ["import", "export", "импорт", "экспорт", "idxal", "ixrac"] and not (is_ref_wagon or is_tank_wagon or is_table_7 or is_special_container or is_generator_container or is_universal_container or (active_1_40_rule is not None) or is_empty_wagon)
        is_table_4_applicable = ship_type_lower in ["transit", "транзит", "tranzit"] and not (is_ref_wagon or is_tank_wagon or is_table_7 or is_special_container or is_generator_container or is_universal_container or (active_1_40_rule is not None) or is_empty_wagon)

        # 3. Определение таблицы и флагов груза до применения главных правил
        column_name = None

        if is_tank_wagon:
            table_name = "Таблица 6"
            column_name = Table6Calculator.determine_column(
                gng_code=gng_code,
                is_private_wagon=is_private_wagon
            )

        # Флаг для Таблицы 6 (Столбец 2 - нефть и нефтепродукты)
        is_oil_product = (is_tank_wagon and column_name == "col_2")

        # Убираем флаг приватноcти для главных правил, если это вагон-дизель-генератор, 
        # так как ставка 0.12 CHF/ось-км уже установлена для приватных вагонов по п. 3.4.3.2
        is_private_for_rules = is_private_wagon if wagon_type_lower != "diesel_generator_wagon" else False

        rules_res = apply_main_rules(
            shipment_type=shipment_type,
            gng_code=gng_code,
            wagon_type=wagon_type_lower,
            from_canonical_name=from_canonical_name,
            to_canonical_name=to_canonical_name,
            is_table_3=is_table_3_applicable and not (is_ref_wagon or is_tank_wagon or is_empty_wagon),
            is_oil_product=is_oil_product,
            is_empty=is_empty_wagon,
            is_private_wagon=is_private_for_rules
        )

        if rules_res is None:
            rules_res = {}

        applied_rules_list = rules_res.get("rules", [])
        for rule in applied_rules_list:
            notifications.append({
                "rule_code": rule["rule_code"],
                "params": rule.get("params", {})
            })

        # 4. Получение базовой ставки в CHF
        base_rate_chf = 0.0
        table_name = "Таблица 3"

        is_transporter = wagon_type_lower in ("transporter", "транспортер")

        # ------------------------------------------------------------------------------
        # БЛОК: Выбор таблицы расчета тарифной ставки
        # ------------------------------------------------------------------------------
        if wagon_type_lower == "diesel_generator_wagon":
            table_name = "Пункт 3.4.3.2"
            base_rate_chf = round(distance_km * axle_count * 0.12, 2)
            applied_rules_list.append({
                "rule_code": "DIESEL_GENERATOR_WAGON_RULE_3_4_3_2",
                "calculated_value": 1.0,
                "params": {"axle_count": axle_count, "rate": 0.12}
            })
            notifications.append({
                "rule_code": "DIESEL_GENERATOR_WAGON_RULE_3_4_3_2",
                "params": {}
            })

        elif is_empty_wagon and is_private_wagon and not is_transporter and not is_ref_wagon and not is_special_container:
            table_name = "Пункт 3.2.2"
            base_rate_chf = distance_km * axle_count * 0.10
            notifications.append({
                "rule_code": "MAIN_EMPTY_PRIVATE_WAGON_0_10_AXLE_KM",
                "params": {"axle_count": axle_count, "distance_km": distance_km}
            })

        elif is_tank_wagon:
            table_name = "Таблица 6"
            t6_res = Table6Calculator.calculate(
                distance_km=distance_km,
                gng_code=gng_code,
                is_private_wagon=is_private_wagon
            )
            base_rate_chf = t6_res["base_rate"]

        elif is_table_7:
            table_name = "Таблица 7"
            calc_type_t7 = calc_type_table_7 or "wagon_small_tonnage"

            t7_res = Table7Calculator.calculate(
                distance_km=distance_km,
                calc_type=calc_type_t7,
                weight_tons=billable_weight,
                weight_category=weight_category_table_7,
                container_category_tons=container_category_tons,
                is_loaded=is_loaded_container,
                cargo_code_gng=gng_code,
                is_passenger_wagon=is_passenger_wagon
            )
            base_rate_chf = t7_res["base_rate"]

            if "billable_weight" in t7_res:
                billable_weight = t7_res["billable_weight"]

            for r in t7_res.get("applied_rules", []):
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })

        elif is_special_container:
            table_name = "Таблица 10"
            # Определяем категорию для Таблицы 10
            if wagon_type_lower == "reefer_container":
                c_type = "ref"
            elif wagon_type_lower == "wine_juice_container":
                c_type = "wine"
            else:
                c_type = "tank"

            # Определяем размерность (20 или 40 футов)
            feet_size = 40 if container_category_tons and container_category_tons > 20 else 20

            t10_res = Table10Calculator.get_base_rate(
                distance_km=distance_km,
                container_type=c_type,
                feet_size=feet_size,
                is_empty=is_empty_wagon
            )
            base_rate_chf = t10_res["base_rate"]

            for r in t10_res.get("applied_rules", []):
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })

        elif wagon_type_lower in ("container", "universal_container", "контейнер"):
            table_name = "Таблица 8"
            t8_res = Table8Calculator.get_base_rate(
                distance_km=distance_km,
                feet_size=container_category_tons or 20,
                is_empty=is_empty_wagon,
                is_private=is_private_wagon,
                is_generator_container=False
            )
            base_rate_chf = t8_res["base_rate"]

            for r in t8_res.get("applied_rules", []):
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })
        
        elif is_generator_container:
            table_name = "Таблица 8"
            t8_res = Table8Calculator.get_base_rate(
                distance_km=distance_km,
                feet_size=container_category_tons or 20,
                is_empty=is_empty_wagon,
                is_private=is_private_wagon,
                is_generator_container=True
            )
            base_rate_chf = t8_res["base_rate"]

            for r in t8_res.get("applied_rules", []):
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })

        elif active_1_40_rule:
            table_name = "Таблица 8"
            t8_res = Table8Calculator.get_base_rate(
                distance_km=distance_km,
                feet_size=container_category_tons or 20,
                is_empty=is_empty_wagon,
                is_private=is_private_wagon,
                coeff_1_40_rule_code=active_1_40_rule
            )
            base_rate_chf = t8_res["base_rate"]

            for r in t8_res.get("applied_rules", []):
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })
                    
        elif is_ref_wagon:
            table_name = "Таблица 5"
            # Для п. 3.3.1 (гружёные İNV / ANV): минимум 10т
            if wagon_type_lower in ("inv", "anv", "inv_anv") and not is_empty_wagon and billable_weight < 10.0:
                notifications.append({
                    "rule_code": "INV_ANV_MIN_WEIGHT_10T_RULE_3_3_1",
                    "params": {"actual_weight": billable_weight}
                })
                billable_weight = 10.0

            # Для п. 3.3.2 (порожние автопоезда/полуприцепы -> 7т, съемные кузова -> 5т)
            elif is_empty_wagon and wagon_type_lower in ("auto_body", "detachable_body", "кузов", "road_train", "semi_trailer", "road_train_platform", "автопоезд", "полуприцеп"):
                if wagon_type_lower in ("auto_body", "detachable_body", "кузов"):
                    billable_weight = 5.0
                else:
                    billable_weight = 7.0

            t5_res = Table5Calculator.calculate(
                distance_km=distance_km,
                weight_tons=billable_weight,
                equipment_type=wagon_type,
                is_empty=is_empty_wagon,
                ref_section_wagons_count=ref_section_wagons_count,
                gng_code=gng_code,
                is_tariff_agreement_origin=is_tariff_agreement_origin,
                axle_count=axle_count,
                is_in_loaded_ref_section=is_in_loaded_ref_section
            )
            base_rate_chf = t5_res["base_rate"]

            t5_rules = t5_res.get("applied_rules", [])
            for r in t5_rules:
                if r not in applied_rules_list:
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

        # ------------------------------------------------------------------------------
        # БЛОК: Правило 3.1.2.7 (Спецплатформа > 19м с габаритным грузом, МПС)
        # ------------------------------------------------------------------------------
        if (
            is_specialized_platform
            and coupling_distance_over_19m
            and is_oversized_cargo
            and not is_private_wagon
        ):
            rule_3_1_2_7 = {
                "rule_code": "MAIN_COEFF_SPECIAL_PLATFORM_OVER_19M_1_20",
                "calculated_value": 1.20
            }
            applied_rules_list.append(rule_3_1_2_7)
            notifications.append({
                "rule_code": "MAIN_COEFF_SPECIAL_PLATFORM_OVER_19M_1_20",
                "params": {}
            })

        # Упорядочивание правил (специфические правила -> 1.015 -> коэффициент приватного вагона 0.85/0.70)
        private_rule_codes = ["MAIN_COEFF_0_85_PRIVATE_WAGON", "MAIN_COEFF_0_70_SPECIAL_CHEMICALS_TANK"]
        
        specific_rules = [r for r in applied_rules_list if r["rule_code"] not in ["MAIN_COEFF_1_015_INTERNATIONAL_LOADED"] + private_rule_codes]
        loaded_rule = [r for r in applied_rules_list if r["rule_code"] == "MAIN_COEFF_1_015_INTERNATIONAL_LOADED"]
        private_rule = [r for r in applied_rules_list if r["rule_code"] in private_rule_codes]

        ordered_rules = specific_rules + loaded_rule + private_rule

        running_rate = base_rate_usd
        for rule in ordered_rules:
            running_rate = running_rate * rule["calculated_value"]

        final_rate_per_ton_usd = round(running_rate, 2)

        # ------------------------------------------------------------------------------
        # БЛОК: Расчет платы за проводников в дизель-генераторе (п. 3.4.3.2)
        # ------------------------------------------------------------------------------
        if is_service_crew:
            notifications.append({
                "rule_code": "SERVICE_CREW_FREE_RULE_3_4_3_2",
                "params": {}
            })
        elif attendants_count > 0:
            # 12 CHF за каждые начатые 100 км на 1 человек
            hundreds_km = math.ceil(distance_km / 100.0)
            attendants_fee_chf = round(hundreds_km * 12.0 * attendants_count, 2)

            applied_rules_list.append({
                "rule_code": "ATTENDANTS_FEE_RULE_3_4_3_2",
                "calculated_value": attendants_fee_chf,
                "params": {"count": attendants_count, "hundreds_km": hundreds_km}
            })
            notifications.append({
                "rule_code": "ATTENDANTS_FEE_RULE_3_4_3_2",
                "params": {"count": attendants_count}
            })

        # ------------------------------------------------------------------------------
        # БЛОК: Финальный расчет полной стоимости за вагон / отправку
        # ------------------------------------------------------------------------------
        # Учитываем сбор за проводников по п. 3.4.3.2 (если начислен в CHF)
        attendants_fee_usd = 0.0
        for rule in applied_rules_list:
            if rule.get("rule_code") == "ATTENDANTS_FEE_RULE_3_4_3_2":
                attendants_fee_chf = rule.get("calculated_value", 0.0)
                attendants_fee_usd = round(attendants_fee_chf / exchange_rate, 2) if exchange_rate > 0 else attendants_fee_chf

        if wagon_type_lower == "diesel_generator_wagon":
            final_rate_total_usd = round(final_rate_per_ton_usd + attendants_fee_usd, 2)
        else:
            final_rate_total_usd = round(final_rate_per_ton_usd * billable_weight + attendants_fee_usd, 2)

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
            "final_rate_total_usd": final_rate_total_usd,
            "is_private_wagon": is_private_wagon,
            "notifications": notifications
        }

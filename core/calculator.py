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
from core.tables.table_11 import calculate_table_11_tariff
from core.tables.table_12 import Table12Calculator
from core.tables.table_13 import Table13Checker
from core.tables.table_transporter import EmptyTransporterCalculator
from core.main_rules import apply_main_rules
from data.currency_rates import get_exchange_rate

# Константы префиксов и кодов ГНГ
EMPTY_WAGON_GNG_PREFIXES = ("9921", "9922")

# ГНГ коды подвижного состава на своих осях (п. 3.7.1) — точные 8-значные коды
ROLLING_STOCK_AXLES_GNG_CODES = (
    "8601", "8602", "8603", "8604", "8605", "8606",
    "99211000", "99212000", "99214000",
    "99221000", "99222000", "99224000"
)

# Фиксированная ставка за паромные операции на ст. Алят (USD / вагон)
FERRY_HANDLING_FEE_USD = 70.0

class TariffCalculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Центральный модуль расчета провозной платы ADY.
    Выполняет выбор базовой таблицы (Таблица 3, 4, 6, 7, 8, 10, 11 или 12),
    конвертацию ставки в USD и последовательно применяет правила.
    """

    @classmethod
    def calculate_ferry_fees(
        cls, 
        route_from: str, 
        route_to: str, 
        num_wagons: int = 1
    ) -> Dict[str, Any]:
        """
        Расчет сборов за накат и выкат с парома строго по станции Алят-эксперт.
        """
        from_st = str(route_from).strip().lower()
        to_st = str(route_to).strip().lower()

        sea_terminals = ["курык", "актау", "трк", "туркменбаши"]
        
        nakat_fee = 0.0
        vykat_fee = 0.0

        # Движение СУША -> МОРЕ (Накат в Аляте)
        if to_st in sea_terminals or to_st == "алят-эксп.":
            if from_st not in sea_terminals and from_st != "алят-эксп.":
                nakat_fee = FERRY_HANDLING_FEE_USD * num_wagons

        # Движение МОРЕ -> СУША (Выкат в Аляте)
        if from_st in sea_terminals:
            if to_st not in sea_terminals:
                vykat_fee = FERRY_HANDLING_FEE_USD * num_wagons

        return {
            "ferry_nakat_fee_usd": nakat_fee,
            "ferry_vykat_fee_usd": vykat_fee,
            "total_ferry_fee_usd": nakat_fee + vykat_fee
        }

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
        is_service_crew: bool = False,                       # Флаг сервисной бригады (бесплатно по п. 3.4.3.2)
        oversized_degree: Optional[str] = None,              # Степень негабаритности (п. 3.5.1)
        is_transporter: bool = False,                        # Флаг транспортера (п. 3.5.1.3)
        cover_wagons_count: int = 0,                         # Количество вагонов прикрытия (п. 3.5.3)
        is_cover_wagon_private: bool = True,                 # Флаг приватного вагона прикрытия
        is_dangerous_cargo: bool = False,                    # Флаг опасного груза (п. 3.6.1)
        un_code: Optional[str] = None,                       # Код ООН (BMT №) по Таблице 13
        is_attached_wagons_group: bool = False,              # Флаг сцепа из нескольких вагонов (п. 3.7.1)
        attached_wagons_count: int = 1,                      # Количество вагонов в сцепе (п. 3.7.1)
        is_rolling_stock_on_own_axles: bool = False,         # Флаг подвижного состава на своих осях (п. 3.7.1)
        is_empty_wagon_repair: bool = False,                 # Флаг отправки в/из ремонта (п. 3.7.2)
        is_passenger_train_composition: bool = False,        # <-- ДОБАВЛЕНА ЗАПЯТАЯ В КОНЦЕ СТРОКИ
        attached_parts_weight: float = 0.0,                  # Масса тележек/запчастей на своих осях (п. 3.7.5)
        is_carrier_transporter_free_return: bool = False,    # Признак бесплатного возврата транспортера ADY (п. 3.7.7)
        is_separate_attendant_wagon: bool = False,           # Флаг отдельного вагона для проводников / теплушки (п. 3.9)
        is_passenger_wagon_type: bool = False,               # Признак пассажирского вагона для теплушки (п. 3.9)
        equipment_weight: float = 0.0,                       # Масса оборудования / средств крепления (п. 3.10.1)
        is_non_removable_equipment: bool = False,            # Флаг вагона с несъёмным оборудованием (п. 3.10.4)
        is_coffin_transport: bool = False,                   # Перевозка гробов с телами усопших (п. 3.11)
        is_separate_locomotive: bool = False,                # Перевозка с отдельным локомотивом (п. 3.12)
        separate_locomotive_coeff: float = 5.00,             # Коэффициент отдельного локомотива (п. 3.12, >= 5.00)
        expedited_delivery_train_type: Optional[str] = None, # Сокращенный срок доставки (п. 3.13): freight/passenger/container
        is_reloaded_part_shipment: bool = False              # Перегрузка из 1 вагона в несколько (п. 5.1.2 / 5.2.1)
    ) -> Dict[str, Any]:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Выполняет полный цикл расчета тарифа с учетом спецвагонов, правил и валютной конвертации.
        """
        
        actual_total_weight = actual_weight + attached_parts_weight + equipment_weight
        act_w = int(actual_total_weight)
        notifications = []

        if attached_parts_weight > 0.0:
            notifications.append({
                "rule_code": "ATTACHED_PARTS_WEIGHT_ADDED_RULE_3_7_5",
                "params": {"added_weight": attached_parts_weight}
            })

        if equipment_weight > 0.0:
            notifications.append({
                "rule_code": "EQUIPMENT_WEIGHT_ADDED_RULE_3_10_1",
                "params": {"added_weight": equipment_weight}
            })
        ship_type_lower = shipment_type.lower()
        wagon_type_lower = wagon_type.lower()

        # Автоматическая проверка по Таблице 13, если передан un_code
        if un_code and not is_dangerous_cargo:
            if Table13Checker.check_dangerous_status(un_code=un_code, wagon_type=wagon_type):
                is_dangerous_cargo = True

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

       # Авто-определение подвижного состава на осях (п. 3.7.1) строго при отсутствии ремонта и транспортеров
        if not is_empty_wagon_repair and not is_transporter and wagon_type_lower != "transporter" and not is_carrier_transporter_free_return:
            if clean_gng.startswith(("8601", "8602", "8603", "8604", "8605", "8606")) or clean_gng in ("99211000", "99212000", "99214000", "99221000", "99222000", "99224000"):
                is_rolling_stock_on_own_axles = True

        if clean_gng.startswith(("8601", "8602", "8603", "8604", "8605", "8606", "99211000", "99212000", "99214000", "99221000", "99222000", "99224000")):
            is_rolling_stock_on_own_axles = True

        # ------------------------------------------------------------------------------
        # БЛОК 1.1: Определение минимальной нормы загрузки (Цистерны / Транспортеры / ГНГ)
        # ------------------------------------------------------------------------------
        if is_tank_wagon:
            weight_after_min_norm = 25.0
        elif wagon_type_lower in ("transporter", "транспортер") or is_transporter:
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

        if is_attached_wagons_group and attached_wagons_count > 1:
            min_attached_weight = float(attached_wagons_count * 20)
            if actual_total_weight < min_attached_weight:
                billable_weight = min_attached_weight
                notifications.append({
                    "rule_code": "ATTACHED_WAGONS_MIN_WEIGHT_RULE_3_7_1",
                    "params": {"count": attached_wagons_count, "min_weight": min_attached_weight}
                })
            else:
                weight_res = Table1Calculator.calculate_billable_weight(weight_after_min_norm)
                billable_weight = weight_res["calculated_weight"]
        elif is_tank_wagon:
            billable_weight = 25.0
        elif is_auto_special and is_empty_wagon:
            billable_weight = 5.0 if wagon_type_lower in ("auto_body", "detachable_body", "кузов") else 7.0
        elif is_table_7 or is_inv_anv:
            billable_weight = float(actual_weight)
        else:
            weight_res = Table1Calculator.calculate_billable_weight(weight_after_min_norm)
            billable_weight = weight_res["calculated_weight"]
            if weight_res.get("rule_code"):
                notifications.append({
                    "rule_code": weight_res["rule_code"],
                    "params": weight_res.get("params", {})
                })

        # Принудительная проверка минимальной нормы 25т для малой степени негабаритности (п. 3.5.1.1)
        if oversized_degree in ["small", "1-2_bottom", "1-3_side", "1-2_top"] and billable_weight < 25.0:
            billable_weight = 25.0
            notifications.append({
                "rule_code": "OVERSIZED_SMALL_DEGREE_RULE_3_5_1_1",
                "params": {"actual_weight": actual_weight, "applied_weight": 25.0}
            })

        # 2. Проверка применимости Таблиц 3 и 4 (с учетом п. 3.7.1)
        is_table_3_applicable = ship_type_lower in ["import", "export", "импорт", "экспорт", "idxal", "ixrac"] and (
            is_rolling_stock_on_own_axles or not (is_ref_wagon or is_tank_wagon or is_table_7 or is_special_container or is_generator_container or is_universal_container or (active_1_40_rule is not None) or is_empty_wagon or is_dangerous_cargo)
        )
        is_table_4_applicable = ship_type_lower in ["transit", "транзит", "tranzit"] and (
            is_rolling_stock_on_own_axles or not (is_ref_wagon or is_tank_wagon or is_table_7 or is_special_container or is_generator_container or is_universal_container or (active_1_40_rule is not None) or is_empty_wagon or is_dangerous_cargo)
        )

        # 3. Определение таблицы и флагов груза до применения главных правил
        column_name = None

        if is_tank_wagon:
            table_name = "Таблица 6"
            column_name = Table6Calculator.determine_column(
                gng_code=gng_code,
                is_private_wagon=is_private_wagon
            )

        is_oil_product = (is_tank_wagon and column_name == "col_2")
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

       # ------------------------------------------------------------------------------
        # БЛОК: Выбор таблицы расчета тарифной ставки (С РАЗДЕЛОМ 3.7, 3.9 И 3.10)
        # ------------------------------------------------------------------------------
        if is_non_removable_equipment and is_empty_wagon:
            table_name = "Пункт 3.10.4"
            base_rate_chf = round(distance_km * axle_count * 0.12, 2)
            notifications.append({
                "rule_code": "NON_REMOVABLE_EQUIPMENT_WAGON_RULE_3_10_4",
                "params": {
                    "distance_km": int(distance_km),
                    "axle_count": int(axle_count),
                    "rate_chf": 0.12,
                    "total_chf": base_rate_chf
                }
            })

        elif is_separate_attendant_wagon:
            table_name = "Пункт 3.9"
            if is_passenger_wagon_type:
                rate_axle_km = 0.30 if is_private_wagon else 0.35
            else:
                rate_axle_km = 0.20 if is_private_wagon else 0.23

            base_rate_chf = round(distance_km * axle_count * rate_axle_km, 2)
            notifications.append({
                "rule_code": "SEPARATE_ATTENDANT_WAGON_RULE_3_9",
                "params": {
                    "distance_km": int(distance_km),
                    "axle_count": int(axle_count),
                    "rate_chf": rate_axle_km,
                    "total_chf": base_rate_chf
                }
            })
        elif is_carrier_transporter_free_return:
            table_name = "Пункт 3.7.7"
            base_rate_chf = 0.0
            notifications.append({
                "rule_code": "EMPTY_CARRIER_TRANSPORTER_FREE_RULE_3_7_7",
                "params": {}
            })

        elif (is_transporter or wagon_type_lower == "transporter") and is_empty_wagon:
            table_name = "Пункт 3.7.8"
            transp_res = EmptyTransporterCalculator.calculate(
                distance_km=distance_km,
                axle_count=axle_count
            )
            base_rate_chf = transp_res["base_rate_chf"]
            for r in transp_res.get("applied_rules", []):
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })

        elif is_empty_wagon_repair:
            table_name = "Пункт 3.7.2"
            base_rate_chf = round(distance_km * axle_count * 0.10, 2)
            notifications.append({
                "rule_code": "EMPTY_WAGON_REPAIR_0_10_AXLE_KM_RULE_3_7_2",
                "params": {"axle_count": axle_count, "distance_km": distance_km}
            })

        elif is_rolling_stock_on_own_axles:
            if is_table_4_applicable:
                table_name = "Таблица 4 (п. 3.7.1)"
                base_rate_chf = Table4Calculator.get_base_rate(
                    distance_km=distance_km,
                    weight_tons=billable_weight
                )
            else:
                table_name = "Таблица 3 (п. 3.7.1)"
                base_rate_chf = Table3Calculator.get_base_rate(
                    distance_km=distance_km,
                    weight_tons=billable_weight
                )

        elif is_dangerous_cargo and not is_tank_wagon and not is_special_container:
            table_name = "Таблица 12"
            t12_res = Table12Calculator.calculate(
                distance_km=distance_km,
                weight_tons=billable_weight
            )
            base_rate_chf = t12_res["base_rate"]
            
            for r in t12_res.get("applied_rules", []):
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })

        elif wagon_type_lower == "diesel_generator_wagon":
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

        elif is_empty_wagon and is_private_wagon and not is_transporter and not is_ref_wagon and not is_special_container and not is_rolling_stock_on_own_axles:
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
            
            if is_dangerous_cargo:
                base_rate_chf *= 2.00
                notifications.append({
                    "rule_code": "DANGEROUS_CARGO_COEFF_2_00_RULE_3_6_1",
                    "params": {"distance_km": int(distance_km), "weight": billable_weight}
                })

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
            if wagon_type_lower == "reefer_container":
                c_type = "ref"
            elif wagon_type_lower == "wine_juice_container":
                c_type = "wine"
            else:
                c_type = "tank"

            feet_size = 40 if container_category_tons and container_category_tons > 20 else 20

            t10_res = Table10Calculator.get_base_rate(
                distance_km=distance_km,
                container_type=c_type,
                feet_size=feet_size,
                is_empty=is_empty_wagon
            )
            base_rate_chf = t10_res["base_rate"]
            
            if is_dangerous_cargo:
                base_rate_chf *= 2.00
                notifications.append({
                    "rule_code": "DANGEROUS_CARGO_COEFF_2_00_RULE_3_6_1",
                    "params": {"distance_km": int(distance_km), "weight": billable_weight}
                })

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

        elif oversized_degree in ["3_top", "3-5_bottom", "4-5_side", "3-5_bottom_side"]:
            table_name = "Таблица 11"
            t11_res = calculate_table_11_tariff(
                distance_km=int(distance_km),
                actual_weight=float(act_w),
                oversized_degree=oversized_degree
            )
            base_rate_chf = t11_res["base_rate_chf"]
            billable_weight = t11_res["billable_weight"]

            applied_rules_list.append({
                "rule_code": t11_res["applied_rules"][0]["rule_code"],
                "calculated_value": t11_res["coeff"],
                "params": t11_res["applied_rules"][0]["params"]
            })
            for r in t11_res["applied_rules"]:
                notifications.append({
                    "rule_code": r["rule_code"],
                    "params": r.get("params", {})
                })

        elif is_ref_wagon:
            table_name = "Таблица 5"
            if wagon_type_lower in ("inv", "anv", "inv_anv") and not is_empty_wagon and billable_weight < 10.0:
                notifications.append({
                    "rule_code": "INV_ANV_MIN_WEIGHT_10T_RULE_3_3_1",
                    "params": {"actual_weight": billable_weight}
                })
                billable_weight = 10.0

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

        # 5. Получение курса валюты и перевод базовой ставки в USD
        exchange_rate = get_exchange_rate(shipment_date)
        base_rate_usd = (base_rate_chf / exchange_rate) if exchange_rate > 0 else base_rate_chf

        # ------------------------------------------------------------------------------
        # БЛОК: Дополнительные коэффициенты Раздела 3.7
        # ------------------------------------------------------------------------------
        if is_rolling_stock_on_own_axles:
            applied_rules_list.append({
                "rule_code": "ROLLING_STOCK_AXLES_COEFF_0_50_RULE_3_7_1",
                "calculated_value": 0.50,
                "params": {}
            })
            notifications.append({
                "rule_code": "ROLLING_STOCK_AXLES_COEFF_0_50_RULE_3_7_1",
                "params": {}
            })

        if is_passenger_train_composition:
            applied_rules_list.append({
                "rule_code": "ROLLING_STOCK_PASSENGER_TRAIN_COEFF_2_00_RULE_3_7_3",
                "calculated_value": 2.00,
                "params": {}
            })
            notifications.append({
                "rule_code": "ROLLING_STOCK_PASSENGER_TRAIN_COEFF_2_00_RULE_3_7_3",
                "params": {}
            })

        # --- Раздел 3.11: Перевозка гробов с телами усопших ---
        if is_coffin_transport:
            applied_rules_list.append({
                "rule_code": "COFFIN_TRANSPORT_COEFF_0_10_RULE_3_11",
                "calculated_value": 0.10,
                "params": {}
            })
            notifications.append({
                "rule_code": "COFFIN_TRANSPORT_COEFF_0_10_RULE_3_11",
                "params": {}
            })

        # --- Раздел 3.12: Перевозка с отдельным локомотивом ---
        if is_separate_locomotive:
            loco_coeff = max(5.00, float(separate_locomotive_coeff))
            applied_rules_list.append({
                "rule_code": "SEPARATE_LOCOMOTIVE_COEFF_5_00_RULE_3_12",
                "calculated_value": loco_coeff,
                "params": {"coeff": loco_coeff}
            })
            notifications.append({
                "rule_code": "SEPARATE_LOCOMOTIVE_COEFF_5_00_RULE_3_12",
                "params": {"coeff": loco_coeff}
            })

        # --- Раздел 3.13: Сокращенный срок доставки ---
        if expedited_delivery_train_type:
            exp_type = str(expedited_delivery_train_type).lower()
            if exp_type in ("freight", "грузовой"):
                exp_coeff = 1.50
                exp_rule = "EXPEDITED_DELIVERY_FREIGHT_TRAIN_COEFF_1_50_RULE_3_13"
            elif exp_type in ("passenger", "пассажирский"):
                exp_coeff = 2.00
                exp_rule = "EXPEDITED_DELIVERY_PASSENGER_TRAIN_COEFF_2_00_RULE_3_13"
            elif exp_type in ("container", "контейнерный"):
                exp_coeff = 1.00
                exp_rule = "EXPEDITED_DELIVERY_CONTAINER_TRAIN_COEFF_1_00_RULE_3_13"
            else:
                exp_coeff = 1.00
                exp_rule = None

            if exp_rule:
                applied_rules_list.append({
                    "rule_code": exp_rule,
                    "calculated_value": exp_coeff,
                    "params": {}
                })
                notifications.append({
                    "rule_code": exp_rule,
                    "params": {}
                })

        # --- Раздел 4: Перевозка домашней утвари (ГНГ 9901) ---
        clean_gng_sec4 = str(gng_code).strip().zfill(8)
        if clean_gng_sec4.startswith("9901"):
            notifications.append({
                "rule_code": "HOUSEHOLD_GOODS_RULE_4",
                "params": {}
            })

        # --- Раздел 5: Перегрузка из 1 вагона в несколько (п. 5.1.2 / 5.2.1) ---
        if is_reloaded_part_shipment:
            notifications.append({
                "rule_code": "CARGO_RELOADED_SPLIT_WAGONS_RULE_5_1_2",
                "params": {}
            })

        # ------------------------------------------------------------------------------
        # БЛОК: Правило 3.1.2.7
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

        # Упорядочивание правил
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
        # БЛОК: Расчет платы за проводников (п. 3.4.3.2 и п. 3.9)
        # ------------------------------------------------------------------------------
        if is_service_crew:
            notifications.append({
                "rule_code": "SERVICE_CREW_FREE_RULE_3_4_3_2",
                "params": {}
            })
        elif attendants_count > 0:
            hundreds_km = int(math.ceil(distance_km / 100.0))
            attendants_fee_chf = round(hundreds_km * 12.0 * attendants_count, 2)

            rule_code_att = "ATTENDANTS_FEE_RULE_3_4_3_2" if wagon_type_lower == "diesel_generator_wagon" else "ATTENDANTS_FEE_RULE_3_9"

            applied_rules_list.append({
                "rule_code": rule_code_att,
                "calculated_value": attendants_fee_chf,
                "params": {"count": attendants_count, "hundreds_km": hundreds_km, "blocks_100km": hundreds_km, "total_chf": attendants_fee_chf}
            })
            notifications.append({
                "rule_code": rule_code_att,
                "params": {"count": attendants_count, "hundreds_km": hundreds_km, "blocks_100km": hundreds_km, "total_chf": attendants_fee_chf}
            })

        
        # ------------------------------------------------------------------------------
        # БЛОК: Расчет платы за вагоны прикрытия
        # ------------------------------------------------------------------------------
        cover_wagons_fee_usd = 0.0
        if cover_wagons_count > 0:
            cover_rate_chf = 0.30 if is_cover_wagon_private else 0.35
            cover_fee_chf = round(distance_km * (cover_wagons_count * 4) * cover_rate_chf, 2)
            cover_wagons_fee_usd = round(cover_fee_chf / exchange_rate, 2) if exchange_rate > 0 else cover_fee_chf

            applied_rules_list.append({
                "rule_code": "EMPTY_COVER_WAGON_AXLE_KM_RULE_3_5_3",
                "calculated_value": cover_wagons_fee_usd,
                "params": {"count": cover_wagons_count, "rate": cover_rate_chf}
            })
            notifications.append({
                "rule_code": "EMPTY_COVER_WAGON_AXLE_KM_RULE_3_5_3",
                "params": {"count": cover_wagons_count, "rate": cover_rate_chf}
            })

        # ------------------------------------------------------------------------------
        # БЛОК: Расчет паромных сборов (Накат / Выкат в Аляте)
        # ------------------------------------------------------------------------------
        ferry_fees = cls.calculate_ferry_fees(
            route_from=from_canonical_name, 
            route_to=to_canonical_name, 
            num_wagons=1
        )

        if ferry_fees["ferry_nakat_fee_usd"] > 0:
            notifications.append({
                "rule_code": "FERRY_NAKAT_FEE_ALAT_RULE",
                "params": {"amount_usd": ferry_fees["ferry_nakat_fee_usd"]}
            })

        if ferry_fees["ferry_vykat_fee_usd"] > 0:
            notifications.append({
                "rule_code": "FERRY_VYKAT_FEE_ALAT_RULE",
                "params": {"amount_usd": ferry_fees["ferry_vykat_fee_usd"]}
            })

       # ------------------------------------------------------------------------------
        # БЛОК: Расчет морского фрахта ASCO (Каспийское море)
        # ------------------------------------------------------------------------------
        from core.asco_calculator import AscoFerryCalculator

        asco_res = AscoFerryCalculator.calculate(
            route_from=from_canonical_name,
            route_to=to_canonical_name,
            gng_code=gng_code,
            wagon_type=wagon_type_lower,
            shipment_type=shipment_type,
            wagon_length_m=wagon_length_m if 'wagon_length_m' in locals() else 14.0,
            is_empty=is_empty_wagon,
            is_dangerous=locals().get('is_dangerous', False),
            dangerous_class=locals().get('dangerous_class', None)
        )

        total_asco_usd = asco_res.get("total_asco_usd", 0.0)

        if total_asco_usd > 0:
            notifications.append({
                "rule_code": "ASCO_FERRY_FREIGHT_RULE",
                "params": {
                    "amount_usd": total_asco_usd,
                    "port": asco_res.get("port"),
                    "category": asco_res.get("cargo_category")
                }
            })

        # ------------------------------------------------------------------------------
        # БЛОК: Финальный расчет полной стоимости
        # ------------------------------------------------------------------------------
        attendants_fee_usd = 0.0
        for rule in applied_rules_list:
            if rule.get("rule_code") == "ATTENDANTS_FEE_RULE_3_4_3_2":
                attendants_fee_chf = rule.get("calculated_value", 0.0)
                attendants_fee_usd = round(attendants_fee_chf / exchange_rate, 2) if exchange_rate > 0 else attendants_fee_chf

        wagon_rate_usd = final_rate_per_ton_usd

        if wagon_type_lower == "diesel_generator_wagon":
            base_total_usd = round(wagon_rate_usd + attendants_fee_usd + cover_wagons_fee_usd, 2)
        else:
            base_total_usd = round(wagon_rate_usd * billable_weight + attendants_fee_usd + cover_wagons_fee_usd, 2)

        final_rate_total_usd = round(base_total_usd + ferry_fees["total_ferry_fee_usd"] + total_asco_usd, 2)

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
            "attendants_fee_usd": attendants_fee_usd,
            "ferry_nakat_fee_usd": ferry_fees["ferry_nakat_fee_usd"],
            "ferry_vykat_fee_usd": ferry_fees["ferry_vykat_fee_usd"],
            "total_ferry_fee_usd": ferry_fees["total_ferry_fee_usd"],
            "total_asco_freight_usd": total_asco_usd,
            "final_rate_total_usd": final_rate_total_usd,
            "is_private_wagon": is_private_wagon,
            "notifications": notifications
        }

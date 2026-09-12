# tests/test_section_3_7_rolling_stock.py

import sys
import os

# Добавление корневой директории проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.router import RailwayRouter
from core.calculator import TariffCalculator
from data.translations import RULE_MESSAGES


def _print_test_header(title: str):
    print(f"\n{'='*70}\n{title}\n{'='*70}")


def _print_calculation_result(
    title: str,
    route_res,
    calc_res,
    gng_code: str,
    weight: float,
    wagon_type: str,
    is_private: bool
):
    _print_test_header(title)
    display_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km
    print(f"Маршрут: {route_res.from_station.canonical_name} ({route_res.from_station.code}) - {route_res.to_station.canonical_name} ({route_res.to_station.code}) [{route_res.shipment_type.value}] - {display_dist} км")
    print(f"ГНГ код: {gng_code}")
    print(f"Тип вагона: {wagon_type} [{'СПС (приватный)' if is_private else 'СПС (инвентарный)'}]")
    print(f"Вес (факт): {weight} т -> Расчетный: {calc_res['billable_weight']} т")
    
    base_chf = round(calc_res['base_rate_chf_per_ton'], 2)
    applied_tbl = calc_res.get('applied_table', calc_res.get('table_name'))
    print(f"Базовая ставка: {base_chf} CHF ({applied_tbl})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']} USD\n")

    all_notifications = []
    if route_res.rule_code:
        all_notifications.append({"rule_code": route_res.rule_code, "params": route_res.params})
    all_notifications.extend(calc_res.get("notifications", []))

    for notif in all_notifications:
        code = notif.get("rule_code")
        params = notif.get("params", {})
        if code in RULE_MESSAGES and code != "TABLE_1_ROUNDING":
            ru_msg = RULE_MESSAGES[code]["ru"].format(**params) if params else RULE_MESSAGES[code]["ru"]
            print(f"{ru_msg}")

    attendants_fee_usd = calc_res.get("attendants_fee_usd", 0.0)
    final_total = calc_res.get("final_rate_total_usd", calc_res.get("final_rate_usd_per_ton"))
    wagon_freight_usd = round(calc_res['final_rate_usd_per_ton'] * calc_res['billable_weight'], 2)

    print("\nДетализация расчёта:")
    print(f"  • Итоговая ставка за тонну: {calc_res['final_rate_usd_per_ton']} USD/т")
    print(f"  • Провозная плата за вагон ({calc_res['billable_weight']} т): {wagon_freight_usd} USD")
    if attendants_fee_usd > 0:
        print(f"  • Плата за проезд проводников: {attendants_fee_usd} USD")
    
    print(f"\nИтого: {final_total} USD\n")

    if all_notifications:
        print("Уведомления:")
        for notif in all_notifications:
            code = notif.get("rule_code")
            params = notif.get("params", {})
            if code in RULE_MESSAGES and code != "TABLE_1_ROUNDING":
                az_msg = RULE_MESSAGES[code]["az"].format(**params) if params else RULE_MESSAGES[code]["az"]
                en_msg = RULE_MESSAGES[code]["en"].format(**params) if params else RULE_MESSAGES[code]["en"]
                print(f"AZ: {az_msg}")
                print(f"EN: {en_msg}")


# ------------------------------------------------------------------------------
# 1. ТЕСТ ПУНКТА 3.7.1: ПОДВИЖНОЙ СОСТАВ НА СВОИХ ОСЯХ (КОЭФФИЦИЕНТ 0.50)
# ------------------------------------------------------------------------------

def test_rolling_stock_on_own_axles_rule_3_7_1():
    """Запуск тестов Правила 3.7.1 (Подвижной состав на своих осях по ГНГ 99222000, Таблица 3/4 x 0.50)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99222000",
        actual_weight=40.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("Запуск тестов Правила 3.7.1 (Подвижной состав по ГНГ 99222000)", route_res, calc_res, "99222000", 40.0, "covered", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "ROLLING_STOCK_AXLES_COEFF_0_50_RULE_3_7_1" in applied_codes


# ------------------------------------------------------------------------------
# 2. ТЕСТ ПУНКТА 3.7.2: ИНВЕНТАРНЫЕ ВАГОНЫ В/ИЗ РЕМОНТА (0.10 CHF/ОСЬ-КМ)
# ------------------------------------------------------------------------------

def test_empty_wagon_repair_rule_3_7_2():
    """Запуск тестов Правила 3.7.2 (Инвентарные вагоны в/из ремонта, 0.10 CHF/ось-км)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99211000",
        actual_weight=0.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False,
        is_empty_wagon=True,
        is_empty_wagon_repair=True,
        axle_count=4
    )

    _print_calculation_result("Запуск тестов Правила 3.7.2 (Инвентарные вагоны в/из ремонта)", route_res, calc_res, "99211000", 0.0, "covered", False)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert calc_res["applied_table"] == "Пункт 3.7.2"
    assert "EMPTY_WAGON_REPAIR_0_10_AXLE_KM_RULE_3_7_2" in applied_codes


# ------------------------------------------------------------------------------
# 3. ТЕСТ ПУНКТА 3.7.3: ПЕРЕВОЗКА В СОСТАВЕ ПАССАЖИРСКОГО ПОЕЗДА (КОЭФФИЦИЕНТ 2.00)
# ------------------------------------------------------------------------------

def test_passenger_train_composition_rule_3_7_3():
    """Запуск тестов Правила 3.7.3 (Перевозка в составе пассажирского поезда, Коэф. 2.00)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="86010000",
        actual_weight=35.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="passenger_wagon",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False,
        is_rolling_stock_on_own_axles=True,
        is_passenger_train_composition=True
    )

    _print_calculation_result("Запуск тестов Правила 3.7.3 (В составе пассажирского поезда)", route_res, calc_res, "86010000", 35.0, "passenger_wagon", False)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "ROLLING_STOCK_PASSENGER_TRAIN_COEFF_2_00_RULE_3_7_3" in applied_codes


# ------------------------------------------------------------------------------
# 4. ТЕСТ ПУНКТА 3.7.5: УЧЕТ МАССЫ ТЕЛЕЖЕК И ЗАПЧАСТЕЙ
# ------------------------------------------------------------------------------

def test_attached_parts_weight_rule_3_7_5():
    """Запуск тестов Правила 3.7.5 (Погрузка вагонных тележек и запчастей в подвижной состав)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="86010000",
        actual_weight=40.0,
        attached_parts_weight=5.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="locomotive",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False,
        is_rolling_stock_on_own_axles=True
    )

    _print_calculation_result("Запуск тестов Правила 3.7.5 (Учет массы тележек и запчастей)", route_res, calc_res, "86010000", 40.0, "locomotive", False)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert calc_res["actual_weight"] == 45
    assert "ATTACHED_PARTS_WEIGHT_ADDED_RULE_3_7_5" in applied_codes


# ------------------------------------------------------------------------------
# 5. ТЕСТ ПУНКТА 3.7.7: БЕСПЛАТНЫЙ ВОЗВРАТ ПОРОЖНЕГО ТРАНСПОРТЕРА ADY
# ------------------------------------------------------------------------------

def test_carrier_transporter_free_return_rule_3_7_7():
    """Запуск тестов Правила 3.7.7 (Бесплатный возврат порожнего транспортера ADY)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Астара")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99211000",
        actual_weight=0.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="transporter",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False,
        is_empty_wagon=True,
        is_transporter=True,
        is_carrier_transporter_free_return=True,
        axle_count=8
    )

    _print_calculation_result("Запуск тестов Правила 3.7.7 (Бесплатный возврат транспортера ADY)", route_res, calc_res, "99211000", 0.0, "transporter", False)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert calc_res["base_rate_chf_per_ton"] == 0.0
    assert "EMPTY_CARRIER_TRANSPORTER_FREE_RULE_3_7_7" in applied_codes


# ------------------------------------------------------------------------------
# 6. ТЕСТ ПУНКТА 3.7.8: ПОРОЖНИЙ 8-ОСНЫЙ ТРАНСПОРТЕР ПО ОСЯМ (0.23 CHF/ОСЬ-КМ)
# ------------------------------------------------------------------------------

def test_empty_transporter_by_axles_rule_3_7_8():
    """Запуск тестов Правила 3.7.8 (Перевозка порожнего 8-осного транспортера по осям)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Астара")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99212000",
        actual_weight=0.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="transporter",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True,
        is_transporter=True,
        axle_count=8
    )

    _print_calculation_result("Запуск тестов Правила 3.7.8 (Порожний 8-осный транспортер)", route_res, calc_res, "99212000", 0.0, "transporter", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert calc_res["applied_table"] == "Пункт 3.7.8"
    assert "TRANSPORTER_AXLE_KM_RATES_RULE_3_7_8" in applied_codes

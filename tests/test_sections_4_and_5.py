# tests/test_sections_4_and_5.py

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

    final_total = calc_res.get("final_rate_total_usd", calc_res.get("final_rate_usd_per_ton"))
    wagon_freight_usd = round(calc_res['final_rate_usd_per_ton'] * calc_res['billable_weight'], 2)

    print("\nДетализация расчёта:")
    print(f"  • Итоговая ставка за тонну: {calc_res['final_rate_usd_per_ton']} USD/т")
    print(f"  • Провозная плата за вагон ({calc_res['billable_weight']} т): {wagon_freight_usd} USD")
    
    print(f"\nИтого: {final_total} USD\n")


def test_household_goods_rule_4():
    """Тест 1: Перевозка домашней утвари (ГНГ 9901, Раздел 4)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99010000",
        actual_weight=15.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("Запуск тестов Раздела 4 (Домашняя утварь ГНГ 9901)", route_res, calc_res, "99010000", 15.0, "covered", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "HOUSEHOLD_GOODS_RULE_4" in applied_codes


def test_cargo_reloaded_split_wagons_rule_5_1_2():
    """Тест 2: Перегрузка из 1 вагона в несколько на границе (п. 5.1.2 / 5.2.1)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="10010000",
        actual_weight=25.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        is_reloaded_part_shipment=True,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("Запуск тестов Раздела 5 (Перегрузка из 1 вагона в несколько, п. 5.1.2)", route_res, calc_res, "10010000", 25.0, "covered", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "CARGO_RELOADED_SPLIT_WAGONS_RULE_5_1_2" in applied_codes

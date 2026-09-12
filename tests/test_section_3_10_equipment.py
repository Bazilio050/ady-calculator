# tests/test_section_3_10_equipment.py

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


def test_equipment_weight_added_rule_3_10_1():
    """Тест 1: Добавление массы средств крепления (п. 3.10.1) — 40 т груза + 3 т оборудования"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="10010000",
        actual_weight=40.0,
        equipment_weight=3.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("Запуск тестов Правила 3.10.1 (Учет массы оборудования)", route_res, calc_res, "10010000", 40.0, "covered", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert calc_res["actual_weight"] == 43
    assert "EQUIPMENT_WEIGHT_ADDED_RULE_3_10_1" in applied_codes


def test_non_removable_equipment_wagon_rule_3_10_4():
    """Тест 2: Порожний вагон с несъёмным оборудованием (п. 3.10.4) — 0.12 CHF / ось-км"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        is_empty_wagon=True,
        is_non_removable_equipment=True,
        axle_count=4,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("Запуск тестов Правила 3.10.4 (Несъёмное оборудование 0.12 CHF/ось-км)", route_res, calc_res, "99210000", 0.0, "covered", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert calc_res["applied_table"] == "Пункт 3.10.4"
    assert "NON_REMOVABLE_EQUIPMENT_WAGON_RULE_3_10_4" in applied_codes

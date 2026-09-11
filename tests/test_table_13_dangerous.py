# tests/test_table_11_oversized.py

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
    print(f"Маршрут: {route_res.from_station.canonical_name} ({route_res.from_station.code}) - {route_res.to_station.canonical_name} ({route_res.to_station.code}) [{route_res.shipment_type.value}] - {route_res.distance_km} км")
    print(f"ГНГ код: {gng_code}")
    print(f"Тип вагона: {wagon_type} [{'приватный' if is_private else 'инвентарный'}]")
    print(f"Вес (факт): {weight} т -> Расчетный (Табл.1/Норма): {calc_res['billable_weight']} т")
    
    base_chf = round(calc_res['base_rate_chf_per_ton'], 2)
    applied_tbl = calc_res.get('applied_table', calc_res.get('table_name'))
    print(f"Базовая ставка: {base_chf} CHF/т ({applied_tbl})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']} USD/т\n")

    notifications = calc_res.get("notifications", [])
    for notif in notifications:
        code = notif.get("rule_code")
        params = notif.get("params", {})
        if code in RULE_MESSAGES and code != "TABLE_1_ROUNDING":
            ru_msg = RULE_MESSAGES[code]["ru"].format(**params) if params else RULE_MESSAGES[code]["ru"]
            print(f"{ru_msg}")

    print(f"\nИтог за 1 т: {calc_res['final_rate_usd_per_ton']} USD/т")
    print(f"Итоговая сумма: {calc_res['final_rate_total_usd']} USD\n")

    if notifications:
        print("Уведомления:")
        for notif in notifications:
            code = notif.get("rule_code")
            params = notif.get("params", {})
            if code in RULE_MESSAGES:
                az_msg = RULE_MESSAGES[code]["az"].format(**params) if params else RULE_MESSAGES[code]["az"]
                en_msg = RULE_MESSAGES[code]["en"].format(**params) if params else RULE_MESSAGES[code]["en"]
                print(f"AZ: {az_msg}")
                print(f"EN: {en_msg}")


# ------------------------------------------------------------------------------
# 1. ТЕСТЫ ДЛЯ РАЗДЕЛА 3.5 (НЕГАБАРИТ И ТАБЛИЦА 11)
# ------------------------------------------------------------------------------

def test_oversized_small_degree_rule_3_5_1_1():
    """Тест 1: Малая степень негабаритности (п. 3.5.1.1, min 25 тонн, Таблица 4)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8401",  # Заменили 2701 на 8401, чтобы проверить округление веса 18т -> 25т
        actual_weight=18.0,
        distance_km=route_res.distance_km,
        wagon_type="platform",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        oversized_degree="small"
    )

    _print_calculation_result("1. Малая степень негабаритности (Ялама -> Беюк Кясик)", route_res, calc_res, "8401", 18.0, "platform", True)
    
    assert calc_res["billable_weight"] == 25.0
    assert calc_res["applied_table"] == "Таблица 4"


def test_oversized_table_11_top_3_degree():
    """Тест 2: 3-я верхняя степень негабаритности (п. 3.5.1.2, Таблица 11, Коэф. 1.50)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8401",
        actual_weight=14.0,
        distance_km=route_res.distance_km,
        wagon_type="platform",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        oversized_degree="3_top"
    )

    _print_calculation_result("2. 3-я верхняя степень негабаритности (Ялама -> Беюк Кясик)", route_res, calc_res, "8401", 14.0, "platform", True)

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert calc_res["applied_table"] == "Таблица 11"
    assert "OVERSIZED_TABLE_11_TOP_3_RULE_3_5_1_2" in rule_codes


def test_oversized_table_11_high_degree():
    """Тест 3: Высокая степень негабаритности 3-5 нижняя / 4-5 боковая (п. 3.5.1.2, Таблица 11, Коэф. 2.00)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8401",
        actual_weight=22.0,
        distance_km=route_res.distance_km,
        wagon_type="platform",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        oversized_degree="3-5_bottom_side"
    )

    _print_calculation_result("3. Высокая степень негабаритности (Ялама -> Беюк Кясик)", route_res, calc_res, "8401", 22.0, "platform", True)

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert calc_res["applied_table"] == "Таблица 11"
    assert "OVERSIZED_TABLE_11_HIGH_DEGREE_RULE_3_5_1_2" in rule_codes


def test_empty_cover_wagons_rule_3_5_3():
    """Тест 4: Вагоны прикрытия / защитные рамки (п. 3.5.3, 0.30 CHF/ось-км)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Астара")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8401",
        actual_weight=30.0,
        distance_km=route_res.distance_km,
        wagon_type="platform",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        cover_wagons_count=2,
        is_cover_wagon_private=True
    )

    _print_calculation_result("4. Вагоны прикрытия (Ялама -> Астара)", route_res, calc_res, "8401", 30.0, "platform", True)

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert "EMPTY_COVER_WAGON_AXLE_KM_RULE_3_5_3" in rule_codes

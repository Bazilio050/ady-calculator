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
    print(f"Маршрут: {route_res.from_station.canonical_name} ({route_res.from_station.code}) - {route_res.to_station.canonical_name} ({route_res.to_station.code}) [{route_res.shipment_type.value}] - {route_res.distance_km} км")
    print(f"ГНГ код: {gng_code}")
    print(f"Тип вагона: {wagon_type} [{'приватный' if is_private else 'инвентарный'}]")
    print(f"Вес (факт): {weight} т -> Расчетный (Табл.1/Норма): {calc_res['billable_weight']} т")
    
    base_chf = round(calc_res['base_rate_chf_per_ton'], 2)
    applied_tbl = calc_res.get('applied_table', calc_res.get('table_name'))
    print(f"Базовая ставка: {base_chf} CHF ({applied_tbl})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']} USD\n")

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
# ТЕСТЫ ДЛЯ РАЗДЕЛА 3.7 (ПОДВИЖНОЙ СОСТАВ НА СВОИХ ОСЯХ)
# ------------------------------------------------------------------------------

def test_rolling_stock_on_own_axles_rule_3_7_1():
    """Тест 1: Перевозка локомотива/подвижного состава на своих осях (п. 3.7.1, коэф. 0.50 к универсальному вагону)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8601",
        actual_weight=40.0,
        distance_km=route_res.distance_km,
        wagon_type="locomotive",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False,
        is_rolling_stock_on_own_axles=True
    )

    _print_calculation_result("1. Подвижной состав на своих осях (Ялама -> Беюк Кясик)", route_res, calc_res, "8601", 40.0, "locomotive", False)

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert "ROLLING_STOCK_AXLES_COEFF_0_50_RULE_3_7_1" in rule_codes


def test_empty_wagon_repair_rule_3_7_2():
    """Тест 2: Инвентарный вагон в ремонт / из ремонта (п. 3.7.2, 0.10 CHF/ось-км)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="9921",
        actual_weight=0.0,
        distance_km=route_res.distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False,
        is_empty_wagon=True,
        is_empty_wagon_repair=True,
        axle_count=4
    )

    _print_calculation_result("2. Инвентарный вагон в ремонт (Ялама -> Беюк Кясик)", route_res, calc_res, "9921", 0.0, "covered", False)

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert calc_res["applied_table"] == "Пункт 3.7.2"
    assert "EMPTY_WAGON_REPAIR_0_10_AXLE_KM_RULE_3_7_2" in rule_codes


def test_empty_transporter_by_axles_rule_3_7_8():
    """Тест 3: Перевозка порожнего 8-осного транспортера (п. 3.7.8, 0.23 CHF/ось-км)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Астара")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="9921",
        actual_weight=0.0,
        distance_km=route_res.distance_km,
        wagon_type="transporter",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True,
        is_transporter=True,
        axle_count=8
    )

    _print_calculation_result("3. Порожний 8-осный транспортер (Ялама -> Астара)", route_res, calc_res, "9921", 0.0, "transporter", True)

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert calc_res["applied_table"] == "Пункт 3.7.8"
    assert "TRANSPORTER_AXLE_KM_RATES_RULE_3_7_8" in rule_codes

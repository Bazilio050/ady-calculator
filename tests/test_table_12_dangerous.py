# tests/test_table_12_dangerous.py

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
# 1. ТЕСТЫ ДЛЯ РАЗДЕЛА 3.6 (ОПАСНЫЕ ГРУЗЫ И ТАБЛИЦА 12)
# ------------------------------------------------------------------------------

def test_dangerous_cargo_table_12_wagon():
    """Тест 1: Перевозка опасного груза в универсальном вагоне (Таблица 12, п. 3.6.1)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="2801",  # Бром/хлор
        actual_weight=22.0,
        distance_km=route_res.distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_dangerous_cargo=True
    )

    _print_calculation_result("1. Опасный груз в вагоне (Ялама -> Беюк Кясик)", route_res, calc_res, "2801", 22.0, "covered", True)

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert calc_res["applied_table"] == "Таблица 12"
    assert "DANGEROUS_CARGO_COEFF_2_00_RULE_3_6_1" in rule_codes


def test_dangerous_cargo_cistern_table_6():
    """Тест 2: Перевозка опасного груза в цистерне (Таблица 6, Коэф. 2.00, п. 3.6.1)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="2710",
        actual_weight=30.0,
        distance_km=route_res.distance_km,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_dangerous_cargo=True
    )

    _print_calculation_result("2. Опасный груз в цистерне (Ялама -> Беюк Кясик)", route_res, calc_res, "2710", 30.0, "cistern", True)

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert calc_res["applied_table"] == "Таблица 6"
    assert "DANGEROUS_CARGO_COEFF_2_00_RULE_3_6_1" in rule_codes

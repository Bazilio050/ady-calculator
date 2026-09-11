# tests/test_containers_next.py

import pytest
from core.router import RailwayRouter
from core.calculator import TariffCalculator
from data.translations import RULE_MESSAGES


def _print_test_header(title: str):
    print(f"\n{'='*70}\n{title}\n{'='*70}")


def _print_calculation_result(title: str, route_res, calc_res, gng_code: str, weight: float, wagon_type: str, is_private: bool):
    _print_test_header(title)
    display_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km
    print(f"Маршрут: {route_res.from_station.canonical_name} ({route_res.from_station.code}) - {route_res.to_station.canonical_name} ({route_res.to_station.code}) [{route_res.shipment_type.value}] - {display_dist} км")
    print(f"ГНГ код: {gng_code}")
    print(f"Тип вагона/контейнера: {wagon_type} [{'СПС (приватный)' if is_private else 'СПС (инвентарный)'}]")
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

    print(f"\nИтоговый тариф: {calc_res['final_rate_usd_per_ton']} USD\n")

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
# ТЕСТЫ ДЛЯ СПЕЦИАЛИЗИРОВАННЫХ КОНТЕЙНЕРОВ (ТАБЛИЦА 8 + КОЭФФИЦИЕНТЫ)
# ------------------------------------------------------------------------------

def test_diesel_generator_container_coeff():
    """Тест 1: Контейнер-дизель-генератор по Таблице 8 с коэффициентом 1.35 (п. 3.4.5)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99310000",
        actual_weight=20.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="diesel_generator_container",
        container_category_tons=20,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("1. Контейнер-дизель-генератор (Таблица 8 x 1.35)", route_res, calc_res, "99310000", 20.0, "diesel_generator_container", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "DIESEL_GENERATOR_CONTAINER_COEFF_1_35" in applied_codes


def test_container_platform_coeff_1_40():
    """Тест 2: Контейнер-платформа (Flatrack) по Таблице 8 с коэффициентом 1.40 (п. 3.4.6)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99310000",
        actual_weight=20.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="container_platform",
        container_category_tons=20,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("2. Контейнер-платформа Flatrack (Таблица 8 x 1.40)", route_res, calc_res, "99310000", 20.0, "container_platform", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "CONTAINER_PLATFORM_COEFF_1_40" in applied_codes


def test_open_top_container_coeff_1_40():
    """Тест 3: Открытый контейнер (Open Top) по Таблице 8 с коэффициентом 1.40 (п. 3.4.7)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99310000",
        actual_weight=20.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="open_top_container",
        container_category_tons=20,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("3. Открытый контейнер Open Top (Таблица 8 x 1.40)", route_res, calc_res, "99310000", 20.0, "open_top_container", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "OPEN_TOP_CONTAINER_COEFF_1_40" in applied_codes


def test_special_purpose_container_coeff_1_40():
    """Тест 4: Контейнер специального назначения по Таблице 8 с коэффициентом 1.40 (п. 3.4.8)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99310000",
        actual_weight=20.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="special_purpose_container",
        container_category_tons=20,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("4. Контейнер специального назначения (Таблица 8 x 1.40)", route_res, calc_res, "99310000", 20.0, "special_purpose_container", True)

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "SPECIAL_PURPOSE_CONTAINER_COEFF_1_40" in applied_codes

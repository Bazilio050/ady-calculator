# tests/test_rule_3_4_3_1.py

import pytest
from core.router import RailwayRouter
from core.calculator import TariffCalculator
from data.translations import RULE_MESSAGES


def _print_test_header(title: str):
    """Печатает стандартизированный заголовок для каждого тестового сценария."""
    print(f"\n{'='*70}\n{title}\n{'='*70}")


def _print_calculation_result(
    title: str,
    route_res,
    calc_res,
    gng_code: str,
    weight: float,
    equipment_type: str
):
    """Выводит детализированные результаты расчета."""
    _print_test_header(title)
    display_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km
    print(
        f"Маршрут: {route_res.from_station.canonical_name} ({route_res.from_station.code}) - "
        f"{route_res.to_station.canonical_name} ({route_res.to_station.code}) "
        f"[{route_res.shipment_type.value}] - {display_dist} км"
    )
    print(f"Код ГНГ / Груз: {gng_code}")
    print(f"Тип подвижного состава: {equipment_type}")
    print(f"Фактический вес: {weight} т -> Расчетный: {calc_res['billable_weight']} т")

    base_chf = round(calc_res['base_rate_chf_per_ton'], 2)
    applied_tbl = calc_res.get('applied_table', calc_res.get('table_name'))
    print(f"Базовая ставка из Таблицы 10: {base_chf} CHF ({applied_tbl})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Итоговый тариф в USD: {calc_res['final_rate_usd_per_ton']} USD\n")

    all_notifications = []
    if route_res.rule_code:
        all_notifications.append({"rule_code": route_res.rule_code, "params": route_res.params})
    all_notifications.extend(calc_res.get("notifications", []))

    for notif in all_notifications:
        code = notif.get("rule_code")
        params = notif.get("params", {})
        if code in RULE_MESSAGES:
            ru_msg = RULE_MESSAGES[code]["ru"].format(**params) if params else RULE_MESSAGES[code]["ru"]
            print(f"{ru_msg}")


# ------------------------------------------------------------------------------
# ТЕСТЫ ТАНК-КОНТЕЙНЕРОВ (Tank konteynerlər: 20 фут, 40 фут, Гружёные / Порожние)
# ------------------------------------------------------------------------------

def test_tank_container_20ft_loaded_transit():
    """1. Танк-контейнер 20 фут, Гружёный [Транзит: Ялама -> БК]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="27101981",
        actual_weight=20.0,
        distance_km=effective_dist,
        wagon_type="tank_container",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=False,
        container_category_tons=20
    )

    _print_calculation_result("1. Танк-контейнер 20 фут (Гружёный) [Транзит]", route_res, calc_res, "27101981", 20.0, "tank_container 20ft")
    assert calc_res["applied_table"] == "Таблица 10"
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_tank_container_40ft_empty_import():
    """2. Танк-контейнер 40 фут, Порожний [Импорт: Ялама -> Абшерон]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Абшерон")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=effective_dist,
        wagon_type="tank_container",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True,
        container_category_tons=40
    )

    _print_calculation_result("2. Танк-контейнер 40 фут (Порожний) [Импорт]", route_res, calc_res, "99210000", 0.0, "tank_container 40ft empty")
    assert calc_res["applied_table"] == "Таблица 10"
    assert calc_res["base_rate_chf_per_ton"] > 0


# ------------------------------------------------------------------------------
# ТЕСТЫ КОНТЕЙНЕРОВ С ВИНОМ И СОКАМИ (Şərab və meyvə şirəsi yükləri)
# ------------------------------------------------------------------------------

def test_wine_juice_container_20ft_export():
    """3. Контейнер с вином/соком 20 фут [Экспорт: Гянджа -> Ялама]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Гянджа", "Ялама")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="22042111",
        actual_weight=18.0,
        distance_km=effective_dist,
        wagon_type="wine_juice_container",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=False,
        container_category_tons=20
    )

    _print_calculation_result("3. Контейнер Вино/Сок 20 фут (Гружёный) [Экспорт]", route_res, calc_res, "22042111", 18.0, "wine_juice_container 20ft")
    assert calc_res["applied_table"] == "Таблица 10"
    assert calc_res["base_rate_chf_per_ton"] > 0


# ------------------------------------------------------------------------------
# ТЕСТЫ РЕФКОНТЕЙНЕРОВ (Refkonteynerlər: 20 фут, 40 фут, Гружёные / Порожние)
# ------------------------------------------------------------------------------

def test_reefer_container_40ft_loaded_transit():
    """4. Рефконтейнер 40 фут, Гружёный [Транзит: Ялама -> БК]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="08081080",
        actual_weight=22.0,
        distance_km=effective_dist,
        wagon_type="reefer_container",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=False,
        container_category_tons=40
    )

    _print_calculation_result("4. Рефконтейнер 40 фут (Гружёный) [Транзит]", route_res, calc_res, "08081080", 22.0, "reefer_container 40ft")
    assert calc_res["applied_table"] == "Таблица 10"
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_reefer_container_20ft_empty_export():
    """5. Рефконтейнер 20 фут, Порожний [Экспорт: Абшерон -> Ялама]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Абшерон", "Ялама")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=effective_dist,
        wagon_type="reefer_container",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True,
        container_category_tons=20
    )

    _print_calculation_result("5. Рефконтейнер 20 фут (Порожний) [Экспорт]", route_res, calc_res, "99210000", 0.0, "reefer_container 20ft empty")
    assert calc_res["applied_table"] == "Таблица 10"
    assert calc_res["base_rate_chf_per_ton"] > 0

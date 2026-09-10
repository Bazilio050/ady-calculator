# tests/test_rule_3_4_3_1.py

# ------------------------------------------------------------------------------
# БЛОК 1: Импорт библиотек и вспомогательных модулей
# ------------------------------------------------------------------------------
import pytest
from core.router import RailwayRouter
from core.calculator import TariffCalculator
from data.translations import RULE_MESSAGES


# ------------------------------------------------------------------------------
# БЛОК 2: Вспомогательные функции форматирования вывода
# ------------------------------------------------------------------------------
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
    """ Выводит детализированные результаты расчета. """
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
        if code in RULE_MESSAGES:
            ru_msg = RULE_MESSAGES[code]["ru"].format(**params) if params else RULE_MESSAGES[code]["ru"]
            print(f"{ru_msg}")

    print(f"\nИтоговый тариф: {calc_res['final_rate_usd_per_ton']} USD\n")


# ------------------------------------------------------------------------------
# БЛОК 3: Тестовые сценарии для Пункта 3.4.3.1
# ------------------------------------------------------------------------------

def test_rule_3_4_3_1_tank_container_loaded():
    """Тест 1: Гружёный 20-футовый танк-контейнер (Таблица 10 + коэффициент 1.40) [Транзит]"""
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

    _print_calculation_result(
        "1. Гружёный танк-контейнер 20 фут (Таблица 10 + К=1.40)",
        route_res, calc_res, "27101981", 20.0, "tank_container"
    )
    assert calc_res["applied_table"] == "Таблица 10"
    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", [])]
    assert "SPECIAL_CONTAINER_TANK_REF_RULE_3_4_3_1" in applied_codes
    assert "TANK_CONTAINER_COEFF_1_40_RULE_3_4_3_1" in applied_codes


def test_rule_3_4_3_1_reefer_container_loaded():
    """Тест 2: Гружёный 40-футовый рефконтейнер (Таблица 10, без коэффициента 1.40) [Импорт]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Абшерон")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="08081080",
        actual_weight=18.0,
        distance_km=effective_dist,
        wagon_type="reefer_container",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=False,
        container_category_tons=40
    )

    _print_calculation_result(
        "2. Гружёный рефконтейнер 40 фут (Таблица 10)",
        route_res, calc_res, "08081080", 18.0, "reefer_container"
    )
    assert calc_res["applied_table"] == "Таблица 10"
    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", [])]
    assert "SPECIAL_CONTAINER_TANK_REF_RULE_3_4_3_1" in applied_codes
    assert "TANK_CONTAINER_COEFF_1_40_RULE_3_4_3_1" not in applied_codes

# tests/test_rule_3_3_2.py

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
    """
    Выводит детализированные результаты расчета на русском, азербайджанском и английском языках.
    """
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

    # Собираем уведомления от Роутера и Калькулятора
    all_notifications = []
    if route_res.rule_code:
        all_notifications.append({"rule_code": route_res.rule_code, "params": route_res.params})
    all_notifications.extend(calc_res.get("notifications", []))

    # Вывод локализованных сообщений на русском языке
    for notif in all_notifications:
        code = notif.get("rule_code")
        params = notif.get("params", {})
        if code in RULE_MESSAGES:
            ru_msg = RULE_MESSAGES[code]["ru"].format(**params) if params else RULE_MESSAGES[code]["ru"]
            print(f"{ru_msg}")

    print(f"\nИтоговый тариф: {calc_res['final_rate_usd_per_ton']} USD\n")

    # Вывод мультиязычных уведомлений (AZ / EN)
    if all_notifications:
        print("Уведомления (AZ / EN):")
        for notif in all_notifications:
            code = notif.get("rule_code")
            params = notif.get("params", {})
            if code in RULE_MESSAGES:
                az_msg = RULE_MESSAGES[code]["az"].format(**params) if params else RULE_MESSAGES[code]["az"]
                en_msg = RULE_MESSAGES[code]["en"].format(**params) if params else RULE_MESSAGES[code]["en"]
                print(f"AZ: {az_msg}")
                print(f"EN: {en_msg}")


# ------------------------------------------------------------------------------
# БЛОК 3: Тестовые сценарии для Пункта 3.3.2 (Порожняя автотехника на спецплатформах)
# ------------------------------------------------------------------------------

def test_rule_3_3_2_empty_road_train_transit():
    """Тест 1: Порожний автопоезд (расчетная масса 7 тонн) [Транзит: Ялама -> Беюк Кясик]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99220000",
        actual_weight=0.0,
        distance_km=effective_dist,
        wagon_type="road_train",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True
    )

    _print_calculation_result(
        "1. Порожний автопоезд (7т) [Транзит: Ялама -> Беюк Кясик]",
        route_res, calc_res, "99220000", 0.0, "road_train (Автопоезд)"
    )
    assert calc_res["billable_weight"] == 7.0
    assert calc_res["applied_table"] == "Таблица 5"
    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", [])]
    assert "EMPTY_ROAD_TRAIN_WEIGHT_7T_RULE_3_3_2" in applied_codes


def test_rule_3_3_2_empty_auto_body_import():
    """Тест 2: Порожний съемный автокузов (расчетная масса 5 тонн) [Импорт: Ялама -> Абшерон]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Абшерон")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99220000",
        actual_weight=0.0,
        distance_km=effective_dist,
        wagon_type="auto_body",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True
    )

    _print_calculation_result(
        "2. Порожний съемный кузов (5т) [Импорт: Ялама -> Абшерон]",
        route_res, calc_res, "99220000", 0.0, "auto_body (Съемный кузов)"
    )
    assert calc_res["billable_weight"] == 5.0
    assert calc_res["applied_table"] == "Таблица 5"
    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", [])]
    assert "EMPTY_AUTO_BODY_WEIGHT_5T_RULE_3_3_2" in applied_codes

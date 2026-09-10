# tests/test_rule_3_3_1.py

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
# БЛОК 3: Тестовые сценарии для Пункта 3.3.1 (Груженые İNV / ANV на спецплатформах)
# ------------------------------------------------------------------------------

def test_rule_3_3_1_inv_import_min_weight():
    """Тест 1: Гружёный İNV весом 6 тонн (меньше 10т) — Норматив 10т [Импорт: Ялама -> Абшерон]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Абшерон")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="87163900",
        actual_weight=6.0,  # Фактический вес 6т < 10т
        distance_km=effective_dist,
        wagon_type="inv",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=False
    )

    _print_calculation_result(
        "1. Перевозка İNV (6т -> мин. 10т) [Импорт: Ялама -> Абшерон]",
        route_res, calc_res, "87163900", 6.0, "inv (Интермодальное ТС)"
    )
    assert calc_res["billable_weight"] == 10.0
    assert calc_res["applied_table"] == "Таблица 5"
    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", [])]
    assert "INV_ANV_MIN_WEIGHT_10T_RULE_3_3_1" in applied_codes


def test_rule_3_3_1_anv_export_min_weight():
    """Тест 2: Гружёный ANV весом 8 тонн (меньше 10т) — Норматив 10т [Экспорт: Гянджа -> Ялама]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Гянджа", "Ялама")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="87163900",
        actual_weight=8.0,  # Фактический вес 8т < 10т
        distance_km=effective_dist,
        wagon_type="anv",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=False
    )

    _print_calculation_result(
        "2. Перевозка ANV (8т -> мин. 10т) [Экспорт: Гянджа -> Ялама]",
        route_res, calc_res, "87163900", 8.0, "anv (Автотранспортное ТС)"
    )
    assert calc_res["billable_weight"] == 10.0
    assert calc_res["applied_table"] == "Таблица 5"
    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", [])]
    assert "INV_ANV_MIN_WEIGHT_10T_RULE_3_3_1" in applied_codes


def test_rule_3_3_1_inv_transit_above_min_weight():
    """Тест 3: Гружёный İNV весом 14 тонн (больше 10т) — Сохранение 14т [Транзит: Ялама -> Беюк Кясик]"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="87163900",
        actual_weight=14.0,  # Фактический вес 14т > 10т
        distance_km=effective_dist,
        wagon_type="inv",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=False
    )

    _print_calculation_result(
        "3. Перевозка İNV (14т > 10т) [Транзит: Ялама -> Беюк Кясик]",
        route_res, calc_res, "87163900", 14.0, "inv (Интермодальное ТС)"
    )
    assert calc_res["billable_weight"] == 14.0
    assert calc_res["applied_table"] == "Таблица 5"

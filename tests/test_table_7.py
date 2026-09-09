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
    calc_type: str
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
    print(f"Тип расчета Таблицы 7 / Вагон: {calc_type}")
    print(f"Фактический вес/объем: {weight} т -> Расчетный: {calc_res['billable_weight']} т")

    base_chf = round(calc_res['base_rate_chf_per_ton'], 2)
    applied_tbl = calc_res.get('applied_table', calc_res.get('table_name'))
    print(f"Базовая ставка: {base_chf} CHF ({applied_tbl})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']} USD\n")

    # Собираем уведомления от Роутера (минимальное расстояние) и от Калькулятора
    all_notifications = []
    if route_res.rule_code:
        all_notifications.append({"rule_code": route_res.rule_code, "params": route_res.params})
    all_notifications.extend(calc_res.get("notifications", []))

    # Вывод версий на русском языке
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
# БЛОК 3: Тестовые сценарии для Таблицы 7 и правила 3.1.2.6
# ------------------------------------------------------------------------------

def test_table_7_small_tonnage_5t_wagon_import():
    """Тест 1: Повагонная отправка малой тоннажности (5 тонн) — Импорт (Ялама -> Абшерон)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Абшерон")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="10019000",
        actual_weight=5.0,
        distance_km=effective_dist,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        calc_type_table_7="wagon_small_tonnage",
        weight_category_table_7=5
    )

    _print_calculation_result(
        "1. Малотоннажная отправка вагона (5т) [Импорт: Ялама -> Абшерон]",
        route_res, calc_res, "10019000", 5.0, "wagon_small_tonnage (5t)"
    )
    assert calc_res["base_rate_chf_per_ton"] > 0
    assert calc_res["applied_table"] == "Таблица 7"


def test_table_7_postal_shipment_66t_transit():
    """Тест 2: Пассажирский/Почтовый вагон ГНГ 99910000 (мин. 66т) — Транзит (Ялама -> Беюк Кясик)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99910000",
        actual_weight=20.0,
        distance_km=effective_dist,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name
    )

    _print_calculation_result(
        "2. Почтовое / Пассажирское отправление ГНГ 99910000 [Транзит: Ялама -> Беюк Кясик]",
        route_res, calc_res, "99910000", 20.0, "postal_passenger_wagon"
    )
    assert calc_res["base_rate_chf_per_ton"] > 0
    assert calc_res["billable_weight"] == 66.0
    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", [])]
    assert "TABLE_7_MIN_PASSENGER_POSTAL_WEIGHT_66T" in applied_codes


def test_transporter_6_axle_min_weight_rule_3_1_2_6():
    """Тест 3: Перевозка на 6-осном транспортере по п. 3.1.2.6 (мин. 5т/ось -> 30т) — Транзит (Ялама -> Беюк Кясик)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "БК")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="84119900",
        actual_weight=12.0,  # Фактический вес 12т (ниже 30т для 6 осей)
        distance_km=effective_dist,
        wagon_type="transporter",
        axle_count=6,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result(
        "3. Перевозка на 6-осном транспортере (п. 3.1.2.6 | Мин. 30 тонн) [Транзит: Ялама -> Беюк Кясик]",
        route_res, calc_res, "84119900", 12.0, "transporter (6 axles)"
    )
    assert calc_res["billable_weight"] == 30.0
    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", [])]
    assert "MIN_WEIGHT_TRANSPORTER_AXLE_NORMATIVE" in applied_codes

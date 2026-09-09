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
    axle_count: int
):
    """
    Выводит детализированные результаты расчета порожнего вагона по п. 3.2.2.
    """
    _print_test_header(title)
    display_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km
    print(
        f"Маршрут: {route_res.from_station.canonical_name} ({route_res.from_station.code}) - "
        f"{route_res.to_station.canonical_name} ({route_res.to_station.code}) "
        f"[{route_res.shipment_type.value}] - {display_dist} км"
    )
    print(f"Код ГНГ: {gng_code}")
    print(f"Количество осей вагона: {axle_count}")
    print(f"Фактический вес/объем: {calc_res['actual_weight']} т (Порожний вагон)")

    base_chf = round(calc_res['base_rate_chf_per_ton'], 2)
    applied_tbl = calc_res.get('applied_table', calc_res.get('table_name'))
    print(f"Базовая ставка: {base_chf} CHF ({applied_tbl})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']} USD\n")

    # Собираем уведомления
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
# БЛОК 3: Тестовые сценарии для правила 3.2.2 (Порожний приватный вагон)
# ------------------------------------------------------------------------------

def test_empty_private_wagon_ganja_yalama():
    """Тест 1: Порожний приватный вагон (4 оси) — Гянджа -> Ялама"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Гянджа", "Ялама")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=effective_dist,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True,
        axle_count=4
    )

    _print_calculation_result(
        "1. Порожний приватный вагон (4 оси) [Гянджа -> Ялама]",
        route_res, calc_res, "99210000", 4
    )

    expected_chf = effective_dist * 4 * 0.10
    assert calc_res["base_rate_chf_per_ton"] == expected_chf
    assert calc_res["applied_table"] == "Пункт 3.2.2"


def test_empty_private_wagon_boyuk_kasik_kuryk():
    """Тест 2: Порожний приватный вагон (4 оси) — Беюк Кясик -> Курык (Транзит)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Беюк Кясик", "Курык")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=effective_dist,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True,
        axle_count=4
    )

    _print_calculation_result(
        "2. Порожний приватный вагон (4 оси) [Беюк Кясик -> Курык]",
        route_res, calc_res, "99210000", 4
    )

    expected_chf = effective_dist * 4 * 0.10
    assert calc_res["base_rate_chf_per_ton"] == expected_chf
    assert calc_res["applied_table"] == "Пункт 3.2.2"


def test_empty_private_wagon_8_axles_alyat_exp_yalama():
    """Тест 3: Порожний приватный вагон (8 осей) — Алят эксп. -> Ялама"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Алят-экспорт", "Ялама")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=effective_dist,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_empty_wagon=True,
        axle_count=8
    )

    _print_calculation_result(
        "3. Порожний приватный вагон (8 осей) [Алят эксп. -> Ялама]",
        route_res, calc_res, "99210000", 8
    )

    expected_chf = effective_dist * 8 * 0.10
    assert calc_res["base_rate_chf_per_ton"] == expected_chf
    assert calc_res["applied_table"] == "Пункт 3.2.2"

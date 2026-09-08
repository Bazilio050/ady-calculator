# tests/test_table_5_full.py

import pytest
from core.router import RailwayRouter
from core.calculator import TariffCalculator
from data.translations import RULE_MESSAGES


def _print_test_header(title: str):
    print(f"\n{'='*70}\n{title}\n{'='*70}")


def _print_calculation_result(title: str, route_res, calc_res, gng_code: str, weight: float, wagon_type: str, is_private: bool):
    _print_test_header(title)
    print(f"Маршрут: {route_res.from_station.canonical_name} ({route_res.from_station.code}) - {route_res.to_station.canonical_name} ({route_res.to_station.code}) [{route_res.shipment_type.value}] - {route_res.distance_km} км")
    print(f"ГНГ код: {gng_code}")
    print(f"Тип вагона: {wagon_type} [{'СПС (приватный)' if is_private else 'СПС (инвентарный)'}]")
    print(f"Вес (факт): {weight} т -> Расчетный (Табл.1/Норма): {calc_res['billable_weight']} т")
    
    base_chf = round(calc_res['base_rate_chf_per_ton'], 2)
    applied_tbl = calc_res.get('applied_table', calc_res.get('table_name'))
    print(f"Базовая ставка: {base_chf} CHF/т ({applied_tbl})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']} USD/т\n")

    # Вывод коэффициентов из словаря переводов (RU версия)
    notifications = calc_res.get("notifications", [])
    for notif in notifications:
        code = notif.get("rule_code")
        params = notif.get("params", {})
        if code in RULE_MESSAGES and code != "TABLE_1_ROUNDING":
            ru_msg = RULE_MESSAGES[code]["ru"].format(**params) if params else RULE_MESSAGES[code]["ru"]
            print(f"{ru_msg}")

    print(f"\nИтог за 1 т: {calc_res['final_rate_usd_per_ton']} USD/т\n")

    # Вывод двуязычных уведомлений AZ и EN из центрального словаря
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
# 1. ТЕСТЫ ДЛЯ СЕКЦИОННОСТИ РЕФРИЖЕРАТОРОВ (П. 3.1.2.1)
# ------------------------------------------------------------------------------

def test_ref_section_2_1_transit():
    """Тест 1: Рефсекция 2+1 (Курык -> Беюк Кясик, Коэф. 1.40)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Курык", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0404",
        actual_weight=28,
        distance_km=route_res.distance_km,
        wagon_type="refrigerator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        ref_section_wagons_count=2
    )

    _print_calculation_result("1. Рефсекция 2+1 (Курык -> Беюк Кясик)", route_res, calc_res, "0404", 28, "refrigerator (2+1)", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_ref_section_3_1_import():
    """Тест 2: Рефсекция 3+1 (Ялама -> Алят-эксп., Коэф. 1.10)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Ələt eksport-Kurik")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0404",
        actual_weight=28,
        distance_km=effective_dist,
        wagon_type="refrigerator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        ref_section_wagons_count=3
    )

    _print_calculation_result("2. Рефсекция 3+1 (Ялама -> Алят-эксп.)", route_res, calc_res, "0404", 28, "refrigerator (3+1)", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_ref_section_4_1_export():
    """Тест 3: Рефсекция 4+1 (Баку-Товарная -> Астара, Коэф. 1.00)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Баку-Товарная", "Астара")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0404",
        actual_weight=28,
        distance_km=effective_dist,
        wagon_type="refrigerator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        ref_section_wagons_count=4
    )

    _print_calculation_result("3. Рефсекция 4+1 (Баку-Товарная -> Астара)", route_res, calc_res, "0404", 28, "refrigerator (4+1)", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_ref_section_5_1_import():
    """Тест 4: Рефсекция 5+1 (Ялама -> Апшерон, Коэф. 0.85)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Апшерон")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0404",
        actual_weight=28,
        distance_km=effective_dist,
        wagon_type="refrigerator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        ref_section_wagons_count=5
    )

    _print_calculation_result("4. Рефсекция 5+1 (Ялама -> Апшерон)", route_res, calc_res, "0404", 28, "refrigerator (5+1)", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_ref_section_6_1_import():
    """Тест 5: Рефсекция 6+1 (Апшерон -> Ялама, Коэф. 0.85)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Апшерон", "Ялама")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0404",
        actual_weight=28,
        distance_km=effective_dist,
        wagon_type="refrigerator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        ref_section_wagons_count=6
    )

    _print_calculation_result("5. Рефсекция 6+1 (Апшерон -> Ялама)", route_res, calc_res, "0404", 28, "refrigerator (6+1)", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


# ------------------------------------------------------------------------------
# 2. ТЕСТЫ ДЛЯ СПЕЦИАЛЬНЫХ ПРАВИЛ ТАБЛИЦЫ 5
# ------------------------------------------------------------------------------

def test_diesel_generator_axle_rate():
    """Тест 6: Дизель-генераторный вагон (0.12 CHF / ось-км)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Астара")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0000",
        actual_weight=0,
        distance_km=route_res.distance_km,
        wagon_type="diesel_generator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        axle_count=4
    )

    _print_calculation_result("6. Дизель-генератор (Ялама -> Астара)", route_res, calc_res, "0000", 0, "diesel_generator", True)
    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert "REF_DIESEL_GENERATOR_AXLE_RATE" in rule_codes


def test_fruit_veg_discount_tariff_agreement():
    """Тест 7: Овощи/фрукты из стран ТС (Коэф. 0.60)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Апшерон")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="08081000",  # Яблоки
        actual_weight=28,
        distance_km=route_res.distance_km,
        wagon_type="refrigerator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_tariff_agreement_origin=True
    )

    _print_calculation_result("7. Овощи/фрукты ТС (Ялама -> Апшерон)", route_res, calc_res, "08081000", 28, "refrigerator", True)
    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert "REF_FRUIT_VEG_COEFF_0_60" in rule_codes


def test_empty_wagon_in_loaded_ref_section():
    """Тест 8: Порожний вагон в гружёной секции (0.10 CHF / ось-км)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0000",
        actual_weight=0,
        distance_km=route_res.distance_km,
        wagon_type="refrigerator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        is_in_loaded_ref_section=True,
        axle_count=4
    )

    _print_calculation_result("8. Порожний вагон в гружёной секции (Ялама -> Беюк Кясик)", route_res, calc_res, "0000", 0, "refrigerator (empty in loaded section)", True)
    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert "REF_EMPTY_WAGON_IN_LOADED_SECTION_AXLE_RATE" in rule_codes


def test_two_tier_car_carrier_platform():
    """Тест 9: Двухъярусная платформа-автовоз (Коэф. 0.80)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Баку-Товарная", "Гянджа")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8703",
        actual_weight=15,
        distance_km=route_res.distance_km,
        wagon_type="two_tier_platform",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("9. Двухъярусная платформа-автовоз (Баку -> Гянджа)", route_res, calc_res, "8703", 15, "two_tier_platform", True)
    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert "CAR_CARRIER_TWO_TIER_COEFF_0_80" in rule_codes

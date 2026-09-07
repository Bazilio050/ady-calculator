import pytest
from core.router import RailwayRouter
from core.calculator import TariffCalculator


def _print_test_header(title: str):
    print(f"\n{'='*70}\n{title}\n{'='*70}")


def _print_calculation_result(title: str, route_res, calc_res, gng_code: str, weight: float, wagon_type: str, is_private: bool):
    _print_test_header(title)
    print(f"Маршрут: {route_res.from_station.canonical_name} ({route_res.from_station.code}) - {route_res.to_station.canonical_name} ({route_res.to_station.code}) [{route_res.shipment_type.value}] - {route_res.distance_km} км")
    print(f"ГНГ код: {gng_code}")
    print(f"Тип вагона: {wagon_type} [{'СПС (приватный)' if is_private else 'СПС (инвентарный)'}]")
    print(f"Вес (факт): {weight} т -> Расчетный (Табл.1/Норма): {calc_res['billable_weight']} т")
    print(f"Базовая ставка: {calc_res['base_rate_chf_per_ton']} CHF/т ({calc_res['applied_table']})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate_chf_to_usd']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']:.2f} USD/т\n")

    if calc_res.get("applied_coefficients"):
        for coeff in calc_res["applied_coefficients"]:
            print(f"Коэф. {coeff['value']:.2f}: {coeff['description']}")
        print()

    print(f"Итог за 1 т: {calc_res['final_rate_usd_per_ton']:.2f} USD/т\n")

    if calc_res.get("formatted_notifications"):
        print("Уведомления:")
        for lang, msgs in calc_res["formatted_notifications"].items():
            for msg in msgs:
                print(f"{lang.upper()}: {msg}")
    print("="*70)


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

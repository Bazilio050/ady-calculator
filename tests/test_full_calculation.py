# tests/test_full_calculation.py

from core.router import RailwayRouter
from core.calculator import TariffCalculator


def _print_calculation_result(test_name: str, route_res, calc_res, gng_code: str, actual_w: int):
    """Вспомогательная функция для красивого визуального вывода результатов."""
    print("\n" + "=" * 80)
    print(f"   {test_name.upper()}")
    print("=" * 80)
    print(f"Маршрут:       {route_res.formatted_output('RU')}")
    print(f"ГНГ код:       {gng_code}")
    print(f"Вес (факт):    {actual_w} т -> Расчетный (Табл.1/Норма): {calc_res['billable_weight']} т")
    print(f"Базовая ставка: {calc_res['base_rate_chf_per_ton']} CHF/т (Таблица 3)")
    print(f"Коэффициент:   {calc_res['final_coeff']}")
    print(f"Итог за 1 т:   {calc_res['final_rate_chf_per_ton']} CHF/т")

    if calc_res["notifications"]:
        print("Уведомления:")
        for note in calc_res["notifications"]:
            print(f"  • [{note['rule_code']}] {note.get('params', {})}")
    print("=" * 80 + "\n")


def test_import_wheat_min_load():
    """Тест 1: Импорт пшеницы (Ялама -> Апшерон)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Апшерон")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="10019900",
        actual_weight=42,
        distance_km=effective_dist,
        wagon_type="крытый",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("1. Импорт пшеницы (Ялама -> Апшерон)", route_res, calc_res, "10019900", 42)

    assert calc_res["billable_weight"] == 60
    assert calc_res["base_rate_chf_per_ton"] > 0
    assert calc_res["final_coeff"] == round(1.015 * 0.85, 4)


def test_export_timber():
    """Тест 2: Экспорт лесоматериалов (Апшерон -> Ялама)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Апшерон", "Ялама")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="44071100",
        actual_weight=40,
        distance_km=effective_dist,
        wagon_type="платформа",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("2. Экспорт леса (Апшерон -> Ялама)", route_res, calc_res, "44071100", 40)

    assert calc_res["billable_weight"] == 45
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_transit_calculation():
    """Тест 3: Транзит угля (Ялама -> Беюк Кясик)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="27011100",
        actual_weight=60,
        distance_km=route_res.distance_km,
        wagon_type="полувагон",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("3. Транзит угля (Ялама -> Беюк Кясик)", route_res, calc_res, "27011100", 60)

    assert calc_res["billable_weight"] == 60
    assert calc_res["base_rate_chf_per_ton"] == 0.0

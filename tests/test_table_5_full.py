# tests/test_table_5_full.py

from core.router import RailwayRouter
from core.calculator import TariffCalculator
from tests.test_full_calculation import _print_calculation_result


def test_refrigerator_import_calculation():
    """Тест 1: Импорт в рефрижераторе (Ялама -> Апшерон) | Реф. вагон | 28т | СПС"""
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
        is_private_wagon=True
    )

    _print_calculation_result("1. Импорт в рефрижераторе (Ялама -> Апшерон)", route_res, calc_res, "0404", 28, "refrigerator", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_thermos_transit_calculation():
    """Тест 2: Транзит в термосе (Ялама -> Беюк Кясик) | Термос | 22т | СПС"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0709",
        actual_weight=22,
        distance_km=route_res.distance_km,
        wagon_type="thermos",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("2. Транзит в термосе (Ялама -> Беюк Кясик)", route_res, calc_res, "0709", 22, "thermos", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_car_carrier_export_calculation():
    """Тест 3: Экспорт автовозом (Апшерон -> Ялама) | Автовоз | 12т | СПС"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Апшерон", "Ялама")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8703",
        actual_weight=12,
        distance_km=effective_dist,
        wagon_type="car_carrier",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("3. Экспорт автовозом (Апшерон -> Ялама)", route_res, calc_res, "8703", 12, "car_carrier", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_inv_anv_empty_calculation():
    """Тест 4: Порожний проход ИНВ/АНВ (Ялама -> Беюк Кясик) | ИНВ/АНВ | 0т | Порожний"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8606",
        actual_weight=0,
        distance_km=route_res.distance_km,
        wagon_type="inv_anv",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("4. Порожний проход ИНВ/АНВ (Ялама -> Беюк Кясик)", route_res, calc_res, "8606", 0, "inv_anv", False)
    assert calc_res["base_rate_chf_per_ton"] > 0

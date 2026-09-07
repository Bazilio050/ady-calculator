# tests/test_full_calculation.py

from core.router import RailwayRouter
from core.calculator import TariffCalculator


def test_import_wheat_min_load():
    """
    Тест 1: Импорт пшеницы (Ялама -> Апшерон)
    Проверяет срабатывание минимальной нормы 60т для зерна и коэффициент 0.85 для приватного вагона.
    """
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Апшерон")

    effective_dist = (
        route_res.calculated_distance_km
        if route_res.calculated_distance_km > 0
        else route_res.distance_km
    )

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="10019900",  # Пшеница (норма 60т)
        actual_weight=42,      # Меньше нормы
        distance_km=effective_dist,
        wagon_type="крытый",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True  # Коэффициент 0.85
    )

    assert calc_res["billable_weight"] == 60
    assert calc_res["base_rate_chf_per_ton"] > 0
    assert calc_res["final_coeff"] == round(1.015 * 0.85, 5)


def test_export_timber():
    """
    Тест 2: Экспорт лесоматериалов (Апшерон -> Ялама)
    Проверяет норму 45т для древесины.
    """
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Апшерон", "Ялама")

    effective_dist = (
        route_res.calculated_distance_km
        if route_res.calculated_distance_km > 0
        else route_res.distance_km
    )

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="44071100",  # Лесоматериалы (норма 45т)
        actual_weight=40,
        distance_km=effective_dist,
        wagon_type="платформа",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    assert calc_res["billable_weight"] == 45
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_transit_calculation():
    """
    Тест 3: Транзит (Ялама -> Беюк Кясик)
    """
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="27011100",  # Уголь
        actual_weight=60,
        distance_km=route_res.distance_km,
        wagon_type="полувагон",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    assert calc_res["billable_weight"] == 60
    assert calc_res["base_rate_chf_per_ton"] == 0.0  # Для транзита Таблица 3 не применяется

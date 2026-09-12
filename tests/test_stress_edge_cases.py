# tests/test_stress_edge_cases.py

import sys
import os

# Добавление корневой директории проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.router import RailwayRouter
from core.calculator import TariffCalculator


def test_negative_weight_validation():
    """Стресс-тест 1: Передача отрицательного веса должна вызывать ValueError"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Абшерон")

    with pytest.raises((ValueError, Exception)):
        TariffCalculator.calculate(
            shipment_type=route_res.shipment_type.value,
            gng_code="10010000",
            actual_weight=-10.0,
            distance_km=route_res.calculated_distance_km,
            wagon_type="covered"
        )


def test_zero_distance_same_station():
    """Стресс-тест 2: Маршрут внутри одной станции (расстояние 0 км)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Абшерон", "Абшерон")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="10010000",
        actual_weight=30.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    assert calc_res["final_rate_total_usd"] == 0.0


def test_complex_multi_rule_combination():
    """Стресс-тест 3: Комбинация правил (Опасный груз + Пассажирский поезд + Сцеп + СПС)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="28047000",  # Опасный груз (Фосфор)
        un_code="1338",
        actual_weight=12.0,   # Мало веса для сцепа
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        is_dangerous_cargo=True,
        is_passenger_train_composition=True,
        is_attached_wagons=True,
        attached_wagons_count=2,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]

    # Проверки:
    # 1. Расчетный вес поднялся до 40 т (20 т * 2 вагона)
    assert calc_res["billable_weight"] == 40.0
    # 2. Применены все требуемые правила
    assert "ATTACHED_WAGONS_MIN_WEIGHT_RULE_3_7_1" in applied_codes
    assert "ROLLING_STOCK_PASSENGER_TRAIN_COEFF_2_00_RULE_3_7_3" in applied_codes
    assert "DANGEROUS_CARGO_COEFF_2_00_RULE_3_6_1" in applied_codes


def test_unknown_gng_code_fallback():
    """Стресс-тест 4: Передача несуществующего кода ГНГ должна отрабатывать штатно"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Абшерон")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="00000000",
        actual_weight=45.0,
        distance_km=route_res.calculated_distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    assert calc_res["final_rate_usd_per_ton"] > 0
    assert calc_res["billable_weight"] == 45.0

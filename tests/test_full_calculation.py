# tests/test_full_calculation.py

from core.router import RailwayRouter
from core.calculator import TariffCalculator


def _print_calculation_result(test_name: str, route_res, calc_res, gng_code: str, actual_w: float, wagon_type: str, is_private: bool):
    """Вспомогательная функция для наглядного вывода результатов расчета."""
    wagon_ownership = "СПС (приватный)" if is_private else "МПС (инвентарный)"
    
    print("\n" + "=" * 80)
    print(f"   {test_name.upper()}")
    print("=" * 80)
    print(f"Маршрут:       {route_res.formatted_output('RU')}")
    print(f"ГНГ код:       {gng_code}")
    print(f"Тип вагона:    {wagon_type} [{wagon_ownership}]")
    print(f"Вес (факт):    {actual_w} т -> Расчетный (Табл.1/Норма): {calc_res['billable_weight']} т")
    print(f"Базовая ставка: {calc_res['base_rate_chf_per_ton']} CHF/т (Таблица 3)")
    print(f"Итоговый коэф: {calc_res['final_coeff']}")
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

    _print_calculation_result("1. Импорт пшеницы (Ялама -> Апшерон)", route_res, calc_res, "10019900", 42, "крытый", True)
    assert calc_res["billable_weight"] == 60


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

    _print_calculation_result("2. Экспорт леса (Апшерон -> Ялама)", route_res, calc_res, "44071100", 40, "платформа", False)
    assert calc_res["billable_weight"] == 45


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

    _print_calculation_result("3. Транзит угля (Ялама -> Беюк Кясик)", route_res, calc_res, "27011100", 60, "полувагон", False)
    assert calc_res["base_rate_chf_per_ton"] == 0.0


def test_import_timber_sps():
    """Тест 4: Ялама -> Апшерон | ГНГ 4407 | платформа | 35т | СПС (приватный)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Апшерон")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="4407",
        actual_weight=35,
        distance_km=effective_dist,
        wagon_type="платформа",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("4. Импорт леса СПС (Ялама -> Апшерон)", route_res, calc_res, "4407", 35, "платформа", True)
    assert calc_res["billable_weight"] == 45


def test_paper_bilajari_boyuk_kesik():
    """Тест 5: Баладжары -> Беюк Кясик | ГНГ 4818 | хоппер | 26т | МПС (инвентарный)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Баладжары", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="4818",
        actual_weight=26,
        distance_km=route_res.distance_km,
        wagon_type="хоппер",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("5. Изделия из бумаги МПС (Баладжары -> Беюк Кясик)", route_res, calc_res, "4818", 26, "хоппер", False)
    assert calc_res["actual_weight"] == 26

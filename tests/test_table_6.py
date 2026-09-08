# tests/test_table_6.py

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
    print(f"Вес (факт): {weight} т -> Расчетный (Табл.6/Правило 2): {calc_res['billable_weight']} т")
    
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
# ТЕСТЫ ДЛЯ ТАБЛИЦЫ 6 (НАЛИВНЫЕ ГРУЗЫ В ЦИСТЕРНАХ)
# ------------------------------------------------------------------------------

def test_table_6_col_2_oil_transit_kuryk():
    """Тест 1: Наливные грузы — Колонка 2 (Нефть и нефтепродукты | Ялама -> Курык)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Курык")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="27101921",
        actual_weight=60.0,
        distance_km=route_res.distance_km,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("1. Наливные грузы — Колонка 2 (Ялама -> Курык)", route_res, calc_res, "27101921", 60.0, "cistern", False)
    assert calc_res["billable_weight"] == 25.0
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_table_6_col_3_energy_gases_export_trk():
    """Тест 2: Наливные грузы — Колонка 3 (Энергетические газы | Апшерон -> ТРК)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Апшерон", "ТРК")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="27111211",
        actual_weight=45.0,
        distance_km=route_res.distance_km,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("2. Наливные грузы — Колонка 3 (Апшерон -> Алят-эксп. / ТРК)", route_res, calc_res, "27111211", 45.0, "cistern", False)
    assert calc_res["billable_weight"] == 25.0
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_table_6_col_4_gases_hydrocarbons_import_alat():
    """Тест 3: Наливные грузы — Колонка 4 (Газы и химические углеводороды | Алят-эксп. -> Гаджигабул)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Алят-эксп", "Гаджигабул")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="28141000",
        actual_weight=50.0,
        distance_km=route_res.distance_km,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("3. Наливные грузы — Колонка 4 (Алят-эксп. -> Гаджигабул)", route_res, calc_res, "28141000", 50.0, "cistern", False)
    assert calc_res["billable_weight"] == 25.0
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_table_6_col_5_alcohols_phenols_transit_alat():
    """Тест 4: Наливные грузы — Колонка 5 (Спирты и фенолы | Ялама -> Алят-эксп.)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Алят-эксп")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="29051100",
        actual_weight=55.0,
        distance_km=route_res.distance_km,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("4. Наливные грузы — Колонка 5 (Ялама -> Алят-эксп.)", route_res, calc_res, "29051100", 55.0, "cistern", False)
    assert calc_res["billable_weight"] == 25.0
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_table_6_col_6_perishable_liquids_export_alat():
    """Тест 5: Наливные грузы — Колонка 6 (Скоропортящиеся наливные | Гянджа -> Курык)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Гянджа", "Курык")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="04011000",
        actual_weight=40.0,
        distance_km=route_res.distance_km,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("5. Наливные грузы — Колонка 6 (Гянджа -> Алят-эксп.)", route_res, calc_res, "04011000", 40.0, "cistern", False)
    assert calc_res["billable_weight"] == 25.0
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_table_6_col_7_other_liquids_import_alat():
    """Тест 6: Наливные грузы — Колонка 7 (Прочие наливные грузы | Алят-эксп. -> Сумгаит)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Алят-эксп.", "Сумгаит")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="99999999",
        actual_weight=50.0,
        distance_km=route_res.distance_km,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("6. Наливные грузы — Колонка 7 (Алят-эксп. -> Сумгаит)", route_res, calc_res, "99999999", 50.0, "cistern", False)
    assert calc_res["billable_weight"] == 25.0
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_table_6_col_8_private_tank_transit_alat():
    """Тест 7: Наливные грузы — Колонка 8 (Приватные цистерны | Беюк Кясик -> Алят-эксп.)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("БК", "Алят-эксп.")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="27071000",
        actual_weight=50.0,
        distance_km=route_res.distance_km,
        wagon_type="cistern",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("7. Наливные грузы — Колонка 8 (Приватные цистерны — без двойной скидки 0.85)", route_res, calc_res, "27071000", 50.0, "cistern", True)
    assert calc_res["billable_weight"] == 25.0

    applied_codes = [n.get("rule_code") for n in calc_res.get("notifications", []) if isinstance(n, dict)]
    assert "MAIN_COEFF_0_85_PRIVATE_WAGON" not in applied_codes

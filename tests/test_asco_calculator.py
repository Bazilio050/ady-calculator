# tests/test_asco_calculator.py

import pytest
from core.asco_calculator import AscoFerryCalculator, determine_asco_cargo_category


def test_determine_asco_cargo_category():
    # Нефть и нефтяные цистерны / крытые
    assert determine_asco_cargo_category("27090010", "cistern") == "oil_cistern"
    assert determine_asco_cargo_category("271019", "covered") == "oil_covered"

    # Алкогольная продукция (вся 22 группа, кроме 2201 и 2202)
    assert determine_asco_cargo_category("220421", "cistern") == "alcohol"
    assert determine_asco_cargo_category("220830", "covered") == "alcohol"
    assert determine_asco_cargo_category("220110", "covered") == "base"

    # Сжиженный газ (LPG)
    assert determine_asco_cargo_category("271112", "cistern") == "lpg"

    # Экспорт из Азербайджана
    assert determine_asco_cargo_category("100190", "covered", shipment_type="export") == "export_az"


def test_asco_calculator_routes():
    print("\n==================================================")
    print("ПРОВЕРКА МОРСКОГО ФРАХТА ASCO (КАСПИЙСКОЕ МОРЕ)")
    print("==================================================")

    # 1. Обычный груз до Туркменбаши
    res1 = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Turkmenbashi",
        gng_code="100190",
        wagon_type="covered",
        wagon_length_m=14.0
    )
    print(f"\nМаршрут: Alyat -> Turkmenbashi (Крытый 14м)")
    print(f"  - Порт: {res1['port']}")
    print(f"  - Категория: {res1['cargo_category']}")
    print(f"  - Формула: {res1['length_meters']}м х ${res1['rate_per_meter']}/м х коэф. {res1['coeff']} = ${res1['total_asco_usd']} USD")
    print("--------------------------------------------------")

    assert res1["status"] == "SUCCESS"
    assert res1["port"] == "turkmenbashi"
    assert res1["total_asco_usd"] == 630.0

    # 2. Нефтяная цистерна до Курык (фикс. длина 13 м)
    res2 = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Kuryk",
        gng_code="27090090",
        wagon_type="cistern",
        wagon_length_m=18.0
    )
    print(f"\nМаршрут: Alyat -> Kuryk (Нефть)")
    print(f"  - Порт: {res2['port']}")
    print(f"  - Категория: {res2['cargo_category']}")
    print(f"  - Формула: {res2['length_meters']}м (фикс) х ${res2['rate_per_meter']}/м х коэф. {res2['coeff']} = ${res2['total_asco_usd']} USD")
    print("--------------------------------------------------")

    assert res2["status"] == "SUCCESS"
    assert res2["length_meters"] == 13.0
    assert res2["total_asco_usd"] == 1079.0


def test_asco_calculator_dangerous_goods():
    # Опасный груз класс 8
    res = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Turkmenbashi",
        gng_code="280610",
        wagon_type="covered",
        wagon_length_m=14.0,
        is_dangerous=True,
        dangerous_class=8
    )
    print(f"\nМаршрут: Alyat -> Turkmenbashi (Опасный груз класс 8)")
    print(f"  - Категория: {res['cargo_category']}")
    print(f"  - Формула: {res['length_meters']}м х ${res['rate_per_meter']}/м х коэф. {res['coeff']} = ${res['total_asco_usd']} USD")
    print("--------------------------------------------------")

    assert res["status"] == "SUCCESS"
    assert res["cargo_category"] == "dangerous"
    assert res["total_asco_usd"] == 700.0


def test_asco_calculator_oversized():
    # Негабарит
    res = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Kuryk",
        gng_code="840110",
        wagon_type="platform",
        wagon_length_m=16.0,
        wagon_width_m=4.1
    )
    print(f"\nМаршрут: Alyat -> Kuryk (Негабарит по ширине и длине)")
    print(f"  - Категория: {res['cargo_category']}")
    print(f"  - Формула: {res['length_meters']}м х ${res['rate_per_meter']}/м х коэф. {res['coeff']} = ${res['total_asco_usd']} USD")
    print("==================================================")

    assert res["status"] == "SUCCESS"
    assert res["coeff"] == 2.6
    assert res["total_asco_usd"] == 2080.0

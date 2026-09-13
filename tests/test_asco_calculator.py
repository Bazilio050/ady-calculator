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
    assert determine_asco_cargo_category("220110", "covered") == "base"  # Вода -> base

    # Сжиженный газ (LPG)
    assert determine_asco_cargo_category("271112", "cistern") == "lpg"

    # Экспорт из Азербайджана
    assert determine_asco_cargo_category("100190", "covered", shipment_type="export") == "export_az"


def test_asco_calculator_routes():
    # Обычный груз до Туркменбаши (длина 14 м)
    res = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Turkmenbashi",
        gng_code="100190",
        wagon_type="covered",
        wagon_length_m=14.0
    )
    assert res["status"] == "SUCCESS"
    assert res["port"] == "turkmenbashi"
    assert res["total_asco_usd"] == 630.0  # 14m * $45/m

    # Маршрут без каспийских портов
    res_na = AscoFerryCalculator.calculate(
        route_from="Baku",
        route_to="Tbilisi",
        gng_code="100190",
        wagon_type="covered"
    )
    assert res_na["status"] == "NOT_APPLICABLE"
    assert res_na["total_asco_usd"] == 0.0


def test_asco_calculator_fixed_length_oil():
    # Нефтяная цистерна до Курык (фиксированная длина 13 м)
    res = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Kuryk",
        gng_code="27090090",
        wagon_type="cistern",
        wagon_length_m=18.0  # Должна проигнорироваться в пользу 13 м
    )
    assert res["status"] == "SUCCESS"
    assert res["length_meters"] == 13.0
    assert res["total_asco_usd"] == 1079.0  # 13m * $83/m


def test_asco_calculator_dangerous_goods():
    # Класс 3 (требует согласования)
    res_agreed = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Turkmenbashi",
        gng_code="290220",
        wagon_type="covered",
        is_dangerous=True,
        dangerous_class=3
    )
    assert res_agreed["status"] == "REQUIRES_AGREEMENT"
    assert res_agreed["total_asco_usd"] == 0.0

    # Класс 8 (надбавка за опасный груз)
    res_danger = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Turkmenbashi",
        gng_code="280610",
        wagon_type="covered",
        wagon_length_m=14.0,
        is_dangerous=True,
        dangerous_class=8
    )
    assert res_danger["status"] == "SUCCESS"
    assert res_danger["cargo_category"] == "dangerous"
    assert res_danger["total_asco_usd"] == 700.0  # 14m * $50/m


def test_asco_calculator_oversized():
    # Длина > 15 м (+30%) и ширина >= 4 м (x2.0)
    res = AscoFerryCalculator.calculate(
        route_from="Alyat",
        route_to="Kuryk",
        gng_code="840110",
        wagon_type="platform",
        wagon_length_m=16.0,
        wagon_width_m=4.1
    )
    # Коэффициент: 1.3 * 2.0 = 2.6
    # Итого: 16m * $50/m * 2.6 = 2080.0
    assert res["status"] == "SUCCESS"
    assert res["coeff"] == 2.6
    assert res["total_asco_usd"] == 2080.0

# tests/test_security_calculator.py

import pytest
from core.security_calculator import SecurityCalculator


def test_security_required_gng_codes():
    # ГНГ из списка (мясо, зерно, кофе) -> Охрана требуется
    assert SecurityCalculator.is_security_required("2011000") is True
    assert SecurityCalculator.is_security_required("10010000") is True
    assert SecurityCalculator.is_security_required("9010000") is True

    # ГНГ не из списка (песок, камень) -> Охрана не требуется
    assert SecurityCalculator.is_security_required("25051000") is False


def test_security_calculator_transit():
    print("\n==================================================")
    print("ПРОВЕРКА ОБЯЗАТЕЛЬНОЙ ОХРАНЫ ВОХР (ТРАНЗИТ)")
    print("==================================================")

    distance = 500.0
    gng_wheat = "10010000"

    # 1. Транзитный маршрут (Пшеница, 500 км)
    # Формула: 500 * 0.1 / 0.7 = 71.43 USD
    res_transit = SecurityCalculator.calculate(
        shipment_type="transit",
        gng_code=gng_wheat,
        distance_km=distance
    )
    print(f"\nСценарий 1: Транзит (Пшеница, {distance} км)")
    print(f"  - Статус охраны: {res_transit['is_required']}")
    print(f"  - Расчет: {distance} км * 0.1 / 0.7 = ${res_transit['security_fee_usd']} USD")
    print("--------------------------------------------------")

    assert res_transit["is_required"] is True
    assert res_transit["security_fee_usd"] == 71.43

    # 2. Импортный маршрут (Охрана не начисляется)
    res_import = SecurityCalculator.calculate(
        shipment_type="import",
        gng_code=gng_wheat,
        distance_km=distance
    )
    print(f"\nСценарий 2: Импорт (Пшеница, {distance} км)")
    print(f"  - Статус охраны: {res_import['is_required']}")
    print(f"  - Плата за охрану: ${res_import['security_fee_usd']} USD")
    print("==================================================")

    assert res_import["is_required"] is False
    assert res_import["security_fee_usd"] == 0.0

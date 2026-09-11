# tests/test_table_13_dangerous.py

import sys
import os

# Добавление корневой директории проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.router import RailwayRouter
from core.calculator import TariffCalculator
from core.tables.table_13 import Table13Checker
from data.translations import RULE_MESSAGES


def test_table_13_checker_logic():
    """Тест 1: Прямая проверка модуля Table13Checker"""
    # 1230 - METANOL (только цистерны 'cen')
    assert Table13Checker.check_dangerous_status("1230", "cistern") is True
    assert Table13Checker.check_dangerous_status("1230", "covered") is False

    # 2927 - Akvanit (крытые вагоны/контейнеры 'ortulu_konteyner')
    assert Table13Checker.check_dangerous_status("2927", "covered") is True
    assert Table13Checker.check_dangerous_status("2927", "cistern") is False

    # 3286 - Heptil (все типы 'hamisi')
    assert Table13Checker.check_dangerous_status("3286", "covered") is True
    assert Table13Checker.check_dangerous_status("3286", "cistern") is True


def test_auto_dangerous_cargo_by_un_code_in_calculator():
    """Тест 2: Авто-определение опасного груза в TariffCalculator по un_code"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    # Передаем un_code="2927" (Akvanit) БЕЗ явного флага is_dangerous_cargo=True
    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="2801",
        actual_weight=20.0,
        distance_km=route_res.distance_km,
        wagon_type="covered",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        un_code="2927"  # Автоматически включает Таблицу 12
    )

    rule_codes = [n["rule_code"] for n in calc_res["notifications"]]
    assert calc_res["applied_table"] == "Таблица 12"
    assert "DANGEROUS_CARGO_COEFF_2_00_RULE_3_6_1" in rule_codes

# tests/test_table_6.py

import pytest
from core.calculator import TariffCalculator


def _print_formatted_result(test_name: str, res: dict):
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Выводит структурированный и красивый отчет по результатам расчета Таблицы 6.
    """
    print(f"\n======================================================================")
    print(f"{test_name}")
    print(f"======================================================================")
    print(f"Таблица расчета: {res.get('applied_table')}")
    print(f"Расстояние: {res.get('distance_km')} км")
    print(f"Вес (факт): {res.get('actual_weight')} т -> Расчетный: {res.get('billable_weight')} т")
    print(f"Базовая ставка в CHF: {res.get('base_rate_chf_per_ton')} CHF/т")
    print(f"Курс конвертации (CHF -> USD): {res.get('exchange_rate_chf_to_usd')}")
    print(f"Базовая ставка в USD: {res.get('base_rate_usd_per_ton')} USD/т")
    print(f"Итоговая ставка в USD: {res.get('final_rate_usd_per_ton')} USD/т")
    
    if res.get('notifications'):
        print("\nУведомления и примененные правила:")
        for notif in res['notifications']:
            code = notif.get('rule_code', '')
            params = notif.get('params', {})
            print(f"- [Правило {code}]: {params}")


def test_table_6_col_2_oil_transit_alat():
    """Колонка 2: Нефть (ГНГ 2710) | Транзит | Ələt-eksp. | Ставка: 20.49"""
    res = TariffCalculator.calculate(
        shipment_type="Transit",
        gng_code="27101921",
        actual_weight=60.0,
        distance_km=300.0,
        wagon_type="cistern",
        from_canonical_name="Yalama",
        to_canonical_name="Ələt-eksp.",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("1. Наливные грузы — Колонка 2 (Нефть и нефтепродукты)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 20.49


def test_table_6_col_3_energy_gases_export_alat():
    """Колонка 3: Энергетические газы (ГНГ 2711) | Экспорт | Ələt-eksp. | Ставка: 24.44"""
    res = TariffCalculator.calculate(
        shipment_type="Export",
        gng_code="27111211",
        actual_weight=45.0,
        distance_km=300.0,
        wagon_type="cistern",
        from_canonical_name="Abşeron",
        to_canonical_name="Ələt-eksp.",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("2. Наливные грузы — Колонка 3 (Энергетические газы)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 24.44


def test_table_6_col_4_gases_hydrocarbons_import_alat():
    """Колонка 4: Газы и углеводороды (ГНГ 2814) | Импорт | Ələt-eksp. | Ставка: 34.92"""
    res = TariffCalculator.calculate(
        shipment_type="Import",
        gng_code="28141000",
        actual_weight=50.0,
        distance_km=300.0,
        wagon_type="cistern",
        from_canonical_name="Ələt-eksp.",
        to_canonical_name="Hacıqabul",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("3. Наливные грузы — Колонка 4 (Газы и химические углеводороды)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 34.92


def test_table_6_col_5_alcohols_phenols_transit_alat():
    """Колонка 5: Спирты и фенолы (ГНГ 2905) | Транзит | Ələt-eksp. | Ставка: 26.19"""
    res = TariffCalculator.calculate(
        shipment_type="Transit",
        gng_code="29051100",
        actual_weight=55.0,
        distance_km=300.0,
        wagon_type="cistern",
        from_canonical_name="Yalama",
        to_canonical_name="Ələt-eksp.",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("4. Наливные грузы — Колонка 5 (Спирты и фенолы)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 26.19


def test_table_6_col_6_perishable_liquids_export_alat():
    """Колонка 6: Скоропортящиеся наливные (ГНГ 0401) | Экспорт | Ələt-eksp. | Ставка: 24.44"""
    res = TariffCalculator.calculate(
        shipment_type="Export",
        gng_code="04011000",
        actual_weight=40.0,
        distance_km=300.0,
        wagon_type="cistern",
        from_canonical_name="Gəncə",
        to_canonical_name="Ələt-eksp.",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("5. Наливные грузы — Колонка 6 (Скоропортящиеся наливные грузы)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 24.44


def test_table_6_col_7_other_liquids_import_alat():
    """Колонка 7: Прочие наливные (ГНГ 9999) | Импорт | Ələt-eksp. | Ставка: 20.95"""
    res = TariffCalculator.calculate(
        shipment_type="Import",
        gng_code="99999999",
        actual_weight=50.0,
        distance_km=300.0,
        wagon_type="cistern",
        from_canonical_name="Ələt-eksp.",
        to_canonical_name="Sumqayıt",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("6. Наливные грузы — Колонка 7 (Прочие наливные грузы)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 20.95


def test_table_6_col_8_private_tank_transit_alat():
    """Колонка 8: Приватная цистерна (ГНГ 270710) | Транзит | Ələt-eksp. | Ставка: 24.44"""
    res = TariffCalculator.calculate(
        shipment_type="Transit",
        gng_code="27071000",
        actual_weight=50.0,
        distance_km=300.0,
        wagon_type="cistern",
        from_canonical_name="Yalama",
        to_canonical_name="Ələt-eksp.",
        is_private_wagon=True,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("7. Наливные грузы — Колонка 8 (Приватные цистерны — без двойной скидки 0.85)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 24.44

    # Проверка отсутствия дублирования скидки 0.85
    applied_codes = [n["rule_code"] for n in res["notifications"]]
    assert "MAIN_COEFF_0_85_PRIVATE_WAGON" not in applied_codes

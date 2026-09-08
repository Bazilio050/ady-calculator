# tests/test_table_6.py

import pytest
from core.calculator import TariffCalculator


def _print_formatted_result(test_title: str, res: dict):
    """
    Выводит детальный структурированный отчет в стиле Таблицы 5.
    """
    from_name = res.get('from_canonical_name') or res.get('from_station_name') or ''
    from_code = res.get('from_station_code') or ''
    to_name = res.get('to_canonical_name') or res.get('to_station_name') or ''
    to_code = res.get('to_station_code') or ''

    from_str = f"{from_name} ({from_code})" if from_code else from_name
    to_str = f"{to_name} ({to_code})" if to_code else to_name

    route_str = f"{from_str} - {to_str} [{res.get('shipment_type', '').lower()}] - {res.get('distance_km')} км"

    wagon_ownership = "приватный" if res.get("is_private_wagon") else "инвентарный"
    wagon_info = f"{res.get('wagon_type', 'cistern')} [{wagon_ownership}]"

    print(f"\n======================================================================")
    print(f"{test_title}")
    print(f"======================================================================")
    print(f"Маршрут: {route_str}")
    print(f"ГНГ код: {res.get('gng_code')}")
    print(f"Тип вагона: {wagon_info}")
    print(f"Вес (факт): {res.get('actual_weight')} т -> Расчетный (Табл.6/Правило 2): {res.get('billable_weight')} т")
    print(f"Базовая ставка: {res.get('base_rate_chf_per_ton')} CHF/т ({res.get('applied_table')})")
    print(f"Курс конвертации (CHF -> USD): {res.get('exchange_rate_chf_to_usd')}")
    print(f"Базовая ставка в USD: {res.get('base_rate_usd_per_ton')} USD/т\n")

    applied_rules = res.get("applied_rules", [])
    if applied_rules:
        for rule in applied_rules:
            desc = rule.get("description_ru") or rule.get("rule_code")
            print(f"{desc}")
        print()

    print(f"Итог за 1 т: {res.get('final_rate_usd_per_ton')} USD/т\n")

    notifications = res.get("notifications", [])
    if notifications:
        print("Уведомления:")
        for notif in notifications:
            if isinstance(notif, dict) and "text_az" in notif and "text_en" in notif:
                print(f"AZ: {notif['text_az']}")
                print(f"EN: {notif['text_en']}")
            elif isinstance(notif, dict) and "message" in notif:
                print(f"- {notif['message']}")


def test_table_6_col_2_oil_transit_kuryk():
    """Колонка 2: Нефть (ГНГ 2710) | Транзит | Yalama -> Kuryk"""
    res = TariffCalculator.calculate(
        shipment_type="Transit",
        gng_code="27101921",
        actual_weight=60.0,
        distance_km=429.0,
        wagon_type="cistern",
        from_canonical_name="Yalama",
        to_canonical_name="Kuryk",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("1. Наливные грузы — Колонка 2 (Нефть и нефтепродукты)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0


def test_table_6_col_3_energy_gases_export_trk():
    """Колонка 3: Энергетические газы (ГНГ 2711) | Экспорт | Abşeron -> ТРК. (Направление ТРК)"""
    res = TariffCalculator.calculate(
        shipment_type="Export",
        gng_code="27111211",
        actual_weight=45.0,
        distance_km=350.0,
        wagon_type="cistern",
        from_canonical_name="Abşeron",
        to_canonical_name="ТРК",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    _print_formatted_result("2. Наливные грузы — Колонка 3 (Энергетические газы — ТРК)", res)

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0


def test_table_6_col_4_gases_hydrocarbons_import_alat():
    """Колонка 4: Газы и углеводороды (ГНГ 2814) | Импорт | Ələt-eksp. -> Hacıqabul"""
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


def test_table_6_col_5_alcohols_phenols_transit_alat():
    """Колонка 5: Спирты и фенолы (ГНГ 2905) | Транзит | Yalama -> Ələt-eksp."""
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


def test_table_6_col_6_perishable_liquids_export_alat():
    """Колонка 6: Скоропортящиеся наливные (ГНГ 0401) | Экспорт | Gəncə -> Ələt-eksp."""
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


def test_table_6_col_7_other_liquids_import_alat():
    """Колонка 7: Прочие наливные (ГНГ 9999) | Импорт | Ələt-eksp. -> Sumqayıt"""
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


def test_table_6_col_8_private_tank_transit_alat():
    """Колонка 8: Приватная цистерна (ГНГ 270710) | Транзит | Yalama -> Ələt-eksp."""
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

    applied_codes = [n.get("rule_code") for n in res.get("notifications", []) if isinstance(n, dict)]
    assert "MAIN_COEFF_0_85_PRIVATE_WAGON" not in applied_codes


# tests/test_table_6.py

import pytest
from core.calculator import TariffCalculator


def test_table_6_col_2_oil_transit_alat():
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Колонка 2: Нефть и нефтепродукты (ГНГ 2710) | Транзит | Станция Ələt-eksp.
    Вес фиксируется на 25 тоннах по Правилу 2.
    """
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

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 24.44


def test_table_6_col_3_energy_gases_export_alat():
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Колонка 3: Энергетические газы (ГНГ 2711) | Экспорт | Станция Ələt-eksp.
    """
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

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 24.44


def test_table_6_col_4_gases_hydrocarbons_import_alat():
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Колонка 4: Газы и углеводороды (ГНГ 2814) | Импорт | Станция Ələt-eksp.
    """
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

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 34.92


def test_table_6_col_5_alcohols_phenols_transit_alat():
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Колонка 5: Спирты и фенолы (ГНГ 2905) | Транзит | Станция Ələt-eksp.
    """
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

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 26.19


def test_table_6_col_6_perishable_liquids_export_alat():
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Колонка 6: Скоропортящиеся наливные грузы (ГНГ 1507 — масла) | Экспорт | Станция Ələt-eksp.
    """
    res = TariffCalculator.calculate(
        shipment_type="Export",
        gng_code="15071000",
        actual_weight=40.0,
        distance_km=300.0,
        wagon_type="cistern",
        from_canonical_name="Gəncə",
        to_canonical_name="Ələt-eksp.",
        is_private_wagon=False,
        shipment_date="2026-08-01"
    )

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 24.44


def test_table_6_col_7_other_liquids_import_alat():
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Колонка 7: Прочие наливные грузы (ГНГ 9999) | Импорт | Станция Ələt-eksp.
    """
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

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 20.95


def test_table_6_col_8_private_tank_transit_alat():
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Колонка 8: Приватная цистерна (Özəl çənlər) с углеводородами (ГНГ 270710) | Транзит | Станция Ələt-eksp.
    Проверяем, что ставка берется из колонки 8 и скидка 0.85 НЕ применятся повторно.
    """
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

    assert res["applied_table"] == "Таблица 6"
    assert res["billable_weight"] == 25.0
    assert res["base_rate_chf_per_ton"] == 24.44

    # Проверяем отсутствие двойной скидки 0.85
    applied_codes = [n["rule_code"] for n in res["notifications"]]
    assert "MAIN_COEFF_0_85_PRIVATE_WAGON" not in applied_codes

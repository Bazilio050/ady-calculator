# tests/test_diesel_generator.py

from core.calculator import TariffCalculator


def test_diesel_generator_wagon_calculation():
    """Проверка расчета провозной платы за вагон-дизель-генератор (п. 3.4.3.2)"""
    distance = 500.0  # км
    axles = 4        # осей
    expected_chf = round(500.0 * 4 * 0.12, 2)  # 240.0 CHF

    res = TariffCalculator.calculate(
        shipment_type="transit",
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=distance,
        wagon_type="diesel_generator_wagon",
        from_canonical_name="Ялама",
        to_canonical_name="БК",
        axle_count=axles,
        is_private_wagon=True
    )

    print(f"\nБазовая ставка: {res['base_rate_chf_per_ton']} CHF (Ожидается: {expected_chf} CHF)")
    assert res['base_rate_chf_per_ton'] == expected_chf
    assert res['table_name'] == "Пункт 3.4.3.2"

# tests/test_diesel_generator.py

from core.calculator import TariffCalculator


def test_attendants_fee_calculation():
    """Проверка расчета платы за проводников (п. 3.4.3.2): 12 CHF / 100 км / чел"""
    distance = 250.0  # 250 км = 3 начатых интервала по 100 км
    attendants = 2    # 2 проводника
    # Расчет: 3 (интервала) * 12 CHF * 2 (человека) = 72 CHF
    
    res = TariffCalculator.calculate(
        shipment_type="transit",
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=distance,
        wagon_type="diesel_generator_wagon",
        from_canonical_name="Ялама",
        to_canonical_name="БК",
        attendants_count=attendants,
        is_private_wagon=True
    )

    applied_codes = [r["rule_code"] for r in res.get("notifications", [])]
    assert "ATTENDANTS_FEE_RULE_3_4_3_2" in applied_codes


def test_service_crew_free():
    """Проверка бесплатного проезда сервисной бригады (п. 3.4.3.2)"""
    res = TariffCalculator.calculate(
        shipment_type="transit",
        gng_code="99210000",
        actual_weight=0.0,
        distance_km=250.0,
        wagon_type="diesel_generator_wagon",
        from_canonical_name="Ялама",
        to_canonical_name="БК",
        is_service_crew=True,
        is_private_wagon=True
    )

    applied_codes = [r["rule_code"] for r in res.get("notifications", [])]
    assert "SERVICE_CREW_FREE_RULE_3_4_3_2" in applied_codes

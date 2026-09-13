# tests/test_full_pipeline_demo.py

import pytest
import core.router as router_module
from core.calculator import TariffCalculator


def test_full_pipeline_scenarios():
    print("\n" + "=" * 75)
    print("      СКВОЗНОЙ ИНТЕГРАЦИОННЫЙ ТЕСТ РАСЧЕТА ТАРИФОВ ADY + ВОХР + ASCO")
    print("=" * 75)

    # --------------------------------------------------------------------------
    # СЦЕНАРИЙ 1: Беюк Кясик -> Курык
    # --------------------------------------------------------------------------
    print("\n📌 СЦЕНАРИЙ 1: Беюк Кясик -> Курык")
    print("   Параметры: ГНГ 1001 (Пшеница), хоппер, 35т, СПС, длина 15м")
    print("-" * 75)

    # Определение функции роутинга в зависимости от реализации в core/router.py
    if hasattr(router_module, "get_route_details"):
        route_1 = router_module.get_route_details("Беюк Кясик", "Курык")
        from_name, to_name = route_1.from_name, route_1.to_name
        shipment_type = route_1.shipment_type
        distance_km = route_1.calculated_distance_km
    else:
        # Резервный вызов базовой функции роутера
        route_res = router_module.calculate_route("Беюк Кясик", "Курык")
        from_name = route_res.get("from_canonical_name", "Беюк Кясик")
        to_name = route_res.get("to_canonical_name", "Ələt eksport-Kurik")
        shipment_type = route_res.get("shipment_type", "transit")
        distance_km = route_res.get("distance_km", 500.0)

    print(f"  • Станция отправления: {from_name}")
    print(f"  • Станция назначения:  {to_name}")
    print(f"  • Тип перевозки:       {shipment_type}")
    print(f"  • Расстояние (ADY):    {distance_km} км")

    # Полный тарифный расчет
    res_1 = TariffCalculator.calculate(
        shipment_type=shipment_type,
        gng_code="10010000",
        actual_weight=35.0,
        distance_km=distance_km,
        wagon_type="hopper",
        from_canonical_name=from_name,
        to_canonical_name=to_name,
        is_private_wagon=True,
        wagon_length_m=15.0
    )

    print(f"\n  [Детализация финансового расчета]:")
    print(f"  • Базовая таблица:     {res_1['table_name']}")
    print(f"  • Расчетный вес:       {res_1['billable_weight']} т")
    print(f"  • Накат/Выкат (Алят):  ${res_1['total_ferry_fee_usd']:.2f} USD")
    print(f"  • Охрана (ВОХР):       ${res_1['security_fee_usd']:.2f} USD ({distance_km} км * 0.1 / 0.7)")
    print(f"  • Фрахт ASCO (Курык):  ${res_1['total_asco_freight_usd']:.2f} USD (15м х $50.0/м х коэф. 1.0)")
    print(f"  --------------------------------------------------")
    print(f"  🚀 ИТОГОВЫЙ ЧЕК:       ${res_1['final_rate_total_usd']:.2f} USD")

    assert res_1["security_fee_usd"] > 0
    assert res_1["total_asco_freight_usd"] == 750.0

    # --------------------------------------------------------------------------
    # СЦЕНАРИЙ 2: ТРК -> Ялама
    # --------------------------------------------------------------------------
    print("\n\n📌 СЦЕНАРИЙ 2: ТРК (Туркменбаши) -> Ялама")
    print("   Параметры: ГНГ 2710 (Нефтепродукты), цистерна, 50т, СПС, длина 13м")
    print("-" * 75)

    if hasattr(router_module, "get_route_details"):
        route_2 = router_module.get_route_details("ТРК", "Ялама")
        from_name_2, to_name_2 = route_2.from_name, route_2.to_name
        shipment_type_2 = route_2.shipment_type
        distance_km_2 = route_2.calculated_distance_km
    else:
        route_res_2 = router_module.calculate_route("ТРК", "Ялама")
        from_name_2 = route_res_2.get("from_canonical_name", "Ələt eksport-Türk.")
        to_name_2 = route_res_2.get("to_canonical_name", "Ялама")
        shipment_type_2 = route_res_2.get("shipment_type", "transit")
        distance_km_2 = route_res_2.get("distance_km", 200.0)

    print(f"  • Станция отправления: {from_name_2}")
    print(f"  • Станция назначения:  {to_name_2}")
    print(f"  • Тип перевозки:       {shipment_type_2}")
    print(f"  • Расстояние (ADY):    {distance_km_2} км")

    # Полный тарифный расчет
    res_2 = TariffCalculator.calculate(
        shipment_type=shipment_type_2,
        gng_code="27101900",
        actual_weight=50.0,
        distance_km=distance_km_2,
        wagon_type="cistern",
        from_canonical_name=from_name_2,
        to_canonical_name=to_name_2,
        is_private_wagon=True,
        wagon_length_m=13.0
    )

    print(f"\n  [Детализация финансового расчета]:")
    print(f"  • Базовая таблица:     {res_2['table_name']}")
    print(f"  • Расчетный вес:       {res_2['billable_weight']} т")
    print(f"  • Накат/Выкат (Алят):  ${res_2['total_ferry_fee_usd']:.2f} USD")
    print(f"  • Охрана (ВОХР):       ${res_2['security_fee_usd']:.2f} USD ({distance_km_2} км * 0.1 / 0.7)")
    print(f"  • Фрахт ASCO (ТРК):    ${res_2['total_asco_freight_usd']:.2f} USD (13м (фикс) х $70.0/м х коэф. 1.0)")
    print(f"  --------------------------------------------------")
    print(f"  🚀 ИТОГОВЫЙ ЧЕК:       ${res_2['final_rate_total_usd']:.2f} USD")
    print("=" * 75)

    assert res_2["security_fee_usd"] > 0
    assert res_2["total_asco_freight_usd"] == 910.0

# tests/test_full_pipeline_demo.py

import pytest
from core.router import RouteCalculator
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

    # 1. Роутер: авто-поиск ЕСР и километров
    route_1 = RouteCalculator.get_route_details("Беюк Кясик", "Курык")
    print(f"  • Станция отправления: {route_1.from_name} (ЕСР: {route_1.from_esr})")
    print(f"  • Станция назначения:  {route_1.to_name} (ЕСР: {route_1.to_esr})")
    print(f"  • Тип перевозки:       {route_1.shipment_type}")
    print(f"  • Расстояние (ADY):    {route_1.calculated_distance_km} км")

    # 2. Калькулятор: полный тарифный расчет
    res_1 = TariffCalculator.calculate(
        shipment_type=route_1.shipment_type,
        gng_code="10010000",
        actual_weight=35.0,
        distance_km=route_1.calculated_distance_km,
        wagon_type="hopper",
        from_canonical_name=route_1.from_name,
        to_canonical_name=route_1.to_name,
        is_private_wagon=True,  # СПС
        wagon_length_m=15.0
    )

    print(f"\n  [Детализация финансового расчета]:")
    print(f"  • Базовая таблица:     {res_1['table_name']}")
    print(f"  • Расчетный вес:       {res_1['billable_weight']} т (мин. норма)")
    print(f"  • Ставка Ж/Д (ADY):    ${res_1['final_rate_total_usd'] - res_1['total_ferry_fee_usd'] - res_1['total_asco_freight_usd'] - res_1['security_fee_usd']:.2f} USD")
    print(f"  • Накат/Выкат (Алят):  ${res_1['total_ferry_fee_usd']:.2f} USD")
    print(f"  • Охрана (ВОХР):       ${res_1['security_fee_usd']:.2f} USD ({route_1.calculated_distance_km} км * 0.1 / 0.7)")
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

    # 1. Роутер: авто-поиск ЕСР и километров
    route_2 = RouteCalculator.get_route_details("ТРК", "Ялама")
    print(f"  • Станция отправления: {route_2.from_name} (ЕСР: {route_2.from_esr})")
    print(f"  • Станция назначения:  {route_2.to_name} (ЕСР: {route_2.to_esr})")
    print(f"  • Тип перевозки:       {route_2.shipment_type}")
    print(f"  • Расстояние (ADY):    {route_2.calculated_distance_km} км")

    # 2. Калькулятор: полный тарифный расчет
    res_2 = TariffCalculator.calculate(
        shipment_type=route_2.shipment_type,
        gng_code="27101900",
        actual_weight=50.0,
        distance_km=route_2.calculated_distance_km,
        wagon_type="cistern",
        from_canonical_name=route_2.from_name,
        to_canonical_name=route_2.to_name,
        is_private_wagon=True,  # СПС
        wagon_length_m=13.0
    )

    print(f"\n  [Детализация финансового расчета]:")
    print(f"  • Базовая таблица:     {res_2['table_name']}")
    print(f"  • Расчетный вес:       {res_2['billable_weight']} т")
    print(f"  • Ставка Ж/Д (ADY):    ${res_2['final_rate_total_usd'] - res_2['total_ferry_fee_usd'] - res_2['total_asco_freight_usd'] - res_2['security_fee_usd']:.2f} USD")
    print(f"  • Накат/Выкат (Алят):  ${res_2['total_ferry_fee_usd']:.2f} USD (Выкат)")
    print(f"  • Охрана (ВОХР):       ${res_2['security_fee_usd']:.2f} USD ({route_2.calculated_distance_km} км * 0.1 / 0.7)")
    print(f"  • Фрахт ASCO (ТРК):    ${res_2['total_asco_freight_usd']:.2f} USD (13м (фикс) х $70.0/м х коэф. 1.0)")
    print(f"  --------------------------------------------------")
    print(f"  🚀 ИТОГОВЫЙ ЧЕК:       ${res_2['final_rate_total_usd']:.2f} USD")
    print("=" * 75)

    assert res_2["security_fee_usd"] > 0
    assert res_2["total_asco_freight_usd"] == 910.0

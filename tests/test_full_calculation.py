# tests/test_full_calculation.py

from core.router import RailwayRouter
from core.calculator import TariffCalculator


def run_test_case(
    raw_from: str,
    raw_to: str,
    gng_code: str,
    actual_weight: int,
    wagon_type: str,
    is_private_wagon: bool = False,
    is_empty: bool = False,
    is_methanol: bool = False,
    is_oil_product: bool = False
):
    """
    Выполняет полный цикл расчета без единой заглушки:
    Роутер (расстояние + режим) -> Калькулятор (норма веса + ставка + коэффициенты)
    """
    router = RailwayRouter(distances_file_path="data/distances.csv")

    # 1. Определение маршрута и типа перевозки
    route_res = router.calculate_route(raw_from, raw_to)

    # Берем расчетное расстояние (с учетом минимальных 151/101 км, если применимо)
    effective_distance = (
        route_res.calculated_distance_km
        if route_res.calculated_distance_km > 0
        else route_res.distance_km
    )

    # 2. Полный расчет тарифа
    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code=gng_code,
        actual_weight=actual_weight,
        distance_km=effective_distance,
        wagon_type=wagon_type,
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=is_private_wagon,
        is_empty=is_empty,
        is_methanol=is_methanol,
        is_oil_product=is_oil_product
    )

    print("\n" + "=" * 70)
    print(f"МАРШРУТ: {raw_from} -> {raw_to}")
    print("=" * 70)
    print(f"• Показ маршрута: {route_res.formatted_output('RU')}")
    print(f"• Фактическое расстояние: {route_res.distance_km} км")
    print(f"• Расчетное расстояние: {effective_distance} км")
    print(f"• Фактический вес: {actual_weight} т")
    print(f"• Расчетный вес (с нормой/Табл.1): {calc_res['billable_weight']} т")
    print(f"• Базовая ставка Таблицы 3: {calc_res['base_rate_chf_per_ton']} CHF/т")
    print(f"• Итоговый коэффициент правил: {calc_res['final_coeff']}")
    print(f"• Итоговая ставка за 1 тонну: {calc_res['final_rate_chf_per_ton']} CHF/т")

    if calc_res["notifications"]:
        print("\nПримененные правила и уведомления:")
        for n in calc_res["notifications"]:
            print(f"  - {n['rule_code']}: {n.get('params', {})}")


if __name__ == "__main__":
    # Контрольный пример #1: Импорт пшеницы (Ялама -> Апшерон)
    run_test_case(
        raw_from="Ялама",
        raw_to="Апшерон",
        gng_code="10019900",     # Пшеница (норма 60т)
        actual_weight=42,         # Меньше нормы
        wagon_type="крытый",
        is_private_wagon=True     # Коэффициент 0.85
    )

    # Контрольный пример #2: Экспорт пиломатериалов (Апшерон -> Ялама)
    run_test_case(
        raw_from="Апшерон",
        raw_to="Ялама",
        gng_code="44071100",     # Лесоматериалы (норма 45т)
        actual_weight=40,
        wagon_type="платформа",
        is_private_wagon=False
    )

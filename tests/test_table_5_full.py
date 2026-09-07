# tests/test_table_5_full.py

from core.router import RailwayRouter
from core.calculator import TariffCalculator
from data.translations import RULE_MESSAGES


def _format_msg(rule_code: str, params: dict, lang: str) -> str:
    """Форматирует строку перевода из RULE_MESSAGES с подстановкой параметров."""
    rule_data = RULE_MESSAGES.get(rule_code, {})
    template = rule_data.get(lang, rule_code)
    try:
        return template.format(**params) if params else template
    except KeyError:
        return template


def _print_calculation_result(test_name: str, route_res, calc_res, gng_code: str, actual_w: float, wagon_type: str, is_private: bool):
    """Вспомогательная функция для чистой печати результатов расчета Таблицы 5 в USD."""
    wagon_ownership = "СПС (приватный)" if is_private else "МПС (инвентарный)"
    table_name = calc_res.get("table_name", "Таблица 5")

    print("\n" + "=" * 80)
    print(f"   {test_name.upper()}")
    print("=" * 80)
    print(f"Маршрут: {route_res.formatted_output('RU')}")
    print(f"ГНГ код: {gng_code}")
    print(f"Тип вагона: {wagon_type} [{wagon_ownership}]")
    print(f"Вес (факт): {actual_w} т -> Расчетный (Табл.1/Норма): {calc_res['billable_weight']} т")
    print(f"Базовая ставка: {calc_res['base_rate_chf_per_ton']} CHF/т ({table_name})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']} USD/т\n")

    for note in calc_res["notifications"]:
        code = note["rule_code"]
        params = note.get("params", {})
        if code.startswith("MAIN_COEFF_"):
            ru_desc = _format_msg(code, params, "ru")
            if "1_04" in code:
                coeff_str = "1,04"
            elif "1_015" in code:
                coeff_str = "1,015"
            elif "0_85" in code:
                coeff_str = "0,85"
            elif "1_50" in code:
                coeff_str = "1,50"
            elif "1_20" in code:
                coeff_str = "1,20"
            else:
                coeff_str = ""
            print(f"Коэф. {coeff_str}: {ru_desc}")

    print(f"\nИтог за 1 т: {calc_res['final_rate_usd_per_ton']} USD/т\n")

    print("Уведомления:")
    for note in calc_res["notifications"]:
        code = note["rule_code"]
        params = note.get("params", {})
        az_text = _format_msg(code, params, "az")
        en_text = _format_msg(code, params, "en")
        print(f"AZ: {az_text}")
        print(f"EN: {en_text}")

    print("=" * 80 + "\n")


def test_refrigerator_import_calculation():
    """Тест 1: Импорт в рефрижераторе (Ялама -> Апшерон) | Реф. вагон | 28т | СПС"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Апшерон")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0404",
        actual_weight=28,
        distance_km=effective_dist,
        wagon_type="refrigerator",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("1. Импорт в рефрижераторе (Ялама -> Апшерон)", route_res, calc_res, "0404", 28, "refrigerator", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_thermos_transit_calculation():
    """Тест 2: Транзит в термосе (Ялама -> Беюк Кясик) | Термос | 22т | СПС"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="0709",
        actual_weight=22,
        distance_km=route_res.distance_km,
        wagon_type="thermos",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("2. Транзит в термосе (Ялама -> Беюк Кясик)", route_res, calc_res, "0709", 22, "thermos", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_car_carrier_export_calculation():
    """Тест 3: Экспорт автовозом (Апшерон -> Ялама) | Автовоз | 12т | СПС"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Апшерон", "Ялама")
    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8703",
        actual_weight=12,
        distance_km=effective_dist,
        wagon_type="car_carrier",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("3. Экспорт автовозом (Апшерон -> Ялама)", route_res, calc_res, "8703", 12, "car_carrier", True)
    assert calc_res["base_rate_chf_per_ton"] > 0


def test_inv_anv_empty_calculation():
    """Тест 4: Порожний проход ИНВ/АНВ (Ялама -> Беюк Кясик) | ИНВ/АНВ | 0т | Порожний"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="8606",
        actual_weight=0,
        distance_km=route_res.distance_km,
        wagon_type="inv_anv",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("4. Порожний проход ИНВ/АНВ (Ялама -> Беюк Кясик)", route_res, calc_res, "8606", 0, "inv_anv", False)
    assert calc_res["base_rate_chf_per_ton"] > 0

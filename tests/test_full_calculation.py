# tests/test_full_calculation.py

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
    """Вспомогательная функция для чистой печати результатов расчета в USD."""
    wagon_ownership = "СПС (приватный)" if is_private else "МПС (инвентарный)"
    ship_type = route_res.shipment_type.value.lower()
    
    # Динамически определяем имя таблицы
    table_name = "Таблица 4" if ship_type in ["transit", "транзит", "tranzit"] else "Таблица 3"

    print("\n" + "=" * 80)
    print(f"    {test_name.upper()}")
    print("=" * 80)
    print(f"Маршрут: {route_res.formatted_output('RU')}")
    print(f"ГНГ код: {gng_code}")
    print(f"Тип вагона: {wagon_type} [{wagon_ownership}]")
    print(f"Вес (факт): {actual_w} т -> Расчетный (Табл.1/Норма): {calc_res['billable_weight']} т")
    print(f"Базовая ставка: {calc_res['base_rate_chf_per_ton']} CHF/т ({table_name})")
    print(f"Курс конвертации (CHF -> USD): {calc_res['exchange_rate']}")
    print(f"Базовая ставка в USD: {calc_res['base_rate_usd_per_ton']} USD/т\n")

    # Вывод коэффициентов (на русском языке)
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


def test_import_wheat_min_load():
    """Тест 1: Импорт пшеницы (Ялама -> Апшерон)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Апшерон")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="10019900",
        actual_weight=42,
        distance_km=effective_dist,
        wagon_type="крытый",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("1. Импорт пшеницы (Ялама -> Апшерон)", route_res, calc_res, "10019900", 42, "крытый", True)
    assert calc_res["billable_weight"] == 60


def test_export_timber():
    """Тест 2: Экспорт лесоматериалов (Апшерон -> Ялама)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Апшерон", "Ялама")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="44071100",
        actual_weight=40,
        distance_km=effective_dist,
        wagon_type="платформа",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("2. Экспорт леса (Апшерон -> Ялама)", route_res, calc_res, "44071100", 40, "платформа", False)
    assert calc_res["billable_weight"] == 45


def test_import_timber_sps():
    """Тест 4: Ялама -> Апшерон | ГНГ 4407 | платформа | 35т | СПС (приватный)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Апшерон")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="4407",
        actual_weight=35,
        distance_km=effective_dist,
        wagon_type="платформа",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("4. Импорт леса СПС (Ялама -> Апшерон)", route_res, calc_res, "4407", 35, "платформа", True)
    assert calc_res["billable_weight"] == 45


def test_paper_bilajari_boyuk_kesik():
    """Тест 5: Баладжары -> Беюк Кясик | ГНГ 4818 | хоппер | 26т | МПС (инвентарный)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Баладжары", "Беюк Кясик")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="4818",
        actual_weight=26,
        distance_km=effective_dist,
        wagon_type="хоппер",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("5. Изделия из бумаги МПС (Баладжары -> Беюк Кясик)", route_res, calc_res, "4818", 26, "хоппер", False)
    assert calc_res["actual_weight"] == 26


def test_alat_exp_boyuk_kesik():
    """Тест 6: Алят (эксп) -> Беюк Кясик | ГНГ 78 | крытый | 35т | СПС | Ноябрь 2026"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Алят-эксп.", "Беюк Кясик")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="78",
        actual_weight=35,
        distance_km=effective_dist,
        wagon_type="крытый",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True,
        shipment_date="15.11.2026"
    )

    _print_calculation_result("6. Алят (эксп) -> Беюк Кясик (Ноябрь 2026)", route_res, calc_res, "78", 35, "крытый", True)
    assert calc_res["exchange_rate"] == 0.81


def test_kuryk_khirdalan():
    """Тест 7: Курык -> Хырдалан | ГНГ 28049 | платформа | 50т | СПС"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Курык", "Хырдалан")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="28049",
        actual_weight=50,
        distance_km=effective_dist,
        wagon_type="платформа",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("7. Курык -> Хырдалан (ГНГ 28049)", route_res, calc_res, "28049", 50, "платформа", True)
    assert calc_res["actual_weight"] == 50
    assert calc_res["billable_weight"] == 60


def test_yalama_trk_wheat_hopper():
    """Тест 8: Ялама -> ТРК | ГНГ 1001 | хоппер | 55т | СПС"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "ТРК")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="1001",
        actual_weight=55,
        distance_km=effective_dist,
        wagon_type="хоппер",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=True
    )

    _print_calculation_result("8. Ялама -> ТРК Пшеница Хоппер", route_res, calc_res, "1001", 55, "хоппер", True)
    assert calc_res["actual_weight"] == 55


def test_transit_coal_yalama_boyuk_kesik():
    """Тест: Транзит угля (Ялама -> Беюк Кясик, 60 т, полувагон)"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    route_res = router.calculate_route("Ялама", "Беюк Кясик")

    effective_dist = route_res.calculated_distance_km if route_res.calculated_distance_km > 0 else route_res.distance_km

    calc_res = TariffCalculator.calculate(
        shipment_type=route_res.shipment_type.value,
        gng_code="27011100",
        actual_weight=60,
        distance_km=effective_dist,
        wagon_type="полувагон",
        from_canonical_name=route_res.from_station.canonical_name,
        to_canonical_name=route_res.to_station.canonical_name,
        is_private_wagon=False
    )

    _print_calculation_result("Транзит угля (Ялама -> Беюк Кясик)", route_res, calc_res, "27011100", 60, "полувагон", False)
    assert calc_res["base_rate_chf_per_ton"] > 0

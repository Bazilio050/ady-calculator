import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.route_helpers import normalize_nlu_stations
from core.calculator import calculate_freight

# ==============================================================================
# КОМПЛЕКСНАЯ МАТРИЦА ТЕСТОВ ADY TARIFF CALCULATOR 2026
# ==============================================================================

POSITIVE_TEST_CASES = [
    {
        "name": "A1. Транзит: Погранпереход -> Погранпереход (Ялама -> Ələt-eksp.)",
        "input": "Ялама Алят эксп 4407 крытый 35т спс",
        "mock_nlu": {
            "from_station": "Yalama",
            "to_station": "Ələt",
            "gng_code": "4407",
            "fact_weight": 35.0,
            "wagon_type": "крытый",
            "is_private_wagon": True
        },
        "expected_to": "Ələt-eksp.",
        "expected_type": "transit",
        "expected_table": "4",
        "expected_min_ton": 45
    },
    {
        "name": "A2. Транзит с паромом: Порт Курык (Ələt Kurik 553002)",
        "input": "Ялама Алят эксп Курык 4407 крытый 35т",
        "mock_nlu": {
            "from_station": "Yalama",
            "to_station": "Ələt",
            "gng_code": "4407",
            "fact_weight": 35.0,
            "wagon_type": "крытый",
            "is_private_wagon": True
        },
        "expected_to": "Ələt-eksp.Kurik",
        "expected_type": "transit",
        "expected_table": "4",
        "expected_min_ton": 45
    },
    {
        "name": "A3. Транзит с паромом: Порт Актау (Ələt Aktau 549204)",
        "input": "Ялама Актау 4407 крытый 35т",
        "mock_nlu": {
            "from_station": "Yalama",
            "to_station": "Aktau",
            "gng_code": "4407",
            "fact_weight": 35.0,
            "wagon_type": "крытый",
            "is_private_wagon": True
        },
        "expected_to": "Ələt-eksp.Aktau",
        "expected_type": "transit",
        "expected_table": "4",
        "expected_min_ton": 45
    },
    {
        "name": "A4. Транзит на стык: Беюк Кясик-експ (558701)",
        "input": "Ялама Беюк Кясик 4407 крытый 35т",
        "mock_nlu": {
            "from_station": "Yalama",
            "to_station": "Böyük Kəsik",
            "gng_code": "4407",
            "fact_weight": 35.0,
            "wagon_type": "крытый",
            "is_private_wagon": True
        },
        "expected_to": "Böyük Kəsik-eksp.",
        "expected_type": "transit",
        "expected_table": "4",
        "expected_min_ton": 45
    },
    {
        "name": "A5. Импорт: Погранпереход -> Внутренняя станция (Ялама -> Абшерон)",
        "input": "Ялама Абшерон 4407 крытый 35т импорт",
        "mock_nlu": {
            "from_station": "Yalama",
            "to_station": "Abşeron",
            "gng_code": "4407",
            "fact_weight": 35.0,
            "wagon_type": "крытый",
            "is_private_wagon": True
        },
        "expected_to": "Abşeron",
        "expected_type": "import",
        "expected_table": "3",
        "expected_min_ton": 45
    },
    {
        "name": "A6. Cədvəl 5: Рефсекция 5+1 (Ялама -> Хырдалан, Импорт, 45т)",
        "input": "Ялама Хырдалан 0207 рефсекция 5+1 45т импорт",
        "mock_nlu": {
            "from_station": "Yalama",
            "to_station": "Xırdalan",
            "gng_code": "0207",
            "fact_weight": 45.0,
            "wagon_type": "ref_section",
            "ref_cars_count": 5,
            "is_private_wagon": True
        },
        "expected_to": "Xırdalan",
        "expected_type": "import",
        "expected_table": "5"
    }
]

NEGATIVE_TEST_CASES = [
    {
        "name": "B1. Ошибка: Отсутствует код ГНГ для груженого вагона",
        "params": {
            "from_station": "Yalama-eksp.",
            "to_station": "Abşeron",
            "gng_code": "",
            "fact_weight": 35.0,
            "shipment_type": "import",
            "is_empty_wagon": False
        },
        "expected_error": "gng_code_required"
    },
    {
        "name": "B2. Ошибка: Маршрут отсутствует в справочнике",
        "params": {
            "from_station": "UnknownStation1",
            "to_station": "UnknownStation2",
            "gng_code": "4407",
            "fact_weight": 35.0,
            "shipment_type": "import",
            "is_empty_wagon": False
        },
        "expected_error": "route_not_found"
    },
    {
        "name": "B3. Ошибка: Дата вычисления выходит за границы справочника FX_RATES",
        "params": {
            "from_station": "Yalama-eksp.",
            "to_station": "Abşeron",
            "gng_code": "4407",
            "fact_weight": 35.0,
            "shipment_type": "import",
            "calculation_date": "2030-01-01"
        },
        "expected_error": "fx_rate_not_found"
    }
]

def run_tests():
    print("🚀 ЗАПУСК ПОЛНОЙ МАТРИЦЫ ТЕСТИРОВАНИЯ ADY 2026 (RULES.md COMPLIANT)")
    print("=" * 85)
    
    passed = 0
    total = len(POSITIVE_TEST_CASES) + len(NEGATIVE_TEST_CASES)

    print("\n--- ЧАСТЬ 1: Позитивные сценарии расчетов ---")
    for idx, test in enumerate(POSITIVE_TEST_CASES, 1):
        name = test["name"]
        raw_in = test["input"]
        mock_nlu = test["mock_nlu"]
        exp_to = test["expected_to"]
        exp_type = test["expected_type"]
        exp_table = test.get("expected_table")
        exp_min_ton = test.get("expected_min_ton")

        try:
            norm_res = normalize_nlu_stations(mock_nlu, raw_in)
            
            calc_result = calculate_freight(
                from_station=norm_res.get("from_station"),
                to_station=norm_res.get("to_station"),
                gng_code=mock_nlu.get("gng_code"),
                fact_weight=mock_nlu.get("fact_weight", 0.0),
                wagon_type=mock_nlu.get("wagon_type", "universal"),
                shipment_type=norm_res.get("shipment_type", "import"),
                is_empty_wagon=mock_nlu.get("is_empty_wagon", False),
                is_private_wagon=mock_nlu.get("is_private_wagon", True),
                ref_cars_count=mock_nlu.get("ref_cars_count"),
                apply_fresh_produce_discount=mock_nlu.get("apply_fresh_produce_discount", False),
                raw_prompt=raw_in
            )

            total_usd = calc_result.get("total_usd", 0.0)
            part1 = calc_result.get("part1", {})
            part2 = calc_result.get("part2", {})

            actual_route = part1.get("route", "")
            
            to_ok = exp_to in actual_route or exp_to in str(norm_res.get("to_station", ""))
            type_ok = (norm_res.get("shipment_type") == exp_type)
            calc_ok = total_usd > 0
            table_ok = exp_table in part2.get("base_tariff", "") if exp_table else True
            min_ton_ok = f"{exp_min_ton} t" in part1.get("weight_info", "") if exp_min_ton else True

            if to_ok and type_ok and calc_ok and table_ok and min_ton_ok:
                print(f"  [PASSED] Тест A{idx}: {name}")
                passed += 1
            else:
                print(f"  [FAILED] Тест A{idx}: {name}")
                print(f"    Получено: Route='{actual_route}', Type='{norm_res.get('shipment_type')}', USD={total_usd}, Tariff='{part2.get('base_tariff')}'")

        except Exception as e:
            print(f"  [FAILED] Тест A{idx}: {name} | Исключение: {e}")

    print("\n--- ЧАСТЬ 2: Отрицательные тесты и перехват исключений ---")
    for idx, test in enumerate(NEGATIVE_TEST_CASES, 1):
        name = test["name"]
        params = test["params"]
        exp_err = test["expected_error"]

        try:
            calculate_freight(**params)
            print(f"  [FAILED] Тест B{idx}: {name} | Ошибка не выброшена!")
        except ValueError as e:
            if exp_err in str(e):
                print(f"  [PASSED] Тест B{idx}: {name} (Корректно выброшено '{exp_err}')")
                passed += 1
            else:
                print(f"  [FAILED] Тест B{idx}: {name} | Ожидалось '{exp_err}', получено '{e}'")
        except Exception as e:
            print(f"  [FAILED] Тест B{idx}: {name} | Неожиданное исключение: {e}")

    print("\n" + "=" * 85)
    print(f"ИТОГ: Успешно пройдено {passed} из {total} тестов.")
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

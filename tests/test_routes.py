import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.route_helpers import normalize_nlu_stations
from core.calculator import calculate_freight

TEST_CASES = [
    {
        "name": "1. Обобщенный Алят эксп (без порта) -> Ələt-eksp. + Transit",
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
        "name": "2. Алят Курык -> Ələt Kurik (553002)",
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
        "name": "3. Алят Актау -> Ələt Aktau (549204)",
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
        "name": "4. Стык Беюк Кясик (без явного слова эксп в тексте)",
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
        "name": "5. Порожний возврат (автоприсвоение GNG 99220000)",
        "input": "Ялама Астара эксп порожний",
        "mock_nlu": {
            "from_station": "Yalama",
            "to_station": "Astara",
            "gng_code": None,
            "fact_weight": 0.0,
            "wagon_type": "крытый",
            "is_empty_wagon": True,
            "is_private_wagon": True
        },
        "expected_to": "Astara-eksp.",
        "expected_type": "transit",
        "expected_table": "4"
    },
    {
        "name": "6. Импорт на Абшерон (Погранпереход -> Внутренняя станция)",
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
    }
]

def run_tests():
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ: СТРОГАЯ ВАЛИДАЦИЯ ТАРИФОВ И МАРШРУТОВ ADY 2026")
    print("=" * 85)
    
    passed = 0
    total = len(TEST_CASES)

    for idx, test in enumerate(TEST_CASES, 1):
        name = test["name"]
        raw_in = test["input"]
        mock_nlu = test["mock_nlu"]
        exp_to = test["expected_to"]
        exp_type = test["expected_type"]
        exp_table = test.get("expected_table")
        exp_min_ton = test.get("expected_min_ton")

        try:
            # 1. Нормализация станций и видов перевозок
            norm_res = normalize_nlu_stations(mock_nlu, raw_in)
            
            # 2. Расчет калькулятором без передаваемого вручную километража
            calc_result = calculate_freight(
                from_station=norm_res.get("from_station"),
                to_station=norm_res.get("to_station"),
                gng_code=mock_nlu.get("gng_code"),
                fact_weight=mock_nlu.get("fact_weight", 0.0),
                wagon_type=mock_nlu.get("wagon_type", "universal"),
                shipment_type=norm_res.get("shipment_type", "import"),
                is_empty_wagon=mock_nlu.get("is_empty_wagon", False),
                is_private_wagon=mock_nlu.get("is_private_wagon", True),
                raw_prompt=raw_in
            )

            total_usd = calc_result.get("total_usd", 0.0)
            part1 = calc_result.get("part1", {})
            part2 = calc_result.get("part2", {})
            part3 = calc_result.get("part3", {})

            actual_route = part1.get("route", "")
            actual_dist_str = part1.get("distance", "")
            
            to_ok = exp_to in actual_route or exp_to in str(norm_res.get("to_station", ""))
            type_ok = (norm_res.get("shipment_type") == exp_type)
            calc_ok = total_usd > 0
            table_ok = exp_table in part2.get("base_tariff", "") if exp_table else True
            min_ton_ok = f"{exp_min_ton} t" in part1.get("weight_info", "") if exp_min_ton else True

            if to_ok and type_ok and calc_ok and table_ok and min_ton_ok:
                print(f"\nТест {idx}: {name}")
                print(f"  Ввод:         '{raw_in}'")
                print(f"  Маршрут:      {actual_route} ({actual_dist_str})")
                print(f"  Вид / Вес:    {norm_res.get('shipment_type').upper()} | {part1.get('weight_info')}")
                print(f"  Ставка CHF:   {part2.get('base_tariff')}")
                print(f"  Формула:      {part3.get('formula')}")
                print(f"  Итого USD:    {total_usd:.2f} $")
                print(f"  Статус:       ✅ PASSED")
                passed += 1
            else:
                print(f"\nТест {idx}: {name}")
                print(f"  Ввод:         '{raw_in}'")
                print(f"  Маршрут:      {actual_route}")
                print(f"  Вид:          Получено: {norm_res.get('shipment_type')} | Ожидалось: {exp_type}")
                print(f"  Тариф:        Итого: {total_usd:.2f} $ | {part2.get('base_tariff')}")
                print(f"  Статус:       ❌ FAILED")

        except Exception as e:
            print(f"\nТест {idx}: {name}\n  Ошибка выполнения: {e}\n  Статус:      ❌ FAILED")

    print("\n" + "=" * 85)
    print(f"ИТОГ: Успешно пройдено {passed} из {total} тестов.")
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

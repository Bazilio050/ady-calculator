# tests/test_routes.py
import sys
import os

# Добавляем корень проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.calculator import calculate_freight

TEST_CASES = [
    {
        "name": "1. Обобщенный Алят эксп (без порта) -> Ələt-eksp. + Transit",
        "input": "Ялама Алят эксп 4407 крытый 35т спс",
        "expected_to": "Ələt-eksp.",
        "expected_dist": 271,
        "expected_type": "transit"
    },
    {
        "name": "2. Алят Курык -> Ələt Kurik (553002)",
        "input": "Ялама Алят эксп Курык 4407 крытый 35т",
        "expected_to": "Ələt-eksp.Kurik",
        "expected_dist": 271,
        "expected_type": "transit"
    },
    {
        "name": "3. Алят Актау -> Ələt Aktau (549204)",
        "input": "Ялама Актау 4407 крытый 35т",
        "expected_to": "Ələt-eksp.Aktau",
        "expected_dist": 271,
        "expected_type": "transit"
    },
    {
        "name": "4. Стык Беюк Кясик (без явного слова эксп в тексте)",
        "input": "Ялама Беюк Кясик 4407 крытый 35т",
        "expected_to": "Böyük Kəsik-eksp.",
        "expected_dist": 680,
        "expected_type": "transit"
    },
    {
        "name": "5. Стык Астара",
        "input": "Ялама Астара эксп",
        "expected_to": "Astara (eks.aşır)",
        "expected_dist": 504,
        "expected_type": "transit"
    },
    {
        "name": "6. Импорт на Абшерон (Погранпереход -> Внутренняя станция)",
        "input": "Ялама Абшерон 4407 крытый 35т",
        "expected_to": "Abşeron",
        "expected_dist": 204,
        "expected_type": "import"
    }
]

def run_tests():
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ МАРШРУТОВ И ТИПОВ ПЕРЕВОЗОК ADY")
    print("=" * 75)
    
    passed = 0
    total = len(TEST_CASES)

    for idx, test in enumerate(TEST_CASES, 1):
        name = test["name"]
        raw_in = test["input"]
        exp_to = test["expected_to"]
        exp_dist = test["expected_dist"]
        exp_type = test["expected_type"]

        try:
            res = calculate_freight(raw_in)
            actual_route = res.get("route_formatted", "")
            actual_dist = res.get("distance_km", 0)
            actual_type = res.get("shipment_type", "")

            to_ok = exp_to in actual_route or exp_to in str(res.get("to_station", ""))
            dist_ok = (actual_dist == exp_dist)
            type_ok = (actual_type == exp_type)

            if to_ok and dist_ok and type_ok:
                print(f"\nТест {idx}: {name}\n  Ввод:         '{raw_in}'\n  Маршрут:     {actual_route}\n  Результат:   {actual_dist} км | Вид: {actual_type}\n  Статус:      ✅ PASSED")
                passed += 1
            else:
                print(f"\nТест {idx}: {name}\n  Ввод:         '{raw_in}'\n  Маршрут:     {actual_route}\n  Результат:   {actual_dist} км | Вид: {actual_type}\n  Ожидалось:   {exp_to} | {exp_dist} км | Вид: {exp_type}\n  Статус:      ❌ FAILED")
        except Exception as e:
            print(f"\nТест {idx}: {name}\n  Ошибка выполнения: {e}\n  Статус:      ❌ FAILED")

    print("\n" + "=" * 75)
    print(f"ИТОГ: Успешно пройдено {passed} из {total} тестов.")
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

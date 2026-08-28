import os
import sys

# Добавляем корень проекта в путь импорта Python
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.distance_finder import get_route_info

def run_tests():
    test_cases = [
        {
            "name": "1. Обобщенный Алят эксп (без порта) -> Ələt-eksp. + Transit",
            "input": {"raw_input": "Ялама Алят эксп 4407 крытый 35т спс", "from_station": "Yalama", "to_station": "Ələt eksport"},
            "expected_to": "Ələt-eksp.",
            "expected_dist": 271,
            "expected_type": "transit"
        },
        {
            "name": "2. Алят Курык -> Ələt Kurik (553002)",
            "input": {"raw_input": "Ялама Алят эксп Курык 4407 крытый 35т", "from_station": "Yalama", "to_station": "Ələt eksport Kurik"},
            "expected_to": "Ələt Kurik (553002)",
            "expected_dist": 271,
            "expected_type": "transit"
        },
        {
            "name": "3. Алят Актау -> Ələt Aktau (549204)",
            "input": {"raw_input": "Ялама Актау 4407 крытый 35т", "from_station": "Yalama", "to_station": "Ələt eksport Aktau"},
            "expected_to": "Ələt Aktau (549204)",
            "expected_dist": 271,
            "expected_type": "transit"
        },
        {
            "name": "4. Алят ТРК -> Ələt Turk. (548803)",
            "input": {"raw_input": "Беюк Кясик ТРК 4407 крытый 35т", "from_station": "Böyük Kəsik", "to_station": "Ələt eksport-Türk."},
            "expected_to": "Ələt Turk. (548803)",
            "expected_dist": 503,
            "expected_type": "transit"
        },
        {
            "name": "5. Стык Беюк Кясик (без явного слова эксп в тексте)",
            "input": {"raw_input": "Ялама Беюк Кясик 4407 крытый 35т", "from_station": "Yalama", "to_station": "Böyük Kəsik"},
            "expected_to": "Böyük Kəsik-eksp. (548004)",
            "expected_dist": 503,
            "expected_type": "transit"
        },
        {
            "name": "6. Стык Астара",
            "input": {"raw_input": "Ялама Астара эксп", "from_station": "Yalama", "to_station": "Astara"},
            "expected_to": "Astara-eksp. (548907)",
            "expected_dist": 505,
            "expected_type": "transit"
        },
        {
            "name": "7. Импорт на Абшерон (Погранпереход -> Внутренняя станция)",
            "input": {"raw_input": "Ялама Абшерон 4407 крытый 35т", "from_station": "Yalama", "to_station": "Abşeron"},
            "expected_to": "Abşeron (545127)",
            "expected_dist": 202,
            "expected_type": "import"
        }
    ]

    print("=" * 75)
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ МАРШРУТОВ И ТИПОВ ПЕРЕВОЗОК ADY")
    print("=" * 75)

    passed = 0
    for idx, case in enumerate(test_cases, start=1):
        res = get_route_info(case["input"])
        from_fmt = res.get("from_formatted", "")
        to_fmt = res.get("to_formatted", "")
        dist = res.get("distance_km", 0)

        # 1. Применяем правило фильтрации портов из app.py
        raw_text_lower = case["input"]["raw_input"].lower()
        has_explicit_port = any(p in raw_text_lower for p in ["aktau", "актау", "kurik", "kuryk", "курык", "trk", "туркмен"])
        
        if not has_explicit_port and ("Ələt" in to_fmt or "Alat" in to_fmt or "Алят" in to_fmt):
            to_fmt = "Ələt-eksp."

        # 2. Определение транзита для межпограничных станций
        st_from_lower = from_fmt.lower()
        st_to_lower = to_fmt.lower()
        border_kw = ["eksp", "exp", "эксп", "экс", "export"]
        
        shipment_type = "transit" if (any(b in st_from_lower for b in border_kw) and any(b in st_to_lower for b in border_kw)) else "import"

        # 3. Проверка успешности теста
        is_ok = (to_fmt == case["expected_to"]) and (dist == case["expected_dist"]) and (shipment_type == case["expected_type"])
        status = "✅ PASSED" if is_ok else "❌ FAILED"
        if is_ok:
            passed += 1

        print(f"\nТест {idx}: {case['name']}")
        print(f"  Ввод:         '{case['input']['raw_input']}'")
        print(f"  Маршрут:     {from_fmt} – {to_fmt}")
        print(f"  Результат:   {dist} км | Вид: {shipment_type}")
        print(f"  Ожидалось:   {case['expected_to']} | {case['expected_dist']} км | Вид: {case['expected_type']}")
        print(f"  Статус:      {status}")

    print("\n" + "=" * 75)
    print(f"ИТОГ: Успешно пройдено {passed} из {len(test_cases)} тестов.")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()

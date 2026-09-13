# demo_asco.py

from core.asco_calculator import AscoFerryCalculator

def run_demo():
    print("=" * 70)
    print("          НАГЛЯДНАЯ ДЕМОНСТРАЦИЯ РАСЧЕТА МОРСКОГО ФРАХТА ASCO          ")
    print("=" * 70)

    test_cases = [
        {
            "title": "1. Стандартный груз в крытом вагоне (Алят -> Туркменбаши)",
            "params": {
                "route_from": "Алят-эксп.",
                "route_to": "Туркменбаши",
                "gng_code": "100190",      # Пшеница
                "wagon_type": "covered",
                "wagon_length_m": 14.0
            }
        },
        {
            "title": "2. Нефть в цистерне (Алят -> Курык) [Фиксированная длина 13м]",
            "params": {
                "route_from": "Алят-эксп.",
                "route_to": "Курык",
                "gng_code": "27090090",    # Нефть сырая
                "wagon_type": "cistern",
                "wagon_length_m": 18.0     # Длина 18м сбросится до 13м по спецправилу
            }
        },
        {
            "title": "3. Алкогольная продукция / Виноматериалы (Алят -> Туркменбаши)",
            "params": {
                "route_from": "Алят-эксп.",
                "route_to": "Туркменбаши",
                "gng_code": "220421",      # Вина виноградные
                "wagon_type": "cistern",
                "wagon_length_m": 14.0
            }
        },
        {
            "title": "4. Опасный груз Класса 8 (Алят -> Курык) [Повышенный тариф]",
            "params": {
                "route_from": "Алят-эксп.",
                "route_to": "Курык",
                "gng_code": "280610",      # Кислота соляная
                "wagon_type": "covered",
                "wagon_length_m": 14.0,
                "is_dangerous": True,
                "dangerous_class": 8
            }
        },
        {
            "title": "5. Негабаритный вагон > 15м и шириной 4.1м (Алят -> Курык)",
            "params": {
                "route_from": "Алят-эксп.",
                "route_to": "Курык",
                "gng_code": "840110",      # Оборудование
                "wagon_type": "platform",
                "wagon_length_m": 16.0,
                "wagon_width_m": 4.1
            }
        }
    ]

    for case in test_cases:
        print(f"\n📌 {case['title']}")
        res = AscoFerryCalculator.calculate(**case['params'])
        print(f"   • Статус:          {res['status']}")
        print(f"   • Порт:            {res.get('port', '-')}")
        print(f"   • Категория груза: {res.get('cargo_category', '-')}")
        print(f"   • Расчетная длина: {res.get('length_meters', 0.0)} м")
        print(f"   • Ставка за метр:  ${res.get('rate_per_meter', 0.0)} / m")
        print(f"   • Коэффициент:     {res.get('coeff', 1.0)}")
        print(f"   • ИТОГО ФРАХТ:     ${res.get('total_asco_usd', 0.0)} USD")
        print("-" * 70)

if __name__ == "__main__":
    run_demo()

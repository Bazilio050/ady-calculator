# tests/test_main_rules.py

from core.main_rules import apply_main_rules


def test_visual_main_rules():
    # Тестовые кейсы: передаем сэмулированные параметры отправки
    test_cases = [
        (
            "Импорт общего груза (Цемент)",
            {"shipment_type": "import", "gng_code": "25232900", "wagon_type": "other", "from_canonical_name": "Yalama (eksport)", "to_canonical_name": "Abşeron"},
            1.50
        ),
        (
            "Импорт леса (ГНГ 4403)",
            {"shipment_type": "import", "gng_code": "44031100", "wagon_type": "other", "from_canonical_name": "Yalama (eksport)", "to_canonical_name": "Abşeron"},
            1.04
        ),
        (
            "Транзит по коридору Алят -> Беюк Кясик",
            {"shipment_type": "transit", "gng_code": "87030000", "wagon_type": "other", "from_canonical_name": "Ələt eksport-Kurik", "to_canonical_name": "Böyük Kəsik (eksport)"},
            1.20
        ),
        (
            "Транзит нефти в цистерне Алят -> Беюк Кясик (однократно 1.20)",
            {"shipment_type": "transit", "gng_code": "27101900", "wagon_type": "tank", "from_canonical_name": "Ələt eksport-Türk.", "to_canonical_name": "Böyük Kəsik (eksport)", "is_oil_product": True},
            1.20
        ),
        (
            "Экспорт арматуры (ГНГ 72)",
            {"shipment_type": "export", "gng_code": "72142000", "wagon_type": "other", "from_canonical_name": "Abşeron", "to_canonical_name": "Böyük Kəsik (eksport)"},
            1.00
        ),
        (
            "Перевозка цветных металлов (ГНГ 74)",
            {"shipment_type": "transit", "gng_code": "74031100", "wagon_type": "other", "from_canonical_name": "Yalama (eksport)", "to_canonical_name": "Astara (eks.aşır)"},
            1.20
        ),
    ]

    print("\n" + "=" * 80)
    print("      ПРОВЕРКА РАБОТЫ ГЛАВНЫХ (СКВОЗНЫХ) ПРАВИЛ ADY")
    print("=" * 80)

    for idx, (description, params, expected_coeff) in enumerate(test_cases, 1):
        try:
            res = apply_main_rules(**params)
            actual_coeff = res["calculated_value"]
            is_correct = (actual_coeff == expected_coeff)
            status = "✅" if is_correct else "❌"

            print(f"\n{idx}. {description} {status}")
            print(f"   Параметры: {params['shipment_type'].upper()} | ГНГ: {params['gng_code']} | Вагон: {params['wagon_type']}")
            print(f"   Итоговый коэффициент: {actual_coeff} (Ожидалось: {expected_coeff})")
            
            if res["rules"]:
                print("   Сработавшие правила:")
                for r in res["rules"]:
                    print(f"     - {r['rule_code']}: x{r['calculated_value']}")
            else:
                print("   Сработавшие правила: Нет (базовый 1.0)")

        except Exception as e:
            print(f"\n{idx}. {description}")
            print(f"   Ошибка: ({e}) ❌")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    test_visual_main_rules()

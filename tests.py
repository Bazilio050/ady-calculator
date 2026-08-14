import sys
import re
from utils import load_rules_config
from engine import process_full_calculation

UI_T = {
    "unit_wagon": "USD/vaqon", "unit_ton": "USD/t",
    "type_import": "İdxal daşınması", "type_export": "İxrac daşınması", "type_transit": "Tranzit daşınması",
    "note_sps": "SPS güzəşt 0.85", "note_import": "Min 151 km", "note_export": "Min 101 km",
    "note_import_base_150": "Import/Export 1.50", "note_express": "Express +2%",
    "note_timber_metal": "Timber/Metal 1.04", "note_ref_transit_120": "Ref transit 1.20",
    "note_coef_1015": "Add coeff 1.015", "note_min_weight": "Min weight"
}

TEST_SUITE = [
    {
        "name": "1. Ялама -> Апшерон (4407, 35т, крытый, СПС)",
        "raw_text": "Ялама Апшерон 4407 35т крытый СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "4407", "cargo_name": "Taxta",
            "actual_weight_tons": 35.0, "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 17.26
    },
    {
        "name": "2. Ялама -> Баладжары (0207, реф 5+1, 35т, СПС)",
        "raw_text": "Ялама - Баладжары 0207 рефвагон 5+1 35т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Biləcəri", "cargo_gng_code": "0207", "cargo_name": "Ət və ət məhsulları",
            "actual_weight_tons": 35.0, "wagon_type": "ref", "park_type": "SPS", "ref_section_cargo_wagons": 5, "explicit_mode": "import"
        },
        "expected_rate": 33.53
    },
    {
        "name": "3. Ялама -> Беюк-Кясик (78, крытый, 60т, СПС)",
        "raw_text": "Ялама БеюкКясик 78 крытый 60т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Böyük Kəsik", "cargo_gng_code": "0078", "cargo_name": "Aşırılan yük",
            "actual_weight_tons": 60.0, "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 38.14
    },
    {
        "name": "4. Баку тов -> Ялама (2713, цистерна, 60т, СПС)",
        "raw_text": "Баку тов Ялама 2713 цистерна 60тн СПС",
        "nlu": {
            "route_from": "Bakı Yük (547105)", "route_to": "Yalama", "cargo_gng_code": "2713", "cargo_name": "Neft məhsulları",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 18.84
    },
    {
        "name": "5. Ялама -> Гюздек (3404, цистерна, 60т, СПС)",
        "raw_text": "Ялама Гюздек 3404 цистерна 60т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Güzdək", "cargo_gng_code": "3404", "cargo_name": "Neft məhsulları",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 16.80
    },
    {
        "name": "6. Ялама -> Гюздек (3404, цистерна, 60т, МПС)",
        "raw_text": "Ялама Гюздек 3404 цистерна 60т МПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Güzdək", "cargo_gng_code": "3404", "cargo_name": "Neft məhsulları",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "MPS", "explicit_mode": "import"
        },
        "expected_rate": 19.76
    },
    {
        "name": "7. Г.Тагиев -> Беюк Кясик (2705, цистерна, 60т, СПС)",
        "raw_text": "Г.Тагиев Беюк Кясик 2705 цистерна 60т СПС",
        "nlu": {
            "route_from": "H.Z. Tağıyev", "route_to": "Böyük Kəsik", "cargo_gng_code": "2705", "cargo_name": "Enerjili qazlar",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 40.84
    },
    {
        "name": "8. Г.Тагиев -> Ялама (28042, цистерна, 50т, СПС)",
        "raw_text": "Г.Тагиев Ялама 28042 цистерна 50т СПС",
        "nlu": {
            "route_from": "H.Z. Tağıyev", "route_to": "Yalama", "cargo_gng_code": "28042", "cargo_name": "Qazlar və karbohidrogenlər",
            "actual_weight_tons": 50.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 58.35
    },
    {
        "name": "9. Баладжары -> Ялама (39053, цистерна, 60т, СПС)",
        "raw_text": "Баладжары Ялама 39053 цистерна 60т СПС",
        "nlu": {
            "route_from": "Biləcəri", "route_to": "Yalama", "cargo_gng_code": "39053", "cargo_name": "Spirt və fenollar",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 29.59
    },
    {
        "name": "10. Сумгаит -> Ялама (2202, цистерна, 60т, МПС)",
        "raw_text": "Сумгаит Ялама 2202 цистерна 60т МПС",
        "nlu": {
            "route_from": "Sumqayıt", "route_to": "Yalama", "cargo_gng_code": "2202", "cargo_name": "Tez xarab olan maye yüklər",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "MPS", "explicit_mode": "export"
        },
        "expected_rate": 28.15
    },
    {
        "name": "11. Ялама -> Ширван (15071010, цистерна, 50т, СПС)",
        "raw_text": "Ялама Ширван 15071010 цистерна 50т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Şirvan", "cargo_gng_code": "15071010", "cargo_name": "Bitki yağları",
            "actual_weight_tons": 50.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 36.11
    },
    {
        "name": "12. Ялама -> Сиазань (29023, цистерна, 50т, СПС)",
        "raw_text": "Ялама Сиазань 29023 цистерна 50т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Siyəzən", "cargo_gng_code": "29023", "cargo_name": "Özəl çənlər yükləri",
            "actual_weight_tons": 50.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 18.66
    },
    {
        "name": "13. Баку тов -> Ялама (4407, крытый, 50т, СПС)",
        "raw_text": "Баку тов Ялама 4407 крытый 50тн СПС",
        "nlu": {
            "route_from": "Bakı Yük (547105)", "route_to": "Yalama", "cargo_gng_code": "4407", "cargo_name": "Taxta",
            "actual_weight_tons": 50.0, "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 15.38
    },
    {
        "name": "14. Баку тов -> Ялама (Почта, 15т, пассажирский)",
        "raw_text": "Баку тов Ялама 99910000 15тн",
        "nlu": {
            "route_from": "Bakı Yük (547105)", "route_to": "Yalama", "cargo_gng_code": "99910000", "cargo_name": "Poçt",
            "actual_weight_tons": 15.0, "wagon_type": "passenger", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 41.27
    },
    {
        "name": "15. Астара -> Ялама (8-осный транспортер, 15т груза, Транзит)",
        "raw_text": "Астара Ялама 8-осный транспортер 15тн",
        "nlu": {
            "route_from": "Astara", "route_to": "Yalama", "cargo_gng_code": "00000000",
            "actual_weight_tons": 15.0, "wagon_type": "transporter", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 63.38
    },
    {
        "name": "16. Беюк Кясик -> Астара (Спецплатформа сцеп >19м, 40т, Транзит)",
        "raw_text": "Беюк Кясик Астара платформа сцеп 19м 40тн",
        "nlu": {
            "route_from": "Böyük Kəsik", "route_to": "Astara", "cargo_gng_code": "00000000",
            "actual_weight_tons": 40.0, "wagon_type": "platform", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 46.48
    },
    {
        "name": "17. Ялама -> Апшерон (Спецплатформа сцеп >19м, 40т, Импорт)",
        "raw_text": "Ялама Апшерон платформа сцеп 19м 40тн idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "actual_weight_tons": 40.0, "wagon_type": "platform", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 21.96
    },
    {
        "name": "18. Апшерон -> Ялама (8-осный транспортер, 15т груза, Экспорт)",
        "raw_text": "Апшерон Ялама 8-осный транспортер 15тн ixrac",
        "nlu": {
            "route_from": "Abşeron", "route_to": "Yalama", "cargo_gng_code": "00000000",
            "actual_weight_tons": 15.0, "wagon_type": "transporter", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 41.27
    },
    {
        "name": "19. Баладжары -> Ялама (Порожний возврат вагона, 192км, Экспорт)",
        "raw_text": "Баладжары Ялама порожний возврат",
        "nlu": {
            "route_from": "Biləcəri", "route_to": "Yalama", "cargo_gng_code": "99220000",
            "cargo_name": "Yükdən boşaldılmış vaqonlar", "is_empty": True, "axles_count": 4,
            "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 148.74
    },
    {
        "name": "20. Алят -> Беюк Кясик (Порожний возврат вагона, 429км, Транзит)",
        "raw_text": "Алят Беюк Кясик порожний вагон",
        "nlu": {
            "route_from": "Ələt", "route_to": "Böyük Kəsik", "cargo_gng_code": "99220000",
            "cargo_name": "Yükdən boşaldılmış vaqonlar", "is_empty": True, "axles_count": 4,
            "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 265.87
    },
    {
        "name": "21. Ялама -> Апшерон (Автопоезд на спецплатформе, 25т, СПС, Импорт — п. 3.3.1)",
        "raw_text": "Ялама Апшерон avtoqatar 25t SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "actual_weight_tons": 25.0, "wagon_type": "avtoqatar", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 652.65
    },
    {
        "name": "22. Ялама -> Апшерон (Прицеп qoşqu порожний на платформе, СПС, Экспорт — п. 3.3.2)",
        "raw_text": "Ялама Апшерон qoşqu boş SPS ixrac",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "99220000",
            "cargo_name": "Boş qoşqu", "is_empty": True, "wagon_type": "qoşqu", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 450.10
    },
    {
        "name": "23. Ялама -> Сиазань (27071 бензол, цистерна 55т, СПС — п. 3.2.5, мин 151км)",
        "raw_text": "Ялама Сиазань 27071 цистерна 55т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Siyəzən", "cargo_gng_code": "27071", "cargo_name": "Benzol və aromatik karbohidrogenlər",
            "actual_weight_tons": 55.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 18.66
    },
    {
        "name": "24. Ялама -> Сумгаит (35т, 3-я верхняя негабаритность, платформа, СПС — Cədvəl 11)",
        "raw_text": "Ялама Сумгаит 35т 3-yuxarı əndazə platforma SPS",
        "nlu": {
            "route_from": "Yalama", "route_to": "Sumqayıt", "cargo_gng_code": "00000000",
            "cargo_name": "Əndazəsiz yük", "actual_weight_tons": 35.0, "wagon_type": "platform",
            "park_type": "SPS", "oversize_group": "deg3_upper", "explicit_mode": "import"
        },
        "expected_rate": 51.25
    },
    {
        "name": "25. Ялама -> Апшерон (Порожний кузов kuzov на платформе, СПС, Импорт — п. 3.3.2, абз. 2)",
        "raw_text": "Ялама Апшерон kuzov boş SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "99220000",
            "cargo_name": "Boş kuzov", "is_empty": True, "wagon_type": "kuzov", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 450.10
    },
    {
        "name": "26. Ялама -> Апшерон (20-футовый универсальный контейнер гружёный, СПС, Импорт — Cədvəl 8)",
        "raw_text": "Ялама Апшерон 20фут контейнер yüklü SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "wagon_type": "container", "container_size": 20, "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 528.00
    },
    {
        "name": "27. Ялама -> Апшерон (40-футовый универсальный контейнер гружёный, СПС, Импорт — Cədvəl 8)",
        "raw_text": "Ялама Апшерон 40фут контейнер yüklü SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "wagon_type": "container", "container_size": 40, "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 950.74
    },
    {
        "name": "28. Ялама -> Апшерон (20-футовый танк-контейнер гружёный, СПС, Импорт — Cədvəl 10)",
        "raw_text": "Ялама Апшерон 20ft tank контейнер yüklü SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "wagon_type": "tank_container", "container_size": 20, "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 740.21
    },
    # --- РАЗДЕЛ 3.6: ОПАСНЫЕ ГРУЗЫ (Cədvəl 12, 13 & Qoruyucu vaqon) ---
    {
        "name": "29. Ялама → Апшерон (Опасный груз BMT 2927, 35т, СПС, Импорт — Cədvəl 12)",
        "raw_text": "Yalama Abşeron 35t tehlukeli BMT 2927 SPS",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "cargo_name": "Təhlükəli yük BMT 2927", "actual_weight_tons": 35.0,
            "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 5777.96
    },
    {
        "name": "30. Ялама → Апшерон (Цистерна Метанол BMT 1230, 50т, СПС — п. 3.6.1 Исключение)",
        "raw_text": "Yalama Abşeron cistern metanol BMT 1230 50t SPS",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "290511",
            "cargo_name": "Metanol", "actual_weight_tons": 50.0,
            "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 634.92
    },
    {
        "name": "31. Ялама → Апшерон (Вагон прикрытия, 4 оси, СПС — п. 3.6.3)",
        "raw_text": "Yalama Abşeron qoruyucu vaqon 4 ox SPS",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "99220000",
            "cargo_name": "Qoruyucu vaqon", "is_empty": True, "axles_count": 4,
            "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 474.13
    }
]

def parse_float(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    match = re.search(r'[-+]?\d*\.\d+|\d+', str(val).replace(',', '.'))
    if match:
        return float(match.group(0))
    return 0.0

def run_tests():
    print(f"🧪 ПРОВЕРКА {len(TEST_SUITE)} ОСНОВНЫХ И ДОПОЛНИТЕЛЬНЫХ МАРШРУТОВ...\n" + "="*60)
    passed, failed = 0, 0

    for test in TEST_SUITE:
        try:
            res = process_full_calculation(test["nlu"], test["raw_text"], "AZ", "2026", UI_T)
            
            raw_rate = res['part3'].get('express_rate') or res['part3'].get('net_ady_rate')
            calc_rate = parse_float(raw_rate)
            exp_rate = test["expected_rate"]

            if abs(calc_rate - exp_rate) <= 0.05:
                print(f"✅ {test['name']} -> Совпало: {calc_rate}$")
                passed += 1
            else:
                print(f"❌ {test['name']} -> Ошибка! Должно быть {exp_rate}$, а калькулятор выдал {calc_rate}$")
                failed += 1
        except Exception as e:
            print(f"❌ {test['name']} -> Ошибка кода: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"📊 ИТОГ: Успешно: {passed} | Ошибок: {failed}")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()

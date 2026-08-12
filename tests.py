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
        "expected_rate": 26.66
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
        "expected_rate": 31.27
    },
    {
        "name": "15. Баладжары -> Сумгаит (10т, универсальный вагон, 35 км)",
        "raw_text": "Баладжары Сумгаит 10тн",
        "nlu": {
            "route_from": "Biləcəri", "route_to": "Sumqayıt", "cargo_gng_code": "00000000",
            "actual_weight_tons": 10.0, "wagon_type": "universal", "park_type": "MPS", "explicit_mode": "local"
        },
        "expected_rate": 9.37
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
            res = process_full_calculation(test["nlu"], "", "AZ", "2026", UI_T)
            
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

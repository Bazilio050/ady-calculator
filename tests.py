import sys
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

# 4 ТВОИХ ПРОВЕРОЧНЫХ МАРШРУТА
TEST_SUITE = [
    {
        "name": "1. Ялама -> Апшерон (4407, 35т, крытый, СПС)",
        "raw_text": "Ялама Апшерон 4407 35т крытый СПС",
        "nlu": {
            "route_from": "Yalama",
            "route_to": "Abşeron",
            "cargo_gng_code": "4407",
            "cargo_name": "Taxta",
            "actual_weight_tons": 35.0,
            "wagon_type": "universal",
            "park_type": "SPS",
            "explicit_mode": "import"
        },
        "expected_rate": 17.26
    },
    {
        "name": "2. Ялама -> Баладжары (0207, реф 5+1, 35т, СПС)",
        "raw_text": "Ялама - Баладжары 0207 рефвагон 5+1 35т СПС",
        "nlu": {
            "route_from": "Yalama",
            "route_to": "Biləcəri",
            "cargo_gng_code": "0207",
            "cargo_name": "Ət və ət məhsulları",
            "actual_weight_tons": 35.0,
            "wagon_type": "ref",
            "park_type": "SPS",
            "ref_section_cargo_wagons": 5,
            "explicit_mode": "import"
        },
        "expected_rate": 35.08
    },
    {
        "name": "3. Ялама -> Беюк-Кясик (78, крытый, 60т, СПС)",
        "raw_text": "Ялама БеюкКясик 78 крытый 60т СПС",
        "nlu": {
            "route_from": "Yalama",
            "route_to": "Böyük Kəsik",
            "cargo_gng_code": "0078",
            "cargo_name": "Aşırılan yük",
            "actual_weight_tons": 60.0,
            "wagon_type": "universal",
            "park_type": "SPS",
            "explicit_mode": "transit"
        },
        "expected_rate": 38.14
    },
    {
        "name": "4. Баку-тов -> Ялама (2713, цистерна, 60т, СПС)",
        "raw_text": "Баку-тов Ялама 2713 цистерна 60тн СПС",
        "nlu": {
            "route_from": "Bakı-Yük",
            "route_to": "Yalama",
            "cargo_gng_code": "2713",
            "cargo_name": "Neft məhsulları",
            "actual_weight_tons": 60.0,
            "wagon_type": "cistern",
            "park_type": "SPS",
            "explicit_mode": "export"
        },
        "expected_rate": 18.84
    }
]

def run_tests():
    print("🧪 ПРОВЕРКА 4 ОСНОВНЫХ МАРШРУТОВ...\n" + "="*50)
    passed, failed = 0, 0

    for test in TEST_SUITE:
        try:
            res = process_full_calculation(test["nlu"], test["raw_text"], "AZ", "2026", UI_T)
            calc_rate = res['part3'].get('express_rate') or res['part3'].get('net_ady_rate')
            exp_rate = test["expected_rate"]

            # Если разница меньше 5 копеек (погрешность округления) — считаем верным
            if abs(calc_rate - exp_rate) <= 0.05:
                print(f"✅ {test['name']} -> Совпало: {calc_rate}$")
                passed += 1
            else:
                print(f"❌ {test['name']} -> Ошибка! Должно быть {exp_rate}$, а калькулятор выдал {calc_rate}$")
                failed += 1
        except Exception as e:
            print(f"❌ {test['name']} -> Ошибка кода: {e}")
            failed += 1

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()

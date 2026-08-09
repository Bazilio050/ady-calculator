import sys
from utils import load_rules_config
from engine import process_full_calculation

def run_tests():
    print("🧪 Запуск тестирования калькулятора AGT Cargo...\n")
    
    # Тестовый пример: Ялама -> Сумгаит (GNG 2815, 65 тонн, SPS, Реф 5+1)
    mock_nlu = {
        "route_from": "Yalama",
        "route_to": "Sumqayıt",
        "cargo_gng_code": "2815",
        "cargo_name": "Qapalı yük",
        "actual_weight_tons": 65.0,
        "wagon_type": "ref",
        "park_type": "SPS",
        "ref_section_cargo_wagons": 5,
        "explicit_mode": "import"
    }
    
    ui_t = {
        "unit_wagon": "USD/vaqon", "unit_ton": "USD/t",
        "type_import": "İdxal daşınması", "type_export": "İxrac daşınması", "type_transit": "Tranzit daşınması",
        "note_sps": "SPS güzəşt 0.85", "note_import": "Min 151 km", "note_export": "Min 101 km",
        "note_import_base_150": "Import/Export 1.50", "note_express": "Express +2%",
        "note_timber_metal": "Timber/Metal 1.04", "note_ref_transit_120": "Ref transit 1.20",
        "note_coef_1015": "Add coeff 1.015", "note_min_weight": "Min weight"
    }

    try:
        res = process_full_calculation(mock_nlu, "Ялама sumqait 2815 qapali 65t sps", "AZ", "2026", ui_t)
        print("✅ УСПЕШНО! Модульная структура работает корректно.")
        print(f"📍 Маршрут: {res['part1']['route']}")
        print(f"💰 Итоговая ставка: {res['part3']['net_ady_rate']}")
        print(f"🚀 С услугой Express (+2%): {res['part3']['express_rate']}")
    except Exception as e:
        print(f"❌ ОШИБКА в тесте: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()

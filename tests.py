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
        "expected_rate": 17.26, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "2. Ялама -> Баладжары (0207, реф 5+1, 35т, СПС)",
        "raw_text": "Ялама - Баладжары 0207 рефвагон 5+1 35т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Biləcəri", "cargo_gng_code": "0207", "cargo_name": "Ət və ət məhsulları",
            "actual_weight_tons": 35.0, "wagon_type": "ref", "park_type": "SPS", "ref_section_cargo_wagons": 5, "explicit_mode": "import"
        },
        "expected_rate": 33.53, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "3. Ялама -> Беюк-Кясик (78, крытый, 60т, СПС)",
        "raw_text": "Ялама БеюкКясик 78 крытый 60т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Böyük Kəsik", "cargo_gng_code": "0078", "cargo_name": "Aşırılan yük",
            "actual_weight_tons": 60.0, "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 38.14, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "4. Баку тов -> Ялама (2713, цистерна, 60т, СПС)",
        "raw_text": "Баку тов Ялама 2713 цистерна 60тн СПС",
        "nlu": {
            "route_from": "Bakı Yük (547105)", "route_to": "Yalama", "cargo_gng_code": "2713", "cargo_name": "Neft məhsulları",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 18.84, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "5. Ялама -> Гюздек (3404, цистерна, 60т, СПС)",
        "raw_text": "Ялама Гюздек 3404 цистерна 60т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Güzdək", "cargo_gng_code": "3404", "cargo_name": "Neft məhsulları",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 16.80, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "6. Ялама -> Гюздек (3404, цистерна, 60т, МПС)",
        "raw_text": "Ялама Гюздек 3404 цистерна 60т МПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Güzdək", "cargo_gng_code": "3404", "cargo_name": "Neft məhsulları",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "MPS", "explicit_mode": "import"
        },
        "expected_rate": 19.76, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "7. Г.Тагиев -> Беюк Кясик (2705, цистерна, 60т, СПС)",
        "raw_text": "Г.Тагиев Беюк Кясик 2705 цистерна 60т СПС",
        "nlu": {
            "route_from": "Z.Tağıyev, "route_to": "Böyük Kəsik", "cargo_gng_code": "2705", "cargo_name": "Enerjili qazlar",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 40.84, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "8. Г.Тагиев -> Ялама (28042, цистерна, 50т, СПС)",
        "raw_text": "Г.Тагиев Ялама 28042 цистерна 50т СПС",
        "nlu": {
            "route_from": "Z.Tağıyev", "route_to": "Yalama", "cargo_gng_code": "28042", "cargo_name": "Qazlar və karbohidrogenlər",
            "actual_weight_tons": 50.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 58.35, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "9. Баладжары -> Ялама (39053, цистерна, 60т, СПС)",
        "raw_text": "Баладжары Ялама 39053 цистерна 60т СПС",
        "nlu": {
            "route_from": "Biləcəri", "route_to": "Yalama", "cargo_gng_code": "39053", "cargo_name": "Spirt və fenollar",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 29.59, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "10. Сумгаит -> Ялама (2202, цистерна, 60т, МПС)",
        "raw_text": "Сумгаит Ялама 2202 цистерна 60т МПС",
        "nlu": {
            "route_from": "Sumqayıt", "route_to": "Yalama", "cargo_gng_code": "2202", "cargo_name": "Tez xarab olan maye yüklər",
            "actual_weight_tons": 60.0, "wagon_type": "cistern", "park_type": "MPS", "explicit_mode": "export"
        },
        "expected_rate": 28.15, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "11. Ялама -> Ширван (15071010, цистерна, 50т, СПС)",
        "raw_text": "Ялама Ширван 15071010 цистерна 50т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Şirvan", "cargo_gng_code": "15071010", "cargo_name": "Bitki yağları",
            "actual_weight_tons": 50.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 36.11, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "12. Ялама -> Сиазань (29023, цистерна, 50т, СПС)",
        "raw_text": "Ялама Сиазань 29023 цистерна 50т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Siyəzən", "cargo_gng_code": "29023", "cargo_name": "Özəl çənlər yükləri",
            "actual_weight_tons": 50.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 18.66, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "13. Баку тов -> Ялама (4407, крытый, 50т, СПС)",
        "raw_text": "Баку тов Ялама 4407 крытый 50тн СПС",
        "nlu": {
            "route_from": "Bakı Yük (547105)", "route_to": "Yalama", "cargo_gng_code": "4407", "cargo_name": "Taxta",
            "actual_weight_tons": 50.0, "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 15.38, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "14. Баку тов -> Ялама (Почта, 15т, пассажирский)",
        "raw_text": "Баку тов Ялама 99910000 15тн",
        "nlu": {
            "route_from": "Bakı Yük (547105)", "route_to": "Yalama", "cargo_gng_code": "99910000", "cargo_name": "Poçt",
            "actual_weight_tons": 15.0, "wagon_type": "passenger", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 41.27, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "15. Астара -> Ялама (8-осный транспортер, 15т груза, Транзит)",
        "raw_text": "Астара Ялама 8-осный транспортер 15тн",
        "nlu": {
            "route_from": "Astara", "route_to": "Yalama", "cargo_gng_code": "00000000",
            "actual_weight_tons": 15.0, "wagon_type": "transporter", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 63.38, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "16. Беюк Кясик -> Астара (Спецплатформа сцеп >19м, 40т, Транзит)",
        "raw_text": "Беюк Кясик Астара платформа сцеп 19м 40тн",
        "nlu": {
            "route_from": "Böyük Kəsik", "route_to": "Astara", "cargo_gng_code": "00000000",
            "actual_weight_tons": 40.0, "wagon_type": "platform", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 46.48, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "17. Ялама -> Апшерон (Спецплатформа сцеп >19м, 40т, Импорт)",
        "raw_text": "Ялама Апшерон платформа сцеп 19м 40тн idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "actual_weight_tons": 40.0, "wagon_type": "platform", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 21.96, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "18. Апшерон -> Ялама (8-осный транспортер, 15т груза, Экспорт)",
        "raw_text": "Апшерон Ялама 8-осный транспортер 15тн ixrac",
        "nlu": {
            "route_from": "Abşeron", "route_to": "Yalama", "cargo_gng_code": "00000000",
            "actual_weight_tons": 15.0, "wagon_type": "transporter", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 41.27, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "19. Баладжары -> Ялама (Порожний возврат вагона, 192км, Экспорт)",
        "raw_text": "Баладжары Ялама порожний возврат",
        "nlu": {
            "route_from": "Biləcəri", "route_to": "Yalama", "cargo_gng_code": "99220000",
            "cargo_name": "Yükdən boşaldılmış vaqonlar", "is_empty": True, "axles_count": 4,
            "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 148.74, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "20. Алят-эксп -> Беюк Кясик (Порожний возврат вагона, 429км, Транзит)",
        "raw_text": "Алят-эксп Беюк Кясик порожний вагон",
        "nlu": {
            "route_from": "Ələt-eksp", "route_to": "Böyük Kəsik", "cargo_gng_code": "99220000",
            "cargo_name": "Yükdən boşaldılmış vaqonlar", "is_empty": True, "axles_count": 4,
            "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 265.87, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "21. Ялама -> Апшерон (Автопоезд на спецплатформе, 25т, СПС, Импорт — п. 3.3.1)",
        "raw_text": "Ялама Апшерон avtoqatar 25t SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "actual_weight_tons": 25.0, "wagon_type": "avtoqatar", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 652.65, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "22. Ялама -> Апшерон (Прицеп qoşqu порожний на платформе, СПС, Экспорт — п. 3.3.2)",
        "raw_text": "Ялама Апшерон qoşqu boş SPS ixrac",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "99220000",
            "cargo_name": "Boş qoşqu", "is_empty": True, "wagon_type": "qoşqu", "park_type": "SPS", "explicit_mode": "export"
        },
        "expected_rate": 450.10, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "23. Ялама -> Сиазань (27071 бензол, цистерна 55т, СПС — п. 3.2.5, мин 151км)",
        "raw_text": "Ялама Сиазань 27071 цистерна 55т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Siyəzən", "cargo_gng_code": "27071", "cargo_name": "Benzol və aromatik karbohidrogenlər",
            "actual_weight_tons": 55.0, "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 18.66, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "24. Ялама -> Сумгаит (35т, 3-я верхняя негабаритность, платформа, СПС — Cədvəl 11)",
        "raw_text": "Ялама Сумгаит 35т 3-yuxarı əndazə platforma SPS",
        "nlu": {
            "route_from": "Yalama", "route_to": "Sumqayıt", "cargo_gng_code": "00000000",
            "cargo_name": "Əndazəsiz yük", "actual_weight_tons": 35.0, "wagon_type": "platform",
            "park_type": "SPS", "oversize_group": "deg3_upper", "explicit_mode": "import"
        },
        "expected_rate": 51.25, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "25. Ялама -> Апшерон (Порожний кузов kuzov на платформе, СПС, Импорт — п. 3.3.2, абз. 2)",
        "raw_text": "Ялама Апшерон kuzov boş SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "99220000",
            "cargo_name": "Boş kuzov", "is_empty": True, "wagon_type": "kuzov", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 450.10, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "26. Ялама -> Апшерон (20-футовый универсальный контейнер гружёный, СПС, Импорт — Cədvəl 8)",
        "raw_text": "Ялама Апшерон 20фут контейнер yüklü SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "wagon_type": "container", "container_size": 20, "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 528.00, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "27. Ялама -> Апшерон (40-футовый универсальный контейнер гружёный, СПС, Импорт — Cədvəl 8)",
        "raw_text": "Ялама Апшерон 40фут контейнер yüklü SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "wagon_type": "container", "container_size": 40, "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 950.74, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "28. Ялама -> Апшерон (20-футовый танк-контейнер гружёный, СПС, Импорт — Cədvəl 10)",
        "raw_text": "Ялама Апшерон 20ft tank контейнер yüklü SPS idxal",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "wagon_type": "tank_container", "container_size": 20, "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 740.21, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "29. Ялама → Апшерон (Опасный груз BMT 2927, 35т, СПС, Импорт — Cədvəl 12)",
        "raw_text": "Yalama Abşeron 35t tehlukeli BMT 2927 SPS",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "00000000",
            "cargo_name": "Təhlükəli yük BMT 2927", "actual_weight_tons": 35.0,
            "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 5777.96, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "30. Ялама → Апшерон (Цистерна Метанол BMT 1230, 50т, СПС — п. 3.6.1 Исключение)",
        "raw_text": "Yalama Abşeron cistern metanol BMT 1230 50t SPS",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "290511",
            "cargo_name": "Metanol", "actual_weight_tons": 50.0,
            "wagon_type": "cistern", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 20.64, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "31. Ялама → Апшерон (Вагон прикрытия, 4 оси, СПС — п. 3.6.3)",
        "raw_text": "Yalama Abşeron qoruyucu vaqon 4 ox SPS",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "99220000",
            "cargo_name": "Qoruyucu vaqon", "is_empty": True, "axles_count": 4,
            "wagon_type": "universal", "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 474.13, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "32. Ялама -> Беюк Кясик (Локомотив 8601 на своих осях, 45т, СПС — п. 3.7.1)",
        "raw_text": "Ялама Беюк Кясик 680км локомотив 8601 на своих осях 45т СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Böyük Kəsik", "cargo_gng_code": "86010000",
            "cargo_name": "Lokomotiv", "actual_weight_tons": 45.0, "wagon_type": "universal",
            "park_type": "SPS", "is_own_axles": True, "explicit_mode": "transit"
        },
        "expected_rate": 19.65, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "33. Ялама -> Апшерон (Порожний вагон МПС в ремонт, 4 оси, 204км — п. 3.7.2)",
        "raw_text": "Ялама Апшерон 204км крытый вагон в ремонт МПС 4 оси",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "99220000",
            "cargo_name": "Boş vaqon", "is_empty": True, "axles_count": 4, "wagon_type": "universal",
            "park_type": "MPS", "is_own_axles": True, "is_in_repair": True, "explicit_mode": "import"
        },
        "expected_rate": 105.36, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "34. Астара -> Ялама (Перегонка порожнего 8-осного транспортера, 504км — п. 3.7.8)",
        "raw_text": "Астара Ялама 504км порожний 8-осный транспортер",
        "nlu": {
            "route_from": "Astara", "route_to": "Yalama", "cargo_gng_code": "99220000",
            "cargo_name": "Boş transportyor", "is_empty": True, "axles_count": 8,
            "wagon_type": "transporter", "park_type": "SPS", "explicit_mode": "transit"
        },
        "expected_rate": 1197.35, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "35. Ялама -> Апшерон (Сборный груз yığma göndərmə 6т -> норма 10т, СПС — п. 3.8)",
        "raw_text": "Ялама Апшерон yığma göndərmə 6t СПС",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron", "cargo_gng_code": "72010000",
            "cargo_name": "Qara metallar", "actual_weight_tons": 6.0, "wagon_type": "universal",
            "park_type": "SPS", "is_consolidated": True, "explicit_mode": "import"
        },
        "expected_rate": 38.60, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "36. Ялама -> Апшерон (Проезд 2 проводников, 204км, Импорт — п. 3.9)",
        "raw_text": "Yalama Abşeron 2 bələdçi idxal 204km",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron",
            "escort_count": 2, "explicit_mode": "import"
        },
        "expected_rate": 139.44, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "37. Ялама -> Апшерон (Теплушка СПС грузовая, 4 оси, 204км, Импорт — п. 3.9)",
        "raw_text": "Yalama Abşeron tepluşka SPS 4 ox idxal 204km",
        "nlu": {
            "route_from": "Yalama", "route_to": "Abşeron",
            "has_teplushka": True, "teplushka_type": "freight_sps", "axles_count": 4,
            "park_type": "SPS", "explicit_mode": "import"
        },
        "expected_rate": 316.07, "expected_guard": 0.00, "expected_ferry": 0.00
    },
    {
        "name": "38. Курык -> Астара (2304, хоппер, 40т, СПС, 17м, Паром)",
        "raw_text": "Курык Астара 2304 хопер 40т спс 17м",
        "nlu": {
            "route_from": "Ələt eksport-Kurik", "route_to": "Astara", "cargo_gng_code": "2304",
            "cargo_name": "Jmyx / Şrot", "actual_weight_tons": 40.0, "wagon_type": "universal",
            "park_type": "SPS", "wagon_length_m": 17.0, "is_asco_ferry": True, "explicit_mode": "transit"
        },
        "expected_rate": 21.21, "expected_guard": 0.00, "expected_ferry": 1105.00
    },
    {
        "name": "39. Ялама -> Алят-эксп (72, полувагон, 50т, СПС, Транзит)",
        "raw_text": "Ялама Алят-эксп 72 полувагон 50т спс",
        "nlu": {
            "route_from": "Yalama", 
            "route_to": "Ələt-eksp", 
            "origin_esr": "547508",
            "dest_esr": "553002",
            "cargo_gng_code": "72000000",
            "cargo_name": "Qara metallar", 
            "actual_weight_tons": 50.0, 
            "wagon_type": "universal",
            "park_type": "SPS", 
            "is_asco_ferry": False, 
            "explicit_mode": "transit"
        },
        "expected_rate": 16.40, 
        "expected_guard": 16.26, 
        "expected_ferry": 0.00
    },
    {
        "name": "40. Беюк Кясик -> ТРК (0207, рефвагон 5+1, 43т, МПС, 22м, Паром)",
        "raw_text": "Беюк Кясик ТРК 0207 рефвагон 5+1 43т мпс 22м",
        "nlu": {
            "route_from": "Böyük Kəsik", "route_to": "Ələt eksport-Türk.", "cargo_gng_code": "0207",
            "cargo_name": "Ət məhsulları", "actual_weight_tons": 43.0, "wagon_type": "ref",
            "park_type": "MPS", "ref_section_cargo_wagons": 5, "wagon_length_m": 22.0,
            "is_asco_ferry": True, "explicit_mode": "transit"
        },
        "expected_rate": 65.15, "expected_guard": 0.00, "expected_ferry": 1430.00
    },
    {
        "name": "41. ТРК -> Беюк Кясик (2713, цистерна, 50т, СПС, 13м, Паром)",
        "raw_text": "ТРК Беюк Кясик 2713 цистерна 50т спс 13м",
        "nlu": {
            "route_from": "Ələt eksport-Türk.", "route_to": "Böyük Kəsik", "cargo_gng_code": "2713",
            "cargo_name": "Neft məhsulları", "actual_weight_tons": 50.0, "wagon_type": "cistern",
            "park_type": "SPS", "wagon_length_m": 13.0, "is_asco_ferry": True, "explicit_mode": "transit"
        },
        "expected_rate": 23.79, "expected_guard": 25.74, "expected_ferry": 650.00
    },
    {
        "name": "42. Курык -> Баладжары (1001, хоппер, 55т, СПС, 15м, Паром)",
        "raw_text": "курык баладжары 1001 хопер 55т спс 15м",
        "nlu": {
            "route_from": "Ələt eksport-Kurik", "route_to": "Biləcəri", "cargo_gng_code": "1001",
            "cargo_name": "Buğda", "actual_weight_tons": 55.0, "wagon_type": "universal",
            "park_type": "SPS", "wagon_length_m": 15.0, "is_asco_ferry": True, "explicit_mode": "import"
        },
        "expected_rate": 10.69, "expected_guard": 0.00, "expected_ferry": 750.00
    },
    {
        "name": "43. ТРК -> Беюк Кясик (2705, цистерна, 50т, МПС, 13м, Паром)",
        "raw_text": "ТРК Беюк кясик 2705 цистерна 50т МПС 13м",
        "nlu": {
            "route_from": "Ələt eksport-Türk.", "route_to": "Böyük Kəsik", "cargo_gng_code": "2705",
            "cargo_name": "Qazlar", "actual_weight_tons": 50.0, "wagon_type": "cistern",
            "park_type": "MPS", "wagon_length_m": 13.0, "is_asco_ferry": True, "explicit_mode": "transit"
        },
        "expected_rate": 57.42, "expected_guard": 25.74, "expected_ferry": 650.00
    },
    {
        "name": "44. Курык -> Беюк Кясик (28141, цистерна, 50т, СПС, 13м, Паром)",
        "raw_text": "Курык Беюк кясик 28141 цистерна 50т СПС 13м",
        "nlu": {
            "route_from": "Ələt eksport-Kurik", "route_to": "Böyük Kəsik", "cargo_gng_code": "28141",
            "cargo_name": "Ammiak", "actual_weight_tons": 50.0, "wagon_type": "cistern",
            "park_type": "SPS", "wagon_length_m": 13.0, "is_asco_ferry": True, "explicit_mode": "transit"
        },
        "expected_rate": 65.15, "expected_guard": 25.74, "expected_ferry": 650.00
    },
    {
        "name": "45. Беюк Кясик -> Курык (Порожний вагон, 15м, Паром)",
        "raw_text": "БеюкКясик Курык порожний вагон 15м",
        "nlu": {
            "route_from": "Böyük Kəsik", "route_to": "Ələt eksport-Kurik", "cargo_gng_code": "99220000",
            "cargo_name": "Boş vaqon", "is_empty": True, "axles_count": 4, "wagon_type": "universal",
            "park_type": "SPS", "wagon_length_m": 15.0, "is_asco_ferry": True, "explicit_mode": "transit"
        },
        "expected_rate": 263.39, "expected_guard": 0.00, "expected_ferry": 750.00
    },
    {
        "name": "46. Беюк Кясик -> ТРК (1701, платформа, 50т, СПС, Паром)",
        "raw_text": "Беюк Кясик ТРК 1701 платформа 50т спс",
        "nlu": {
            "route_from": "Böyük Kəsik", "route_to": "Ələt eksport-Türk.", "cargo_gng_code": "1701",
            "cargo_name": "Qənd və şəkər", "actual_weight_tons": 50.0, "wagon_type": "platform",
            "park_type": "SPS", "wagon_length_m": 15.0, "is_asco_ferry": True, "explicit_mode": "transit"
        },
        "expected_rate": 28.71, "expected_guard": 25.50, "expected_ferry": 750.00
    },
    {
        "name": "47. Сальяны -> Алят (2304, крытый, 60т, СПС)",
        "raw_text": "Сальяны Алят 2304 крытый 60т СПС",
        "nlu": {
            "route_from": "Salyan", 
            "route_to": "Ələt", 
            "origin_esr": "548907",        # Сухопутный ESR станции Сальяны
            "dest_esr": "548502",          # Сухопутный ESR станции Алят
            "cargo_gng_code": "2304",
            "cargo_name": "Jmyx / Şrot", 
            "actual_weight_tons": 60.0, 
            "wagon_type": "universal",
            "park_type": "SPS", 
            "is_asco_ferry": False, 
            "explicit_mode": "import"
        },
        "expected_rate": 10.69,
        "expected_guard": 0.00,
        "expected_ferry": 0.00
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
    print(f"🧪 ПРОВЕРКА {len(TEST_SUITE)} ТЕСТОВЫХ СЦЕНАРИЕВ (ТАРИФ + ОХРАНА + ПАРОМ)...\n" + "="*70)
    passed, failed = 0, 0

    for test in TEST_SUITE:
        try:
            res = process_full_calculation(test["nlu"], test["raw_text"], "AZ", "2026", UI_T)
            
            # 1. Извлечение Тарифа (экспресс или базовый net_ady)
            raw_rate = res['part3'].get('express_rate') or res['part3'].get('net_ady_rate')
            calc_rate = parse_float(raw_rate)
            exp_rate = test["expected_rate"]

            # 2. Извлечение Охраны
            calc_guard = parse_float(res['part3'].get('guard_cost') or res['part3'].get('guard_rate'))
            exp_guard = test.get("expected_guard", 0.00)

            # 3. Извлечение Паромного Фрахта
            ferry_obj = res['part3'].get('asco_ferry') or {}
            calc_ferry = parse_float(ferry_obj.get('total_usd') if isinstance(ferry_obj, dict) else ferry_obj)
            exp_ferry = test.get("expected_ferry", 0.00)

            # Режим первичного автоопределения для новых тестов с expected_rate == 0.0
            if exp_rate == 0.0:
                print(f"ℹ️ {test['name']} -> Рассчитано: Тариф: {calc_rate}$ | Охрана: {calc_guard}$ | Паром: {calc_ferry}$ (Внесите в expected_rate после проверки)")
                passed += 1
                continue

            # Тройная проверка
            rate_ok = abs(calc_rate - exp_rate) <= 0.05
            guard_ok = abs(calc_guard - exp_guard) <= 0.05
            ferry_ok = abs(calc_ferry - exp_ferry) <= 0.05

            if rate_ok and guard_ok and ferry_ok:
                details = f"Тариф: {calc_rate}$"
                if exp_guard > 0: details += f" | Охрана: {calc_guard}$"
                if exp_ferry > 0: details += f" | Паром: {calc_ferry}$"
                print(f"✅ {test['name']} -> Совпало ({details})")
                passed += 1
            else:
                errors = []
                if not rate_ok: errors.append(f"Тариф {calc_rate}$ вместо {exp_rate}$")
                if not guard_ok: errors.append(f"Охрана {calc_guard}$ вместо {exp_guard}$")
                if not ferry_ok: errors.append(f"Паром {calc_ferry}$ вместо {exp_ferry}$")
                
                print(f"❌ {test['name']} -> Ошибка! " + ", ".join(errors))
                failed += 1

        except Exception as e:
            print(f"❌ {test['name']} -> Ошибка кода: {e}")
            failed += 1

    print("\n" + "="*70)
    print(f"📊 ИТОГ: Успешно: {passed} | Ошибок: {failed}")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()

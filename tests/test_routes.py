from core.router import RailwayRouter, ShipmentType


def run_all_route_tests():
    router = RailwayRouter(distances_file_path="data/Distances.txt")

    test_cases = [
        # 1. Запросы с портом Алят
        ("Алят экс", "Сальяны", ShipmentType.IMPORT, "553002", "554007"),
        ("Астара", "ТРК", ShipmentType.TRANSIT, "554109", "548803"),
        ("Absheron", "Alat Aqtau", ShipmentType.EXPORT, "552103", "549204"),
        ("Алят", "Сумгаит", ShipmentType.LOCAL, "548502", "550000"),

        # 2. Чистые транзитные запросы без суффиксов (RU, AZ, EN)
        ("Ялама", "Беюк Кясик", ShipmentType.TRANSIT, "545006", "558631"),
        ("Yalama", "Böyük Kəsik", ShipmentType.TRANSIT, "545006", "558631"),
        ("Yalama", "Boyuk Kesik", ShipmentType.TRANSIT, "545006", "558631"),

        # 3. Импортные / Экспортные маршруты на разных языках
        ("Ялама", "Апшерон", ShipmentType.IMPORT, "545006", "552103"),
        ("Беюк Кясик", "Алят", ShipmentType.IMPORT, "558631", "548502"),
        ("Апшерон", "Ялама", ShipmentType.EXPORT, "552103", "545006"),
        ("Şirvan", "Boyuk Kesik", ShipmentType.EXPORT, "553505", "558631")
    ]

    print("\n--- РЕЗУЛЬТАТЫ ПРОВЕРКИ МАРШРУТОВ ADY ---")
    for raw_from, raw_to, expected_type, exp_from_code, exp_to_code in test_cases:
        res = router.calculate_route(raw_from, raw_to)
        out_str = res.formatted_output()
        print(f"Запрос: [{raw_from} -> {raw_to}] ===> {out_str}")

        assert res.shipment_type == expected_type, f"Ошибка типа для {raw_from}->{raw_to}: ожидалось {expected_type}, получено {res.shipment_type}"
        assert res.from_station.code == exp_from_code, f"Неверный код отправления для {raw_from}: {res.from_station.code} != {exp_from_code}"
        assert res.to_station.code == exp_to_code, f"Неверный код назначения для {raw_to}: {res.to_station.code} != {exp_to_code}"

    print("------------------------------------------")
    print("SUCCESS: Все мультиязычные тесты пройдены успешно!\n")


if __name__ == "__main__":
    run_all_route_tests()

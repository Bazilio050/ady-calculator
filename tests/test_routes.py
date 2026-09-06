from core.router import RailwayRouter, ShipmentType


def test_visual_routing():
    router = RailwayRouter(distances_file_path="data/distances.csv")

    test_cases = [
        ("Ялама", "Апшерон", ShipmentType.IMPORT),
        ("Ялама", "Беюк Кясик", ShipmentType.TRANSIT),
        ("Беюк Кясик", "Алят", ShipmentType.IMPORT),
        ("Алят экс", "Сальяны", ShipmentType.IMPORT),
        ("Астара", "ТРК", ShipmentType.TRANSIT),
        ("Yalama", "Boyuk Kesik", ShipmentType.TRANSIT),
        ("Апшерон", "Ялама", ShipmentType.EXPORT),
        ("Курык", "Баладжары", ShipmentType.IMPORT),
        ("Хырдалан", "Курык", ShipmentType.EXPORT),
        ("Курык", "Беюк Кясик", ShipmentType.TRANSIT),
        ("Гянджа", "Беюк Кясик", ShipmentType.EXPORT),
        ("Астара", "Имишли", ShipmentType.IMPORT),
        ("Казах", "Астара", ShipmentType.EXPORT),
        ("Алят експ", "Ялама", ShipmentType.TRANSIT),
        ("Гюздек", "Алят експ", ShipmentType.EXPORT),
        ("ТРК", "Баладжары", ShipmentType.IMPORT),
        ("Хырдалан", "ТРК", ShipmentType.EXPORT),
    ]

    print("\n" + "=" * 80)
    print("      ПРОВЕРКА ЕСТЕСТВЕННЫХ ЗАПРОСОВ, РЕЖИМОВ И ЕСР-КОДОВ ADY")
    print("=" * 80)

    for idx, (raw_from, raw_to, expected_type) in enumerate(test_cases, 1):
        try:
            res = router.calculate_route(raw_from, raw_to)
            is_correct = (res.shipment_type == expected_type)
            status = "✅" if is_correct else "❌"

            print(f"\n{idx}. Запрос: {raw_from} -> {raw_to} {status}")
            print(f"   AZ: {res.formatted_output('AZ')}")
            print(f"   RU: {res.formatted_output('RU')}")
            print(f"   EN: {res.formatted_output('EN')}")

        except Exception as e:
            print(f"\n{idx}. Запрос: {raw_from} -> {raw_to}")
            print(f"   Ошибка: ({e}) ❌")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    test_visual_routing()

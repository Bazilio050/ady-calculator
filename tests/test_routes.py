# ------------------------------------------------------------------------------
# БЛОК 1: Автономный запуск проверки 7 маршрутов ADY
# ------------------------------------------------------------------------------
from core.router import RailwayRouter, ShipmentType


def run_all_route_tests():
    router = RailwayRouter(distances_file_path="data/Distances.txt")

    # 1. Ялама -> Беюк Кясик (Транзит)
    r1 = router.calculate_route("Ялама экспорт", "Беюк-Кясик-эксп.")
    assert r1.shipment_type == ShipmentType.TRANSIT, f"Ожидался TRANSIT, получено {r1.shipment_type}"

    # 2. Беюк Кясик -> Алят (Импорт)
    r2 = router.calculate_route("Беюк-Кясик-эксп.", "Алят")
    assert r2.shipment_type == ShipmentType.IMPORT, f"Ожидался IMPORT, получено {r2.shipment_type}"

    # 3. Астара -> Апшерон (Импорт)
    r3 = router.calculate_route("Астара (эксп.перевалка)", "Апшерон")
    assert r3.shipment_type == ShipmentType.IMPORT, f"Ожидался IMPORT, получено {r3.shipment_type}"

    # 4. Ялама -> Баладжары (Импорт)
    r4 = router.calculate_route("Ялама экспорт", "Баладжары")
    assert r4.shipment_type == ShipmentType.IMPORT, f"Ожидался IMPORT, получено {r4.shipment_type}"

    # 5. Сумгаит -> Алят (Локальная)
    r5 = router.calculate_route("Сумгаит", "Алят")
    assert r5.shipment_type == ShipmentType.LOCAL, f"Ожидался LOCAL, получено {r5.shipment_type}"

    # 6. Ширван -> Ялама (Экспорт)
    r6 = router.calculate_route("Ширван", "Ялама экспорт")
    assert r6.shipment_type == ShipmentType.EXPORT, f"Ожидался EXPORT, получено {r6.shipment_type}"

    # 7. Апшерон -> Беюк Кясик (Экспорт)
    r7 = router.calculate_route("Апшерон", "Беюк-Кясик-эксп.")
    assert r7.shipment_type == ShipmentType.EXPORT, f"Ожидался EXPORT, получено {r7.shipment_type}"

    print("SUCCESS: Все 7 маршрутов успешно прошли проверку!")


if __name__ == "__main__":
    run_all_route_tests()

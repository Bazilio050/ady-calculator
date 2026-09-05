# ------------------------------------------------------------------------------
# БЛОК 1: Модульный тест полного набора целевых маршрутов ADY
# ------------------------------------------------------------------------------
import pytest
from core.router import RailwayRouter, ShipmentType


@pytest.fixture
def router():
    return RailwayRouter(distances_file_path="data/Distances.txt")


def test_yalama_to_boyuk_kasik_transit(router):
    # 1. Ялама -> Беюк Кясик (Транзит)
    result = router.calculate_route("Ялама экспорт", "Беюк-Кясик-эксп.")
    assert result.from_station.canonical_name == "Yalama (eksport)"
    assert result.to_station.canonical_name == "Böyük Kəsik (eksport)"
    assert result.shipment_type == ShipmentType.TRANSIT


def test_boyuk_kasik_to_alat_import(router):
    # 2. Беюк Кясик -> Алят (Импорт)
    result = router.calculate_route("Беюк-Кясик-эксп.", "Алят")
    assert result.from_station.canonical_name == "Böyük Kəsik (eksport)"
    assert result.to_station.canonical_name == "Ələt"
    assert result.shipment_type == ShipmentType.IMPORT


def test_astara_to_absheron_import(router):
    # 3. Астара -> Апшерон (Импорт)
    result = router.calculate_route("Астара (эксп.перевалка)", "Апшерон")
    assert result.from_station.canonical_name == "Astara (eks.aşır)"
    assert result.to_station.canonical_name == "Abşeron"
    assert result.shipment_type == ShipmentType.IMPORT


def test_yalama_to_bilajari_import(router):
    # 4. Ялама -> Баладжары (Импорт)
    result = router.calculate_route("Ялама экспорт", "Баладжары")
    assert result.from_station.canonical_name == "Yalama (eksport)"
    assert result.to_station.canonical_name == "Biləcəri"
    assert result.shipment_type == ShipmentType.IMPORT


def test_sumgayit_to_alat_local(router):
    # 5. Сумгаит -> Алят (Внутренняя / Local)
    result = router.calculate_route("Сумгаит", "Алят")
    assert result.from_station.canonical_name == "Sumqayıt"
    assert result.to_station.canonical_name == "Ələt"
    assert result.shipment_type == ShipmentType.LOCAL


def test_shirvan_to_yalama_export(router):
    # 6. Ширван -> Ялама (Экспорт)
    result = router.calculate_route("Ширван", "Ялама экспорт")
    assert result.from_station.canonical_name == "Şirvan"
    assert result.to_station.canonical_name == "Yalama (eksport)"
    assert result.shipment_type == ShipmentType.EXPORT


def test_absheron_to_boyuk_kasik_export(router):
    # 7. Апшерон -> Беюк Кясик (Экспорт)
    result = router.calculate_route("Апшерон", "Беюк-Кясик-эксп.")
    assert result.from_station.canonical_name == "Abşeron"
    assert result.to_station.canonical_name == "Böyük Kəsik (eksport)"
    assert result.shipment_type == ShipmentType.EXPORT

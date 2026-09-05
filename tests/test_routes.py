# ------------------------------------------------------------------------------
# БЛОК 1: Модульный тест маршрутизатора (проверка ЕСР, порядка и типов перевозки)
# ------------------------------------------------------------------------------
import pytest
from core.router import RailwayRouter, ShipmentType


@pytest.fixture
def router():
    return RailwayRouter(distances_file_path="data/Distances.txt")


def test_unknown_station_raises_value_error(router):
    # Ошибка при поиске несуществующей станции (никаких Abşeron по умолчанию)
    with pytest.raises(ValueError, match="не найдена в справочнике"):
        router.resolve_station("НесуществующаяСтанция999")


def test_strict_order_and_local_type(router):
    # Проверка сохранения порядка и локальной перевозки (Внутренняя -> Внутренняя)
    result = router.calculate_route("Баку-Товарная", "Сумгаит")
    assert result.from_station.canonical_name == "Bakı yük"
    assert result.to_station.canonical_name == "Sumqayıt"
    assert result.shipment_type == ShipmentType.LOCAL


def test_transit_type_classification(router):
    # Проверка транзита (Погранпереход -> Погранпереход)
    result = router.calculate_route("Ялама экспорт", "Беюк-Кясик-эксп.")
    assert result.from_station.is_border is True
    assert result.to_station.is_border is True
    assert result.shipment_type == ShipmentType.TRANSIT


def test_import_type_classification(router):
    # Проверка импорта (Погранпереход -> Внутренняя)
    result = router.calculate_route("Ялама экспорт", "Баку-Товарная")
    assert result.from_station.is_border is True
    assert result.to_station.is_border is False
    assert result.shipment_type == ShipmentType.IMPORT

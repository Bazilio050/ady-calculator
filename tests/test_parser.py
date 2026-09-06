# ------------------------------------------------------------------------------
# БЛОК 1: Автотесты для валидации Pydantic-схемы парсера
# ------------------------------------------------------------------------------
import pytest
from pydantic import ValidationError
from core.schemas import ShipmentQuery


def test_shipment_query_valid():
    """Проверка создания объекта с режимом перевозки и ГНГ от 2 до 8 цифр."""
    query = ShipmentQuery(
        raw_from="Ялама",
        raw_to="Апшерон",
        shipment_type="Импорт",
        gng_code="4407",
        gng_name="Пиломатериалы",
        weight_tons=35.0,
        wagon_type="крытый",
        wagon_ownership="СПС"
    )
    assert query.shipment_type == "Импорт"
    assert query.gng_code == "4407"
    assert query.weight_tons == 35.0
    assert query.wagon_ownership == "СПС"


def test_gng_code_length_validation():
    """Проверка валидации длины ГНГ (от 2 до 8 цифр)."""
    # 2 цифры — валидно
    q2 = ShipmentQuery(raw_from="A", raw_to="B", gng_code="44")
    assert q2.gng_code == "44"

    # 8 цифр — валидно
    q8 = ShipmentQuery(raw_from="A", raw_to="B", gng_code="12345678")
    assert q8.gng_code == "12345678"

    # Меньше 2 цифр — ошибка
    with pytest.raises(ValidationError):
        ShipmentQuery(raw_from="A", raw_to="B", gng_code="4")

    # Больше 8 цифр — ошибка
    with pytest.raises(ValidationError):
        ShipmentQuery(raw_from="A", raw_to="B", gng_code="123456789")


def test_gng_code_digits_only():
    """Проверка на наличие нецифровых символов в ГНГ."""
    with pytest.raises(ValidationError):
        ShipmentQuery(raw_from="A", raw_to="B", gng_code="4407A")

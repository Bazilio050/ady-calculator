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
    print(f"\n[УСПЕХ] Запрос распарсен: {query.raw_from} -> {query.raw_to} | Режим: {query.shipment_type} | ГНГ: {query.gng_code} ({query.gng_name}) | Вес: {query.weight_tons}т | Вагон: {query.wagon_type} ({query.wagon_ownership})")
    assert query.shipment_type == "Импорт"
    assert query.gng_code == "4407"
    assert query.weight_tons == 35.0
    assert query.wagon_ownership == "СПС"


def test_gng_code_length_validation():
    """Проверка валидации длины ГНГ (от 2 до 8 цифр)."""
    q2 = ShipmentQuery(raw_from="A", raw_to="B", gng_code="44")
    print(f"\n[УСПЕХ] Валидация 2-значного ГНГ: {q2.gng_code}")
    assert q2.gng_code == "44"

    q8 = ShipmentQuery(raw_from="A", raw_to="B", gng_code="12345678")
    print(f"[УСПЕХ] Валидация 8-значного ГНГ: {q8.gng_code}")
    assert q8.gng_code == "12345678"

    with pytest.raises(ValidationError):
        ShipmentQuery(raw_from="A", raw_to="B", gng_code="4")

    with pytest.raises(ValidationError):
        ShipmentQuery(raw_from="A", raw_to="B", gng_code="123456789")


def test_gng_code_digits_only():
    """Проверка на наличие нецифровых символов в ГНГ."""
    with pytest.raises(ValidationError):
        ShipmentQuery(raw_from="A", raw_to="B", gng_code="4407A")

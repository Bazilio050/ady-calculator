# core/schemas.py

# ------------------------------------------------------------------------------
# БЛОК 1: Pydantic-схемы для парсинга и валидации параметров перевозки
# ------------------------------------------------------------------------------
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ShipmentQuery(BaseModel):
    """Схема структурированных данных запроса на перевозку (Таблицы 1, 3, 4, 5)."""
    
    # 1. Поля маршрута
    raw_from: str = Field(description="Станция отправления из текста запроса")
    raw_to: str = Field(description="Станция назначения из текста запроса")
    
    shipment_type: Optional[str] = Field(
        default=None,
        description="Режим перевозки: Импорт, Экспорт, Транзит, Внутренняя"
    )
    
    # 2. Поля груза и веса
    gng_code: Optional[str] = Field(
        default=None, 
        description="Код ГНГ груза (строго от 2 до 8 цифр)"
    )
    gng_name: Optional[str] = Field(
        default=None, 
        description="Короткое емкое название груза (1-3 слова max)"
    )
    weight_tons: Optional[float] = Field(
        default=None, 
        description="Фактический вес груза в тоннах"
    )
    
    # 3. Поля вагона и принадлежности
    wagon_type: Optional[str] = Field(
        default=None, 
        description="Тип вагона (крытый, полувагон, цистерна, платформа, рефрижератор, дизель-генератор, двухъярусная платформа)"
    )
    wagon_ownership: Optional[str] = Field(
        default=None, 
        description="Принадлежность вагона (СПС, приватный, собственный, инвентарный, ПС)"
    )
    is_private_wagon: bool = Field(
        default=False,
        description="True, если вагон приватный/собственный (СПС). Применяется коэффициент 0.85"
    )
    shipment_date: Optional[str] = Field(
        default=None,
        description="Дата отправки в формате YYYY-MM-DD (для определения курса валют)"
    )

    # 4. Специфичные поля Таблицы 5 (Спецвагоны и рефсекции)
    ref_section_wagons_count: Optional[int] = Field(
        default=None,
        description="Количество грузовых вагонов в рефрижераторной секции (1, 2, 3, 4, 5 и более)"
    )
    is_tariff_agreement_origin: bool = Field(
        default=False,
        description="True, если плодоовощная продукция произведена в стране Тарифного Соглашения (скидка 0.60)"
    )
    axle_count: int = Field(
        default=4,
        description="Количество осей вагона (по умолчанию 4, для дизель-генераторов и аксиальных ставок)"
    )
    is_in_loaded_ref_section: bool = Field(
        default=False,
        description="True, если вагон следует порожним в составе гружёной рефсекции (0.10 CHF/ось-км)"
    )

    # 5. Специфичные поля для специализированных платформ (Правило 3.1.2.7)
    is_specialized_platform: bool = Field(
        default=False,
        description="True, если перевозка выполняется на специализированной платформе для крупнотоннажных контейнеров"
    )
    coupling_distance_over_19m: bool = Field(
        default=False,
        description="True, если расстояние между осями сцепа автосцепок платформы превышает 19 метров"
    )
    is_oversized_cargo: bool = Field(
        default=False,
        description="True, если перевозимый груз является габаритным/очерченным (əndazəli)"
    )

    @field_validator("gng_code")
    @classmethod
    def validate_gng_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned.isdigit():
            raise ValueError("Код ГНГ должен состоять только из цифр")
        if not (2 <= len(cleaned) <= 8):
            raise ValueError("Длина кода ГНГ должна быть от 2 до 8 цифр")
        return cleaned

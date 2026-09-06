# ------------------------------------------------------------------------------
# БЛОК 1: Pydantic-схемы для парсинга пользовательских запросов
# ------------------------------------------------------------------------------
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ShipmentQuery(BaseModel):
    """Схема структурированных данных, извлекаемых из текста запроса."""
    
    raw_from: str = Field(description="Станция отправления из текста запроса")
    raw_to: str = Field(description="Станция назначения из текста запроса")
    
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
        description="Вес груза в тоннах"
    )
    wagon_type: Optional[str] = Field(
        default=None, 
        description="Тип вагона (например: крытый, полувагон, цистерна, платформа)"
    )
    wagon_ownership: Optional[str] = Field(
        default=None, 
        description="Принадлежность вагона (например: СПС, ПС, инвентарный)"
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

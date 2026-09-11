# core/schemas.py

# ------------------------------------------------------------------------------
# БЛОК 1: Pydantic-схемы для парсинга и валидации параметров перевозки
# ------------------------------------------------------------------------------
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ShipmentQuery(BaseModel):
    """Схема структурированных данных запроса на перевозку (Таблицы 1, 3, 4, 5, 6, 7)."""
    
    # 1. Поля маршрута
    raw_from: str = Field(description="Станция отправления из текста запроса")
    raw_to: str = Field(description="Станция назначения из текста запроса")
    
    shipment_type: Optional[str] = Field(
        default=None,
        description="Режим перевозки: Импорт, Экспорт, Транзит, Внутренняя"
    )
    
    # 2. Поля груза и веса
    gng_code: Optional[str] = Field(
        default="99220000",
        description="Код ГНГ груза (строго от 2 до 8 цифр). По умолчанию 99220000."
    )
    gng_name: Optional[str] = Field(
        default=None, 
        description="Короткое емкое название груза (1-3 слова max)"
    )
    weight_tons: Optional[float] = Field(
        default=None, 
        description="Фактический вес груза в тоннах"
    )

    # 3. Поля тип вагона
    wagon_type: Optional[str] = Field(
        default=None, 
        description="Тип вагона (крытый, полувагон, цистерна, платформа, рефрижератор, дизель-генератор, двухъярусная платформа, автопоезд, полуприцеп, road_train, semi_trailer, road_train_platform, inv, anv, inv_anv, auto_body, detachable_body, кузов, tank_container, reefer_container, wine_juice_container)"
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
    is_empty_wagon: bool = Field(
        default=False,
        description="True, если вагон следует в порожнем состоянии (boş вагон)"
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

    # --------------------------------------------------------------------------
    # БЛОК: Параметры для раздела 3.5 (Негабарит, Транспортеры, Вагоны прикрытия)
    # --------------------------------------------------------------------------
    oversized_degree: Optional[str] = Field(
        default=None,
        description="Степень негабаритности: 'small', '3_top', '3-5_bottom_side', '6_degree' и др."
    )
    is_transporter: bool = Field(
        default=False,
        description="Признак перевозки на транспортере"
    )
    cover_wagons_count: int = Field(
        default=0,
        ge=0,
        description="Количество порожних вагонов прикрытия или защитных рамок"
    )
    is_cover_wagon_private: bool = Field(
        default=True,
        description="Признак приватного вагона прикрытия (True = 0.30 CHF/ось-км, False = 0.35 CHF/ось-км)"
    )

    # --------------------------------------------------------------------------
    # БЛОК: Параметры для раздела 3.6 (Опасные грузы)
    # --------------------------------------------------------------------------
    is_dangerous_cargo: bool = Field(
        default=False,
        description="Признак опасного груза (п. 3.6.1: коэффициент 2.00 к Таблицам 6, 7, 9, 10, 12)"
    )

    # --------------------------------------------------------------------------
    # БЛОК: Код ООН для Таблицы 13 (Опасные грузы)
    # --------------------------------------------------------------------------
    un_code: Optional[str] = Field(
        default=None,
        description="4-значный код ООН (BMT №) для автоматической проверки опасных грузов по Таблице 13"
    )

    # --------------------------------------------------------------------------
    # БЛОК: Параметры для раздела 3.7 (Подвижной состав на своих осях)
    # --------------------------------------------------------------------------
    is_rolling_stock_on_own_axles: bool = Field(
        default=False,
        description="Признак перевозки подвижного состава на своих осях (п. 3.7.1: коэффициент 0.50 к универсальному вагону)"
    )
    is_empty_wagon_repair: bool = Field(
        default=False,
        description="Признак отправки инвентарного вагона в/из ремонта (п. 3.7.2: ставка 0.10 CHF/ось-км)"
    )
    is_passenger_train_composition: bool = Field(
        default=False,
        description="Признак перевозки подвижного состава в составе пассажирского поезда (п. 3.7.3: коэффициент 2.00)"
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

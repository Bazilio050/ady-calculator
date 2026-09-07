# core/calculator.py

from typing import Dict, Any, List
from core.tables.table_1_weight import Table1Calculator
from core.tables.table_min_load import TableMinLoadCalculator
from core.tables.table_3 import Table3Calculator
from core.main_rules import apply_main_rules


class TariffCalculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Центральный модуль расчета провозной платы. 
    Объединяет данные весовых таблиц, базовых ставок и сквозных коэффициентов.
    """

    @classmethod
    def calculate(
        cls,
        shipment_type: str,           # 'import', 'export', 'transit', 'local'
        gng_code: str,                # Код ГНГ
        actual_weight: int,           # Фактический вес в тоннах
        distance_km: float,           # Тарифное расстояние в км
        wagon_type: str,              # Тип вагона
        from_canonical_name: str,     # Станция отправления
        to_canonical_name: str,       # Станция назначения
        is_private_wagon: bool = False,# Собственный/приватный вагон (0.85)
        is_empty: bool = False,       # Порожний пробег
        is_methanol: bool = False,    # Метанол
        is_oil_product: bool = False  # Нефть/нефтепродукты
    ) -> Dict[str, Any]:
        """
        Главный метод расчета итогового тарифа.
        """
        notifications: List[Dict[str, Any]] = []

        # Шаг 1.1: Расчет веса (минимальная норма и Таблица 1)
        # (Логика будет добавлена на Шаге 2)

        return {
            "status": "draft"
        }

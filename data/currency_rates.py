# data/currency_rates.py

from datetime import datetime
from typing import Dict


# Таблица квартальных курсов CHF -> USD
EXCHANGE_RATES: Dict[str, float] = {
    "01.01.2023-31.01.2023": 0.98,
    "01.04.2023-30.06.2023": 0.93,
    "01.07.2023-30.09.2023": 0.91,
    "01.10.2023-31.12.2023": 0.88,
    "01.01.2024-31.03.2024": 0.90,
    "01.04.2024-30.06.2024": 0.87,
    "01.07.2024-30.09.2024": 0.90,
    "01.10.2024-31.12.2024": 0.88,
    "01.01.2025-31.03.2025": 0.86,
    "01.04.2025-30.06.2025": 0.90,
    "01.07.2025-30.09.2025": 0.85,
    "01.09.2025-31.12.2025": 0.81,
    "01.01.2026-31.03.2026": 0.80,
    "01.04.2026-30.06.2026": 0.79,
    "01.07.2026-30.09.2026": 0.79,
    "01.10.2026-31.12.2026": 0.81,
}


def get_exchange_rate(shipment_date: str = None) -> float:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Возвращает курс конвертации CHF -> USD для указанной даты (в формате DD.MM.YYYY).
    Если дата не передана или не найдена в диапазоне, возвращает текущий курс 0.79.
    """
    if not shipment_date:
        return 0.79

    try:
        target_date = datetime.strptime(shipment_date.strip(), "%d.%m.%Y").date()
        for period, rate in EXCHANGE_RATES.items():
            start_str, end_str = period.split("-")
            start_d = datetime.strptime(start_str.strip(), "%d.%m.%Y").date()
            end_d = datetime.strptime(end_str.strip(), "%d.%m.%Y").date()

            if start_d <= target_date <= end_d:
                return rate
    except Exception:
        pass

    return 0.79

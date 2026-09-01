# ==============================================================================
# МОДУЛЬ КУРСОВ ВАЛЮТ ADY (CHF / USD)
# ==============================================================================
from datetime import datetime

FX_RATES = [
    {"start": "2023-01-01", "end": "2023-01-31", "rate": 0.98},
    {"start": "2023-04-01", "end": "2023-06-30", "rate": 0.93},
    {"start": "2023-07-01", "end": "2023-09-30", "rate": 0.91},
    {"start": "2023-10-01", "end": "2023-12-31", "rate": 0.88},
    {"start": "2024-01-01", "end": "2024-03-31", "rate": 0.90},
    {"start": "2024-04-01", "end": "2024-06-30", "rate": 0.87},
    {"start": "2024-07-01", "end": "2024-09-30", "rate": 0.90},
    {"start": "2024-10-01", "end": "2024-12-31", "rate": 0.88},
    {"start": "2025-01-01", "end": "2025-03-31", "rate": 0.86},
    {"start": "2025-04-01", "end": "2025-06-30", "rate": 0.90},
    {"start": "2025-07-01", "end": "2025-09-30", "rate": 0.85},
    {"start": "2025-10-01", "end": "2025-12-31", "rate": 0.81},
    {"start": "2026-04-01", "end": "2026-06-30", "rate": 0.79},
    {"start": "2026-07-01", "end": "2026-09-30", "rate": 0.79},
]

def get_chf_usd_rate(target_date_str: str = None) -> float:
    """
    Возвращает курс USD/CHF на указанную дату (YYYY-MM-DD).
    Если дата не передана, берёт текущую системную дату.
    Если период не найден в таблице FX_RATES, выбрасывает ValueError.
    """
    if not target_date_str:
        target_date = datetime.now().date()
    else:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"invalid_date_format: Неверный формат даты '{target_date_str}'. Используйте YYYY-MM-DD.")

    for item in FX_RATES:
        s_date = datetime.strptime(item["start"], "%Y-%m-%d").date()
        e_date = datetime.strptime(item["end"], "%Y-%m-%d").date()
        if s_date <= target_date <= e_date:
            return item["rate"]

    raise ValueError(f"fx_rate_not_found: Официальный курс CHF/USD на дату {target_date} не найден в справочнике.")

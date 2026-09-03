# ==============================================================================
# МОДУЛЬ КУРСОВ ВАЛЮТ ADY (CHF / USD)
# ==============================================================================
from datetime import datetime

# ------------------------------------------------------------------------------
# БЛОК 1: Справочник официальных периодов и коэффициентов пересчета ADY (USD/CHF)
# ------------------------------------------------------------------------------
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
    {"start": "2026-01-01", "end": "2025-03-31", "rate": 0.80},
    {"start": "2026-04-01", "end": "2026-06-30", "rate": 0.79},
    {"start": "2026-07-01", "end": "2026-09-30", "rate": 0.79},
    {"start": "2026-10-01", "end": "2026-12-31", "rate": 0.81},
]

# ------------------------------------------------------------------------------
# БЛОК 2: Функция получения делителя пересчета ADY (USD/CHF)
# ------------------------------------------------------------------------------
def get_usd_chf_rate(target_date_str: str = None) -> float:
    """
    Возвращает официальный коэффициент деления ADY (USD/CHF) на указанную дату (YYYY-MM-DD).
    Если дата не передана, берется текущая системная дата.
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

    # Резервный коэффициент по умолчанию для 2026 года
    return 0.79


# ------------------------------------------------------------------------------
# БЛОК 3: Функция получения прямых и обратных курсов конвертации
# ------------------------------------------------------------------------------
def get_chf_to_usd_rate(target_date_str: str = None) -> float:
    """
    Возвращает прямой курс стоимости 1 CHF в USD (1 CHF = X USD).
    Пример: при ставке ADY 0.79 вернет 1 / 0.79 = 1.265823...
    """
    base_rate = get_usd_chf_rate(target_date_str)
    if base_rate <= 0:
        return 1.2658
    return round(1.0 / base_rate, 4)


# ------------------------------------------------------------------------------
# БЛОК 4: Функция форматирования строки курса для интерфейса (UI)
# ------------------------------------------------------------------------------
def get_formatted_currency_display(target_date_str: str = None) -> dict:
    """
    Возвращает готовые строки и значения для вывода в интерфейсе пользователя.
    """
    divider_rate = get_usd_chf_rate(target_date_str)
    chf_in_usd = get_chf_to_usd_rate(target_date_str)

    return {
        "divider_rate": divider_rate,
        "chf_in_usd": chf_in_usd,
        "ticker_chf_usd": "CHF/USD",
        "display_chf_usd": f"1 CHF = {chf_in_usd:.4f} USD",
        "display_usd_chf": f"1 USD = {divider_rate} CHF"
    }

# ==============================================================================
# ПРОСЛОЙКА ДЛЯ СОВМЕСТИМОСТИ СО СТАРИМИ ТЕСТАМИ И APP.PY
# ==============================================================================
from core_engine.engine import calculate_freight_tariff

# Алиас для поддержки старого имени функции из tests.py
process_full_calculation = calculate_freight_tariff

__all__ = ["calculate_freight_tariff", "process_full_calculation"]

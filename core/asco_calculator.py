# core/asco_calculator.py

from typing import Dict, Any, Optional

# Тарифные ставки ASCO в USD за 1 погонный метр длины вагона
ASCO_RATES = {
    "turkmenbashi": {
        "base": {"loaded": 45.0, "empty": 36.0},
        "oil_cistern": {"loaded": 70.0, "empty": 32.0, "fixed_length": 13.0},
        "oil_covered": {"loaded": 70.0, "empty": 36.0, "fixed_length": 15.0},
        "alcohol": {"loaded": 72.0, "empty": 36.0},
        "lpg": {"loaded": 119.0, "empty": 36.0},
        "dangerous": {"loaded": 50.0, "empty": 36.0},
        "export_az": {"loaded": 43.0, "empty": 36.0},
    },
    "kuryk": {
        "base": {"loaded": 50.0, "empty": 41.0},
        "oil_cistern": {"loaded": 83.0, "empty": 37.0, "fixed_length": 13.0},
        "oil_covered": {"loaded": 83.0, "empty": 41.0, "fixed_length": 15.0},
        "alcohol": {"loaded": 77.0, "empty": 41.0},
        "lpg": {"loaded": 135.0, "empty": 41.0},
        "dangerous": {"loaded": 55.0, "empty": 41.0},
        "export_az": {"loaded": 48.0, "empty": 41.0},
    }
}


def determine_asco_cargo_category(
    gng_code: str, 
    wagon_type: str, 
    shipment_type: str = "transit"
) -> str:
    """
    Автоматическое определение категории груза ASCO по ГНГ коду и типу вагона.
    """
    clean_gng = str(gng_code).strip()
    w_type = wagon_type.lower()
    ship_type = shipment_type.lower()

    # Нефть и нефтепродукты (ГНГ 2709, 2710)
    if clean_gng.startswith(("2709", "2710")):
        if w_type in ("cistern", "tank", "цистерна", "бункер", "bunker"):
            return "oil_cistern"
        elif w_type in ("covered", "крытый"):
            return "oil_covered"

    # Спирт и спиртные напитки (ГНГ 2207, 2208)
    if clean_gng.startswith(("2207", "2208")):
        return "alcohol"

    # Сжиженный газ (ГНГ 2711)
    if clean_gng.startswith("2711"):
        return "lpg"

    # Экспорт из Азербайджана (неопасные грузы)
    if ship_type in ("export", "экспорт", "ixrac"):
        return "export_az"

    return "base"

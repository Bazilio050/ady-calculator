# ==============================================================================
# МОДУЛЬ 3: ДИНАМИЧЕСКИЙ РАСЧЕТ И СБОРКА КОЭФФИЦИЕНТОВ (ЧИСТАЯ ВЕРСИЯ)
# ==============================================================================
from utils import get_global_coefficients

def calculate_coefficients(
    shipment_mode: str,
    clean_gng: str,
    origin_esr: str,
    dest_esr: str,
    wagon_type: str = "covered",
    is_private_wagon: bool = True,
    nlu_data: dict = None
) -> dict:
    """
    Получает список всех применимых коэффициентов из utils.py,
    перемножает их и формирует детальную расшифровку.
    """
    if nlu_data is None:
        nlu_data = {}

    # 1. Запрос коэффициентов из utils.py
    coeffs_list, notes = get_global_coefficients(
        shipment_type=shipment_mode,
        gng_code=clean_gng,
        origin_esr=origin_esr,
        dest_esr=dest_esr
    )

    total_coeff = 1.0
    applied_details = []

    # 2. Перемножение полученных коэффициентов
    for item in coeffs_list:
        if isinstance(item, tuple) and len(item) == 2:
            name, val = item
            total_coeff *= float(val)
            applied_details.append({
                "name": name,
                "value": float(val),
                "rule_ref": "get_global_coefficients"
            })

    total_coeff_rounded = round(total_coeff, 4)

    return {
        "total_coeff": total_coeff_rounded,
        "details": applied_details
    }

# ==============================================================================
# МОДУЛЬ 3: ДИНАМИЧЕСКИЙ РАСЧЕТ И СБОРКА КОЭФФИЦИЕНТОВ (ЧИСТАЯ ВЕРСИЯ)
# ==============================================================================
from utils import get_applicable_coefficients  # Внешний справочник правил

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
    Получает список всех применимых коэффициентов из внешнего справочника,
    перемножает их и формирует детальную расшифровку.
    """
    if nlu_data is None:
        nlu_data = {}

    # 1. Запрос применимых коэффициентов из внешнего справочника
    coefficients_list = get_applicable_coefficients(
        shipment_mode=shipment_mode,
        clean_gng=clean_gng,
        origin_esr=origin_esr,
        dest_esr=dest_esr,
        wagon_type=wagon_type,
        is_private_wagon=is_private_wagon,
        nlu_data=nlu_data
    )

    # 2. Чистая перемножающая математика (без хардкода)
    total_coeff = 1.0
    applied_details = []

    for item in coefficients_list:
        val = float(item.get("value", 1.0))
        name = item.get("name", "Коэффициент")
        rule_ref = item.get("rule_ref", "")

        total_coeff *= val
        applied_details.append({
            "name": name,
            "value": val,
            "rule_ref": rule_ref
        })

    # Округление итогового коэффициента до 4 знаков после запятой
    total_coeff_rounded = round(total_coeff, 4)

    return {
        "total_coeff": total_coeff_rounded,
        "details": applied_details
    }

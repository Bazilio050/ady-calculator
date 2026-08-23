# ==============================================================================
# МОДУЛЬ 4: РАСЧЕТ ДОПОЛНИТЕЛЬНЫХ СБОРОВ (ОХРАНА, ПАРОМ ASCO, СПЕЦ-УСЛУГИ)
# ==============================================================================
from utils import (
    calculate_security_charge,  # Чтение из Security_Cargo_GNG.txt
    calculate_asco_ferry_fare   # Чтение из ASCO_Tariffs
)

def calculate_special_charges(
    clean_gng: str,
    tariff_dist_km: int,
    chargeable_weight: int,
    nlu_data: dict,
    origin_esr: str = "",
    dest_esr: str = ""
) -> dict:
    """
    Рассчитывает дополнительные сборы: охрану ГНГ, паромные переправы ASCO
    и сборы по специализированным перевозкам.
    """
    special_details = []
    total_special_usd = 0.0

    # 1. Расчет обязательной охраны ГНГ
    sec_cost = calculate_security_charge(
        clean_gng=clean_gng,
        distance_km=tariff_dist_km,
        weight_tons=chargeable_weight,
        nlu_data=nlu_data
    )
    if sec_cost > 0:
        total_special_usd += sec_cost
        special_details.append({
            "name": "Охрана груза (ГНГ)",
            "amount_usd": round(sec_cost, 2),
            "rule_ref": "Security_Cargo_GNG.txt"
        })

    # 2. Расчет паромной переправы ASCO (если задействован паромный маршрут)
    ferry_cost = calculate_asco_ferry_fare(
        origin_esr=origin_esr,
        dest_esr=dest_esr,
        nlu_data=nlu_data
    )
    if ferry_cost > 0:
        total_special_usd += ferry_cost
        special_details.append({
            "name": "Паромная переправа ASCO",
            "amount_usd": round(ferry_cost, 2),
            "rule_ref": "ASCO Tariff Rules"
        })

    return {
        "total_special_usd": round(total_special_usd, 2),
        "details": special_details
    }

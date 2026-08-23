# ==============================================================================
# МОДУЛЬ 4: РАСЧЕТ ДОПОЛНИТЕЛЬНЫХ СБОРОВ (ОХРАНА, ПАРОМ ASCO, СПЕЦ-УСЛУГИ)
# ==============================================================================

def calculate_special_charges(
    clean_gng: str,
    tariff_dist_km: int,
    chargeable_weight: int,
    nlu_data: dict,
    origin_esr: str = "",
    dest_esr: str = ""
) -> dict:
    """
    Рассчитывает дополнительные сборы (охрана ГНГ, паром ASCO и спец-услуги).
    """
    special_details = []
    total_special_usd = 0.0

    # Проверка необходимости охраны из NLU данных
    if nlu_data.get("requires_guard", False):
        guard_rate = float(nlu_data.get("guard_rate_per_km", 0.0))
        sec_cost = guard_rate * tariff_dist_km
        if sec_cost > 0:
            total_special_usd += sec_cost
            special_details.append({
                "name": "Охрана груза (ГНГ)",
                "amount_usd": round(sec_cost, 2),
                "rule_ref": "NLU Security Guard Flag"
            })

    # Проверка паромной переправы ASCO из NLU данных
    if nlu_data.get("is_ferry", False):
        ferry_cost = float(nlu_data.get("ferry_rate_usd", 0.0))
        if ferry_cost > 0:
            total_special_usd += ferry_cost
            special_details.append({
                "name": "Паромная переправа ASCO",
                "amount_usd": round(ferry_cost, 2),
                "rule_ref": "ASCO Ferry Rate"
            })

    return {
        "total_special_usd": round(total_special_usd, 2),
        "details": special_details
    }

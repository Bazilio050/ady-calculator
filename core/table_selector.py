# ==============================================================================
# МОДУЛЬ ВЫБОРА ТАРИФНОЙ ТАБЛИЦЫ ADY 2026 (Стр. 18)
# ==============================================================================

def select_tariff_table(wagon_category: str, shipment_type: str, is_empty_inventory: bool = False) -> str:
    """
    Определяет номер тарифной таблицы для повагонных отправок (универсальные вагоны).
    """
    if is_empty_inventory:
        return "FREE_INVENTORY"

    mode = str(shipment_type or "").strip().lower()
    is_transit = any(k in mode for k in ["tranzit", "transit", "транзит"])

    # Универсальные вагоны (п. 3.1.1)
    if is_transit:
        return "4"  # Cədvəl 4
    else:
        return "3"  # Cədvəl 3

# ==============================================================================
# МОДУЛЬ 5: ГЛАВНЫЙ ДИСПЕТЧЕР-РАСЧЕТЧИК (CORE ENGINE 2.0)
# ==============================================================================
from core_engine.mode_and_distance import determine_shipment_mode, calculate_route_distances
from core_engine.weight_calculator import calculate_chargeable_weight
from core_engine.coefficients import calculate_coefficients
from core_engine.special_tariffs import calculate_special_charges
from tables import get_base_tariff_from_tables  # Диспетчер выбора таблиц (3-12)

def calculate_freight_tariff(nlu_data: dict, user_input_raw: str = "") -> dict:
    """Главный диспетчер: объединяет 4 модуля и возвращает итоговую структуру."""
    origin_esr = str(nlu_data.get("origin_esr", ""))
    dest_esr = str(nlu_data.get("dest_esr", ""))
    clean_gng = str(nlu_data.get("gng_code", ""))
    wagon_type = str(nlu_data.get("wagon_type", "covered"))
    is_private = bool(nlu_data.get("is_private_wagon", True))

    # 1. Режим и километраж
    shipment_mode = determine_shipment_mode(nlu_data, origin_esr, dest_esr)
    actual_dist, tariff_dist = calculate_route_distances(nlu_data, user_input_raw, origin_esr, dest_esr, shipment_mode)

    # 2. Оплачиваемый вес
    weight_info = calculate_chargeable_weight(nlu_data, clean_gng)
    chargeable_weight = weight_info["chargeable_weight"]

    # 3. Базовая ставка из таблиц (3-12)
    base_rate_usd = get_base_tariff_from_tables(
        clean_gng=clean_gng,
        tariff_dist_km=tariff_dist,
        wagon_type=wagon_type,
        nlu_data=nlu_data
    )

    # 4. Коэффициенты
    coeff_info = calculate_coefficients(
        shipment_mode=shipment_mode,
        clean_gng=clean_gng,
        origin_esr=origin_esr,
        dest_esr=dest_esr,
        wagon_type=wagon_type,
        is_private_wagon=is_private,
        nlu_data=nlu_data
    )

    # 5. Спецсборы (Охрана, ASCO и др.)
    special_info = calculate_special_charges(
        clean_gng=clean_gng,
        tariff_dist_km=tariff_dist,
        chargeable_weight=chargeable_weight,
        nlu_data=nlu_data,
        origin_esr=origin_esr,
        dest_esr=dest_esr
    )

    # Итоговая математика
    main_railway_tariff = base_rate_usd * chargeable_weight * coeff_info["total_coeff"]
    total_final_usd = main_railway_tariff + special_info["total_special_usd"]

    return {
        "shipment_mode": shipment_mode,
        "actual_dist_km": actual_dist,
        "tariff_dist_km": tariff_dist,
        "weight_info": weight_info,
        "base_rate_usd": round(base_rate_usd, 4),
        "total_coeff": coeff_info["total_coeff"],
        "coeff_details": coeff_info["details"],
        "main_railway_tariff_usd": round(main_railway_tariff, 2),
        "special_charges_usd": special_info["total_special_usd"],
        "special_details": special_info["details"],
        "total_final_usd": round(total_final_usd, 2)
    }

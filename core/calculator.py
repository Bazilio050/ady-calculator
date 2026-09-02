# ==============================================================================
# МОДУЛЬ РАСЧЕТА ТАРИФОВ ADY 2026 (CORE CALCULATOR ENGINE)
# ==============================================================================
import re
from core.distance_finder import get_route_info
from core.table_parser import get_base_rate_from_table
from core.table_selector import select_tariff_table
from core.coefficients import get_applicable_coefficients
from core.currency import get_chf_usd_rate

def calculate_freight(
    from_station: str,
    to_station: str,
    gng_code: str,
    fact_weight: float = 0.0,
    wagon_type: str = "universal",
    shipment_type: str = "import",
    is_empty_wagon: bool = False,
    is_private_wagon: bool = True,
    ref_cars_count: int = None,
    apply_fresh_produce_discount: bool = False,
    is_long_platform_over_19m: bool = False,
    origin_country: str = None,
    destination_country: str = None,
    gng_name: str = None,
    calculation_date: str = None,
    lang: str = "AZ",
    raw_prompt: str = "",
    **kwargs
) -> dict:
    
    # 1. Защитная валидация обязательных данных
    if not is_empty_wagon and not str(gng_code or "").strip():
        raise ValueError("gng_code_required")

    # 2. Расчет расстояния
    dist_info = get_route_info(from_station, to_station, shipment_type=shipment_type)
    distance = dist_info.get("distance_km", 0)
    if distance <= 0:
        raise ValueError("route_not_found")

    # 3. Валидация валютного курса
    chf_rate = get_chf_usd_rate(calculation_date)
    if not chf_rate:
        raise ValueError("fx_rate_not_found")

    # 4. Выбор тарифной таблицы и колонки
    table_info = select_tariff_table(
        wagon_category=wagon_type,
        shipment_type=shipment_type,
        is_empty_inventory=False,
        gng_code=gng_code,
        fact_weight=fact_weight
    )
    table_num = str(table_info["table"])
    column_num = int(table_info["column"])

    # 5. Получение базовой ставки (в CHF)
    base_tariff_chf = get_base_rate_from_table(
        table_number=table_num,
        distance_km=distance,
        weight_category=int(fact_weight),
        column_number=column_num
    )
    
    # 6. Расчет применимых коэффициентов
    coeff_data = get_applicable_coefficients(
        shipment_type=shipment_type,
        gng_code=gng_code,
        table_number=table_num,
        wagon_type=wagon_type,
        from_station=from_station,
        to_station=to_station,
        is_loaded=not is_empty_wagon,
        is_private_wagon=is_private_wagon,
        ref_cars_count=ref_cars_count,
        apply_fresh_produce_discount=apply_fresh_produce_discount,
        is_long_platform_over_19m=is_long_platform_over_19m,
        lang=lang
    )

    total_multiplier = coeff_data["total_multiplier"]
    coeffs_list = coeff_data["coefficients_list"]

    # 7. Математика расчета с учетом особенностей Cədvəl 5 и конвертации CHF -> USD
    is_per_wagon_flat_rate = (table_num == "5" and column_num in [2, 4])

    if is_per_wagon_flat_rate:
        final_tariff_chf = base_tariff_chf * total_multiplier
        final_tariff_usd = final_tariff_chf / chf_rate
        
        calc_weight = max(fact_weight, 1.0)
        usd_per_ton = final_tariff_usd / calc_weight
        total_usd_wagon = final_tariff_usd
    else:
        calc_weight = fact_weight
        final_tariff_chf = base_tariff_chf * total_multiplier
        usd_per_ton = final_tariff_chf / chf_rate
        total_usd_wagon = usd_per_ton * calc_weight

    # 8. Сборка детализированного ответа для UI
    # Формируем строку с кодом/названием груза и типом вагона
    cargo_str = f"ГНГ {gng_code}" + (f" ({gng_name})" if gng_name else "")
    cargo_and_wagon_info = f"{cargo_str}, {wagon_type}"

    part1 = {
        "route": f"{from_station} — {to_station}",
        "shipment_type": shipment_type,
        "distance": f"{distance} km",
        "weight_info": f"{fact_weight} t" if not is_empty_wagon else "0 t (Boş)",
        "wagon_type": wagon_type,
        "ref_cars_count": ref_cars_count,
        "cargo_and_wagon": cargo_and_wagon_info  # Добавлен отсутствующий ключ для app.py
    }

    part2 = {
        "chf_usd_rate": chf_rate,
        "base_tariff": f"{base_tariff_chf:.2f} CHF (Cədvəl {table_num}, Sütun {column_num})",
        "coefficients": coeffs_list,
        "total_multiplier": total_multiplier
    }

    part3 = {
        "usd_per_ton": round(usd_per_ton, 2),
        "total_usd_wagon": round(total_usd_wagon, 2),
        "is_flat_rate": is_per_wagon_flat_rate
    }

    return {
        "total_usd": round(total_usd_wagon, 2),
        "rate_per_ton": round(usd_per_ton, 2),
        "part1": part1,
        "part2": part2,
        "part3": part3,
        "raw_prompt": raw_prompt
    }

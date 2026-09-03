# ==============================================================================
# МОДУЛЬ РАСЧЕТА ТАРИФОВ ADY 2026 (CORE CALCULATOR ENGINE)
# ==============================================================================
import os
import sys

from core.distance_finder import get_route_info
from core.table_parser import get_base_rate_from_table
from core.table_selector import select_tariff_table
from core.coefficients import get_applicable_coefficients
from core.currency import get_chf_usd_rate
from core.weight import get_weight_display_info
from data.stations_mapping import format_station_display


# ==============================================================================
# СПРАВОЧНИКИ ЛОКАЛИЗАЦИИ И ПЕРЕВОДОВ (UI TRANSLATION DICTIONARIES)
# ==============================================================================

SHIPMENT_TYPES_LANG = {
    "TRANSIT": {"AZ": "Tranzit", "RU": "Транзит", "EN": "Transit"},
    "IMPORT": {"AZ": "İdxal", "RU": "Импорт", "EN": "Import"},
    "EXPORT": {"AZ": "İxrac", "RU": "Экспорт", "EN": "Export"},
    "LOCAL": {"AZ": "Daxili", "RU": "Местное", "EN": "Local"}
}

WAGON_TYPES_LANG = {
    "universal": {"AZ": "Universal vaqon", "RU": "Универсальный вагон", "EN": "Universal wagon"},
    "covered": {"AZ": "Örtülü vaqon", "RU": "Крытый вагон", "EN": "Covered wagon"},
    "open": {"AZ": "Yarımvaqon", "RU": "Полувагон", "EN": "Gondola wagon"},
    "platform": {"AZ": "Platforma", "RU": "Платформа", "EN": "Flatcar"},
    "fitting_platform": {"AZ": "Fiting platforması", "RU": "Фитинговая платформа", "EN": "Fitting flatcar"},
    "cistern": {"AZ": "Çən vaqonu", "RU": "Цистерна", "EN": "Tank wagon"},
    "refr": {"AZ": "Refrijerator", "RU": "Рефрижератор", "EN": "Refrigerated wagon"},
    "thermos": {"AZ": "Termos vaqon", "RU": "Вагон-термос", "EN": "Thermos wagon"},
    "hopper": {"AZ": "Xopper vaqonu", "RU": "Хоппер", "EN": "Hopper wagon"},
    "grain": {"AZ": "Taxıldaşıyan (Xopper)", "RU": "Зерновоз (Хоппер)", "EN": "Grain hopper"},
    "cement": {"AZ": "Sementdaşıyan", "RU": "Цементовоз", "EN": "Cement hopper"},
    "fertilizer": {"AZ": "Gübrədaşıyan", "RU": "Удобровоз / Минераловоз", "EN": "Fertilizer hopper"},
    "pellet": {"AZ": "Aqlomerat/Həbdaşıyan", "RU": "Окатышевоз", "EN": "Pellet hopper"},
    "car_transporter": {"AZ": "Avtomobildaşıyan", "RU": "Автомобилевоз", "EN": "Car transporter"},
    "cattle": {"AZ": "Mal-qara vaqonu", "RU": "Скотовоз", "EN": "Cattle wagon"},
    "transporter": {"AZ": "Nəqledici (Transporter)", "RU": "Транспортер", "EN": "Heavy transporter"},
    "dumpcar": {"AZ": "Dumpkar (Özüdökən)", "RU": "Думпкар (Самосвал)", "EN": "Dumpcar"},
    "special": {"AZ": "Xüsusi vaqon", "RU": "Специализированный вагон", "EN": "Special wagon"},
    "ref_section": {"AZ": "Refrijerator seksiyası", "RU": "Рефрижераторная секция", "EN": "Refrigerated section"},
    "autocar": {"AZ": "avtomobildaşıyan platforma", "RU": "платформа-автомобилевоз", "EN": "car-carrying platform"},
    "two_tier_car_platform": {"AZ": "İkimərtəbəli avtomobildaşıyan platforma", "RU": "Двухъярусная платформа-автомобилевоз", "EN": "Two-tier car-carrying platform"},
}


# ==============================================================================
# ОСНОВНАЯ ФУНКЦИЯ РАСЧЕТА ТАРИФА (MAIN CALCULATION FUNCTION)
# ==============================================================================

def calculate_freight(
    from_station: str,
    to_station: str,
    gng_code: str = "",
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
    
    current_lang = (lang or "AZ").upper()

    # --------------------------------------------------------------------------
    # БЛОК 1: Защитная валидация обязательных данных и синонимов станций
    # --------------------------------------------------------------------------
    if not is_empty_wagon and not str(gng_code or "").strip():
        raise ValueError("gng_code_required")

    STATION_ALIASES = {
        "ТРК": "Ələt-eksp.Türk.",
    }
    from_station_clean = STATION_ALIASES.get(from_station, from_station)
    to_station_clean = STATION_ALIASES.get(to_station, to_station)

    # --------------------------------------------------------------------------
    # БЛОК 2: Расчет ж/д расстояния через модуль distance_finder
    # --------------------------------------------------------------------------
    dist_info = get_route_info(from_station_clean, to_station_clean, shipment_type=shipment_type, lang=current_lang)
    if not dist_info or not isinstance(dist_info, dict):
        raise ValueError("route_not_found")

    distance = dist_info.get("distance_km", 0)
    if not distance or distance <= 0:
        raise ValueError("route_not_found")

    # --------------------------------------------------------------------------
    # БЛОК 3: Проверка и получение курса валют (CHF/USD)
    # --------------------------------------------------------------------------
    chf_rate = get_chf_usd_rate(calculation_date)
    if not chf_rate:
        raise ValueError("fx_rate_not_found")

    # --------------------------------------------------------------------------
    # БЛОК 4: Расчет весовых параметров и нормы загрузки (core/weight.py)
    # --------------------------------------------------------------------------
    axles_val = kwargs.get("wagon_axles", 4) or kwargs.get("transporter_axles", 0)
    
    weight_data = get_weight_display_info(
        fact_weight=fact_weight,
        gng_code=gng_code,
        wagon_type=wagon_type,
        transporter_axles=axles_val  # <- Передаем созданную выше axles_val!
    )
    
    chargeable_tons = weight_data["chargeable_tons"]     
    weight_cat = weight_data["weight_category"]         
    weight_info_display = weight_data["weight_info_str"]

    # --------------------------------------------------------------------------
    # БЛОК 5: Определение тарифной таблицы ADY Policy 2026
    # --------------------------------------------------------------------------
    table_info = select_tariff_table(
        wagon_category=wagon_type,
        shipment_type=shipment_type,
        is_empty_inventory=False,
        gng_code=gng_code,
        fact_weight=chargeable_tons
    )
    table_num = str(table_info["table"])
    column_num = int(table_info["column"])

    # --------------------------------------------------------------------------
    # БЛОК 6: Поиск базовой ставки по нормативной весовой категории
    # --------------------------------------------------------------------------
    base_tariff_chf = get_base_rate_from_table(
        table_number=table_num,
        distance_km=distance,
        weight_category=weight_cat,
        column_number=column_num
    )

    # --------------------------------------------------------------------------
    # БЛОК 7: Расчет коэффициентов ADY
    # --------------------------------------------------------------------------
    coeff_data = get_applicable_coefficients(
        shipment_type=shipment_type,
        gng_code=gng_code,
        table_number=table_num,
        wagon_type=wagon_type,
        from_station=from_station_clean,
        to_station=to_station_clean,
        is_loaded=not is_empty_wagon,
        is_private_wagon=is_private_wagon,
        ref_cars_count=ref_cars_count,
        apply_fresh_produce_discount=apply_fresh_produce_discount,
        is_long_platform_over_19m=is_long_platform_over_19m,
        lang=current_lang
    )

    total_multiplier = coeff_data["total_multiplier"]
    coeffs_list = coeff_data["coefficients_list"]

    # --------------------------------------------------------------------------
    # БЛОК 8: Математический расчет
    # --------------------------------------------------------------------------
    is_per_wagon_flat_rate = (table_num == "5" and column_num in [2, 4, 6])

    if is_per_wagon_flat_rate:
        final_tariff_chf = base_tariff_chf * total_multiplier
        final_tariff_usd = final_tariff_chf / chf_rate
        calc_weight = max(chargeable_tons, 1.0)
        usd_per_ton = final_tariff_usd / calc_weight
        total_usd_wagon = final_tariff_usd
    else:
        final_tariff_chf = base_tariff_chf * total_multiplier
        usd_per_ton = final_tariff_chf / chf_rate
        calc_weight = chargeable_tons
        total_usd_wagon = usd_per_ton * calc_weight

    # --------------------------------------------------------------------------
    # БЛОК 9: Локализация и отображение
    # --------------------------------------------------------------------------
    ship_type_key = shipment_type.upper()
    shipment_type_display = SHIPMENT_TYPES_LANG.get(ship_type_key, {}).get(current_lang, ship_type_key)
    wagon_type_display = WAGON_TYPES_LANG.get(wagon_type.lower(), {}).get(current_lang, wagon_type)

    dist_unit = "км" if current_lang == "RU" else "km"
    weight_unit = "т" if current_lang == "RU" else "t"

    cargo_label = f"ГНГ {gng_code}" + (f" ({gng_name})" if gng_name else "")
    cargo_and_wagon_str = f"{cargo_label}, {wagon_type_display}"
    period_str = calculation_date if calculation_date else "2026"

    if current_lang == "RU":
        tbl_str = f"Таблица {table_num}, Колонка {column_num}"
    elif current_lang == "EN":
        tbl_str = f"Table {table_num}, Column {column_num}"
    else:
        tbl_str = f"Cədvəl {table_num}, Sütun {column_num}"
    base_tariff_display = f"{base_tariff_chf:.2f} CHF ({tbl_str})"

    st_from_name = dist_info.get("from_station_name") or dist_info.get("from_station") or from_station
    st_from_code = (
        dist_info.get("from_station_code") or 
        dist_info.get("from_code") or 
        dist_info.get("code_from") or 
        kwargs.get("from_station_code", "")
    )
    
    st_to_name = dist_info.get("to_station_name") or dist_info.get("to_station") or to_station
    st_to_code = (
        dist_info.get("to_station_code") or 
        dist_info.get("to_code") or 
        dist_info.get("code_to") or 
        kwargs.get("to_station_code", "")
    )

    from_formatted = format_station_display(st_from_name, st_from_code, lang=current_lang)
    to_formatted = format_station_display(st_to_name, st_to_code, lang=current_lang)
    route_display = f"{from_formatted} — {to_formatted}"

    # ИСПОЛЬЗУЕМ СТРОКУ ИЗ weight.py (с нормой 60т)
    if is_empty_wagon:
        weight_info_str = "0 т (Порожний)" if current_lang == "RU" else ("0 t (Boş)" if current_lang == "AZ" else "0 t (Empty)")
    else:
        weight_info_str = weight_info_display

    coeffs_formula_str = " * ".join([f"{c['value']}" for c in coeffs_list]) if coeffs_list else "1.00"
    
    if is_per_wagon_flat_rate:
        formula_text = f"{base_tariff_chf:.2f} CHF/{chf_rate:.2f} * {coeffs_formula_str} = ${total_usd_wagon:.2f} USD / вагон"
    else:
        formula_text = f"{base_tariff_chf:.2f} CHF/{chf_rate:.2f} * {coeffs_formula_str} = ${usd_per_ton:.2f} USD/{weight_unit}"

    # --------------------------------------------------------------------------
    # БЛОК 10: Сборка итогового ответа
    # --------------------------------------------------------------------------
    part1 = {
        "route": route_display,
        "shipment_type": shipment_type_display,
        "distance": f"{distance} {dist_unit}",
        "weight_info": weight_info_str,
        "cargo_and_wagon": cargo_and_wagon_str,
        "period": period_str,
        "wagon_type": wagon_type_display,
        "ref_cars_count": ref_cars_count
    }

    part2 = {
        "exchange_rate": f"1 USD = {chf_rate} CHF",
        "base_tariff": base_tariff_display,
        "coefficients": coeffs_list,
        "total_multiplier": total_multiplier
    }

    if current_lang == "RU":
        base_note = "Тариф рассчитан согласно Тарифной политике ADY 2026."
        base_rate_note = f"Базовый тариф: {base_tariff_chf:.2f} CHF ({tbl_str})."
        fx_note = f"Курс пересчета: 1 USD = {chf_rate:.2f} CHF."
    elif current_lang == "EN":
        base_note = "Tariff is calculated according to ADY 2026 Tariff Policy."
        base_rate_note = f"Base rate: {base_tariff_chf:.2f} CHF ({tbl_str})."
        fx_note = f"Exchange rate: 1 USD = {chf_rate:.2f} CHF."
    else:
        base_note = "Tarif ADY 2026 Tarif Siyasətinə uyğun hesablanmışdır."
        base_rate_note = f"Baza tarifi: {base_tariff_chf:.2f} CHF ({tbl_str})."
        fx_note = f"Valyuta məzənnəsi: 1 USD = {chf_rate:.2f} CHF."

    dynamic_notes = [
        base_note,
        base_rate_note,
        fx_note
    ]

    min_norm = weight_data.get("min_weight_norm", 0)
    if min_norm > 0 and fact_weight < min_norm:
        if current_lang == "RU":
            dynamic_notes.append(f"Применена минимальная норма загрузки {min_norm} тонн.")
        elif current_lang == "EN":
            dynamic_notes.append(f"Minimum loading norm of {min_norm} tons applied.")
        else:
            dynamic_notes.append(f"Minimum yükləmə norması tətbiq olundu: {min_norm} ton.")

    for coeff in coeffs_list:
        if coeff.get("note"):
            dynamic_notes.append(coeff["note"])

    part3 = {
        "formula": formula_text,
        "net_ady_rate": f"${usd_per_ton:.2f} USD/{weight_unit}" if not is_per_wagon_flat_rate else f"${total_usd_wagon:.2f} USD",
        "usd_per_ton": round(usd_per_ton, 2),
        "total_usd_wagon": round(total_usd_wagon, 2),
        "is_flat_rate": is_per_wagon_flat_rate,
        "notes": dynamic_notes
    }

    return {
        "total_usd": round(total_usd_wagon, 2),
        "rate_per_ton": round(usd_per_ton, 2),
        "part1": part1,
        "part2": part2,
        "part3": part3,
        "raw_prompt": raw_prompt
    }

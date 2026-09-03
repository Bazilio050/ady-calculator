# ==============================================================================
# ОСНОВНОЙ МОДУЛЬ РАСЧЕТА ТАРИФОВ ADY (ТАРИФНАЯ ПОЛИТИКА 2026)
# ==============================================================================
import math
from core.currency import get_formatted_currency_display
from core.coefficients import get_all_coefficients
from core.table_selector import select_tariff_table_and_column
from core.weight import calculate_chargeable_weight, get_weight_display_info
from data.stations_mapping import format_station_display

# ------------------------------------------------------------------------------
# БЛОК 1: Словари локализации
# ------------------------------------------------------------------------------
WAGON_TYPES_LANG = {
    "universal": {"AZ": "Universal vaqon", "RU": "Универсальный вагон", "EN": "Universal wagon"},
    "tank": {"AZ": "Sistern", "RU": "Цистерна", "EN": "Tank wagon"},
    "autocar": {"AZ": "Avtomobildaşıyan vaqon", "RU": "Автомобилевоз", "EN": "Car transporter"},
    "two_tier_car_platform": {"AZ": "İkimərtəbəli avtomobildaşıyan platforma", "RU": "Двухъярусный автомобилевоз", "EN": "Two-tier car transporter"},
    "arv": {"AZ": "Avtonom refrigirator vaqonu (ARV)", "RU": "Автономный рефрижераторный вагон (АРВ)", "EN": "Autonomous refrigerated wagon"},
    "thermos": {"AZ": "Termos vaqon", "RU": "Вагон-термос", "EN": "Thermos wagon"},
    "ref_section": {"AZ": "Refrigirator seksiyası", "RU": "Рефрижераторная секция", "EN": "Refrigerated section"}
}

SHIPMENT_TYPES_LANG = {
    "transit": {"AZ": "Tranzit", "RU": "Транзит", "EN": "Transit"},
    "import": {"AZ": "İdxal", "RU": "Импорт", "EN": "Import"},
    "export": {"AZ": "İxrac", "RU": "Экспорт", "EN": "Export"}
}

# ------------------------------------------------------------------------------
# БЛОК 2: Главная функция расчета провозной платы
# ------------------------------------------------------------------------------
def calculate_freight(
    from_station: str = "",
    to_station: str = "",
    from_station_code: str = "",
    to_station_code: str = "",
    gng_code: str = "",
    gng_name: str = "",
    fact_weight: float = 0.0,
    wagon_type: str = "universal",
    shipment_type: str = "transit",
    is_empty_wagon: bool = False,
    is_private_wagon: bool = False,
    is_round_trip: bool = False,
    wagon_axles: int = 4,
    distance_km: int = 680,
    lang: str = "AZ",
    raw_prompt: str = ""
) -> dict:
    current_lang = (lang or "AZ").upper()

    # 1. Форматирование станций с передачей ЕСР-кодов из NLU
    from_formatted = format_station_display(from_station, from_station_code, lang=current_lang)
    to_formatted = format_station_display(to_station, to_station_code, lang=current_lang)
    route_display = f"{from_formatted} — {to_formatted}"

    ship_type_dict = SHIPMENT_TYPES_LANG.get(shipment_type, SHIPMENT_TYPES_LANG["transit"])
    shipment_type_display = ship_type_dict.get(current_lang, ship_type_dict["AZ"])

    wagon_type_dict = WAGON_TYPES_LANG.get(wagon_type, WAGON_TYPES_LANG["universal"])
    wagon_display = wagon_type_dict.get(current_lang, wagon_type_dict["AZ"])
    
    cargo_display = f"ГНГ {gng_code} ({gng_name})" if gng_code else gng_name
    
    if current_lang == "AZ":
        ownership_str = "Şəxsi (SPS)" if is_private_wagon else "İnventar (MPS)"
    elif current_lang == "EN":
        ownership_str = "Private (SPS)" if is_private_wagon else "Inventory (MPS)"
    else:
        ownership_str = "СПС" if is_private_wagon else "МПС"

    cargo_and_wagon_display = f"{cargo_display}, {wagon_display} ({ownership_str})"

    # 2. Расчет весовых категорий
    weight_data = get_weight_display_info(
        fact_weight=fact_weight,
        gng_code=gng_code,
        wagon_type=wagon_type
    )
    chargeable_tons = weight_data["chargeable_tons"]
    weight_info_display = weight_data["weight_info_str"]

    # 3. Выбор тарифной таблицы и расчет базового тарифа
    table_info = select_tariff_table_and_column(
        gng_code=gng_code,
        wagon_type=wagon_type,
        shipment_type=shipment_type,
        is_empty_wagon=is_empty_wagon,
        fact_weight=fact_weight,
        wagon_axles=wagon_axles
    )

    # Берем тариф из таблицы ADY (если совпадений нет, применяется расчет по расстоянию)
    table_tariff_value = table_info.get("tariff_value_chf", 0.0)
    if table_tariff_value > 0:
        base_tariff_chf = round(table_tariff_value, 2)
    else:
        base_tariff_chf = round(distance_km * 0.015 * max(chargeable_tons, 10), 2)

    # 4. Получение коэффициентов
    coeffs_list = get_all_coefficients(
        gng_code=gng_code,
        wagon_type=wagon_type,
        shipment_type=shipment_type,
        is_private_wagon=is_private_wagon,
        is_round_trip=is_round_trip,
        wagon_axles=wagon_axles
    )

    total_coeff = 1.0
    for c in coeffs_list:
        if c.get("applied", True):
            total_coeff *= c["value"]

    curr_display = get_formatted_currency_display()
    divider_rate = curr_display["divider_rate"]  # 0.79

    net_chf = round(base_tariff_chf * total_coeff, 2)
    net_usd = round(net_chf / divider_rate, 2)

    # 5. Динамические примечания (Qeydlər) под язык интерфейса
    notes = []
    if weight_data.get("min_weight_norm", 0) > 0:
        if current_lang == "AZ":
            notes.append(f"Minimum yükləmə norması tətbiq olundu: {weight_data['min_weight_norm']} ton.")
        elif current_lang == "EN":
            notes.append(f"Minimum loading norm applied: {weight_data['min_weight_norm']} tons.")
        else:
            notes.append(f"Применена минимальная норма загрузки {weight_data['min_weight_norm']} тонн.")

    if not is_private_wagon:
        if current_lang == "AZ":
            notes.append("İnventar vaqon (MPS) — 0.85 əmsalı tətbiq edilmir.")
        elif current_lang == "EN":
            notes.append("Inventory wagon (MPS) — 0.85 coefficient is not applied.")
        else:
            notes.append("Вагон инвентарный (МПС) — коэффициент 0.85 не применяется.")
    else:
        if current_lang == "AZ":
            notes.append("Şəxsi vaqon (SPS) — 0.85 əmsalı tətbiq edilir.")
        elif current_lang == "EN":
            notes.append("Private wagon (SPS) — 0.85 coefficient is applied.")
        else:
            notes.append("Вагон собственный (СПС) — применяется коэффициент 0.85.")

    if current_lang == "AZ":
        notes.append("Məbləğ 1 vaqon üçün hesablanmışdır.")
    elif current_lang == "EN":
        notes.append("The amount is calculated per 1 wagon.")
    else:
        notes.append("Сумма рассчитана за 1 вагон.")

    # 6. Наглядная формула с промежуточным итогом в CHF
    formula_str = f"({base_tariff_chf:.2f} CHF × {total_coeff:.4f} = {net_chf:.2f} CHF) ÷ {divider_rate} = {net_usd:.2f} USD"

    # Единица измерения тарифа
    per_wagon_suffix = "/ 1 vaqon" if current_lang == "AZ" else ("/ 1 wagon" if current_lang == "EN" else "/ 1 вагон")

    return {
        "part1": {
            "route": route_display,
            "shipment_type": shipment_type_display,
            "distance": f"{distance_km} км" if current_lang != "AZ" else f"{distance_km} km",
            "cargo_and_wagon": cargo_and_wagon_display,
            "weight_info": weight_info_display,
            "period": "2026"
        },
        "part2": {
            "exchange_rate": curr_display["display_chf_usd"],
            "base_tariff": f"{base_tariff_chf:.2f} CHF",
            "coefficients": coeffs_list
        },
        "part3": {
            "formula": formula_str,
            "net_ady_rate": f"{net_usd:.2f} USD ({net_chf:.2f} CHF) {per_wagon_suffix}",
            "notes": notes
        }
    }

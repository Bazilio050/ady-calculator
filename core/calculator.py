# ==============================================================================
# ОСНОВНОЙ МОДУЛЬ РАСЧЕТА ТАРИФОВ ADY (ТАРИФНАЯ ПОЛИТИКА 2026)
# ==============================================================================
import math
from core.currency import get_usd_chf_rate, get_formatted_currency_display
from core.coefficients import get_all_coefficients
from core.table_selector import select_tariff_table_and_column
from core.weight import calculate_chargeable_weight, get_weight_display_info
from data.stations_mapping import format_station_display

# ------------------------------------------------------------------------------
# БЛОК 1: Словари локализации видов вагонов и видов перевозок
# ------------------------------------------------------------------------------
WAGON_TYPES_LANG = {
    "universal": {
        "AZ": "Universal vaqon",
        "RU": "Универсальный вагон",
        "EN": "Universal wagon"
    },
    "tank": {
        "AZ": "Sistern",
        "RU": "Цистерна",
        "EN": "Tank wagon"
    },
    "autocar": {
        "AZ": "Avtomobildaşıyan vaqon",
        "RU": "Автомобилевоз",
        "EN": "Car transporter"
    },
    "two_tier_car_platform": {
        "AZ": "İkimərtəbəli avtomobildaşıyan platforma",
        "RU": "Двухъярусный автомобилевоз",
        "EN": "Two-tier car transporter"
    },
    "arv": {
        "AZ": "Avtonom refrigirator vaqonu (ARV)",
        "RU": "Автономный рефрижераторный вагон (АРВ)",
        "EN": "Autonomous refrigerated wagon"
    },
    "thermos": {
        "AZ": "Termos vaqon",
        "RU": "Вагон-термос",
        "EN": "Thermos wagon"
    },
    "ref_section": {
        "AZ": "Refrigirator seksiyası",
        "RU": "Рефрижераторная секция",
        "EN": "Refrigerated section"
    }
}

SHIPMENT_TYPES_LANG = {
    "transit": {
        "AZ": "Tranzit",
        "RU": "Транзит",
        "EN": "Transit"
    },
    "import": {
        "AZ": "İdxal",
        "RU": "Импорт",
        "EN": "Import"
    },
    "export": {
        "AZ": "İxrac",
        "RU": "Экспорт",
        "EN": "Export"
    }
}


# ------------------------------------------------------------------------------
# БЛОК 2: Главная функция расчета провозной платы (calculate_freight)
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
    """
    Выполняет полный расчет железнодорожного тарифа ADY на основе входящих данных.
    """
    current_lang = (lang or "AZ").upper()

    # 1. Локализация названий станций и видов перевозки
    from_formatted = format_station_display(from_station, from_station_code, lang=current_lang)
    to_formatted = format_station_display(to_station, to_station_code, lang=current_lang)
    route_display = f"{from_formatted} — {to_formatted}"

    ship_type_dict = SHIPMENT_TYPES_LANG.get(shipment_type, SHIPMENT_TYPES_LANG["transit"])
    shipment_type_display = ship_type_dict.get(current_lang, ship_type_dict["AZ"])

    # 2. Локализация типа вагона и наименования груза
    wagon_type_dict = WAGON_TYPES_LANG.get(wagon_type, WAGON_TYPES_LANG["universal"])
    wagon_display = wagon_type_dict.get(current_lang, wagon_type_dict["AZ"])
    
    cargo_display = f"ГНГ {gng_code} ({gng_name})" if gng_code else gng_name
    
    # Флаг собственника для отображения
    ownership_str = "СПС" if is_private_wagon else "МПС"
    cargo_and_wagon_display = f"{cargo_display}, {wagon_display} ({ownership_str})"

    # 3. Расчет весовых категорий через модуль weight.py
    weight_data = get_weight_display_info(
        fact_weight=fact_weight,
        gng_code=gng_code,
        wagon_type=wagon_type
    )
    chargeable_tons = weight_data["chargeable_tons"]
    weight_info_display = weight_data["weight_info_str"]

    # 4. Выбор тарифной таблицы и колонки
    table_info = select_tariff_table_and_column(
        gng_code=gng_code,
        wagon_type=wagon_type,
        is_empty_wagon=is_empty_wagon,
        wagon_axles=wagon_axles
    )

    # 5. Получение базового тарифа в CHF (базовая фиктивная сетка для примера/заглушки)
    # В реале тут будет обращение к тарифной сетке ADY по расстоянию и весовой категории
    base_tariff_chf = round(distance_km * 0.015 * max(chargeable_tons, 10), 2)

    # 6. Расчет коэффициентов (включая проверку СПС / МПС)
    coeffs_data = get_all_coefficients(
        gng_code=gng_code,
        wagon_type=wagon_type,
        shipment_type=shipment_type,
        is_private_wagon=is_private_wagon,
        is_round_trip=is_round_trip,
        wagon_axles=wagon_axles
    )

    # Умножение всех применимых коэффициентов
    total_coeff = 1.0
    applied_coeffs_list = []
    for c in coeffs_data:
        if c.get("applied", True):
            total_coeff *= c["value"]
            applied_coeffs_list.append(c)

    # 7. Получение курса валют ADY
    curr_display = get_formatted_currency_display()
    divider_rate = curr_display["divider_rate"]  # 0.79

    # 8. Итоговая формула расчета
    # Тариф в CHF = База CHF * Коэффициенты
    net_chf = round(base_tariff_chf * total_coeff, 2)
    # Тариф в USD = Тариф в CHF / 0.79
    net_usd = round(net_chf / divider_rate, 2)

    # 9. Формирование сносок и примечаний
    notes = []
    if weight_data["min_weight_norm"] > 0:
        notes.append(f"Применена минимальная норма загрузки {weight_data['min_weight_norm']} тонн для ГНГ {gng_code}.")
    if not is_private_wagon:
        notes.append("Вагон инвентарный (МПС) — понижающий коэффициент 0.85 не применяется.")

    # --------------------------------------------------------------------------
    # БЛОК 3: Сборка итогового словаря результатов по частям (Part 1, 2, 3)
    # --------------------------------------------------------------------------
    return {
        "part1": {
            "route": route_display,
            "shipment_type": shipment_type_display,
            "distance": f"{distance_km} км",
            "cargo_and_wagon": cargo_and_wagon_display,
            "weight_info": weight_info_display,
            "period": "2026"
        },
        "part2": {
            "exchange_rate": curr_display["display_chf_usd"],
            "base_tariff": f"{base_tariff_chf:.2f} CHF",
            "coefficients": applied_coeffs_list
        },
        "part3": {
            "formula": f"({base_tariff_chf:.2f} CHF * {total_coeff:.4f}) / {divider_rate} = {net_usd:.2f} USD",
            "net_ady_rate": f"{net_usd:.2f} USD ({net_chf:.2f} CHF)",
            "notes": notes
        }
    }

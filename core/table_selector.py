# ==============================================================================
# МОДУЛЬ ВЫБОРА ТАРИФНОЙ ТАБЛИЦЫ И КОЛОНКИ ADY 2026
# ==============================================================================
import re

# ------------------------------------------------------------------------------
# БЛОК 1: Вспомогательная функция определения колонок для наливных грузов (Таблица 6)
# ------------------------------------------------------------------------------
def get_table_6_column(gng_code: str, is_private_tank: bool = False) -> int:
    """Определяет номер колонки (2-8) в Таблице 6 по коду ГНГ."""
    code = re.sub(r'\D', '', str(gng_code or ""))
    if not code:
        return 7

    if is_private_tank and (
        code.startswith(("27071", "27072", "27073", "290211", "29022", "29023", "29026", "29027", "29029"))
        or code.startswith(("290241", "290242", "290243", "290244"))
    ):
        return 8

    col2_prefixes = ("27090010", "27090090", "2710", "2712", "2713", "27149000", "2715", "340319", "340399", "3404", "381121", "381129", "38170050", "38241000")
    if code.startswith(col2_prefixes):
        return 2

    if code.startswith(("2705", "2711")):
        return 3

    col4_prefixes = ("27071", "27072", "27073", "27074", "27075", "27079920", "28011", "28013000", "28013010", "28041", "28042", "28043", "28044", "28112100", "28121100", "28141", "28539030", "2901", "2902", "29321200", "29333100", "29333955", "3817")
    if code.startswith(col4_prefixes):
        return 4

    col5_prefixes = ("1520", "270779980", "2905", "2906", "2907", "2908", "29094100", "29321300", "3820", "38237", "3826", "39053")
    if code.startswith(col5_prefixes):
        return 5

    col6_prefixes = ("0401", "040320", "040390", "040410", "0405", "0406", "1501", "1502", "1503", "1504", "1505", "1506", "151610", "151790", "2009", "2105", "2201", "2202", "2203", "2204", "2205", "2206")
    if code.startswith(col6_prefixes):
        return 6

    return 7


# ------------------------------------------------------------------------------
# БЛОК 2: Основная функция выбора тарифной таблицы и номера колонки
# ------------------------------------------------------------------------------
def select_tariff_table(
    wagon_category: str, 
    shipment_type: str, 
    is_empty_inventory: bool = False, 
    gng_code: str = "",
    fact_weight: float = 0.0,
    is_medium_container: bool = False,
    container_tonnage: int = 3,
    is_container_empty: bool = False
) -> dict:
    """
    Определяет номер тарифной таблицы (3, 4, 5, 6, 7) и номер колонки ADY 2026.
    """
    if is_empty_inventory:
        return {"table": "FREE_INVENTORY", "column": 1}

    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    w_type = str(wagon_category or "").strip().lower()

    if clean_gng == "99910000" or "passenger" in w_type or "пассажир" in w_type:
        return {"table": "7", "column": 6}

    if is_medium_container:
        if not is_container_empty:
            col = 7 if container_tonnage == 3 else 8
        else:
            col = 9 if container_tonnage == 3 else 10
        return {"table": "7", "column": col}

    if any(k in w_type for k in ["цистерна", "tank", "çənd", "bunker", "бункер"]):
        col_num = get_table_6_column(gng_code)
        return {"table": "6", "column": col_num}

    if "two_tier_car_platform" in w_type or "двухъярусная" in w_type or "ikimərtəbəli" in w_type:
        return {"table": "5", "column": 6}

    if any(k in w_type for k in ["autocar", "car_transporter", "автовоз", "автомобилевоз"]):
        col = 4 if fact_weight <= 0 else 2
        return {"table": "5", "column": col}

    if any(k in w_type for k in ["ref_section", "ref", "arv", "арв", "реф", "thermos", "термос"]):
        if "thermos" in w_type or "термос" in w_type:
            col = 4 if fact_weight < 25.0 else 5
            return {"table": "5", "column": col}
        else:
            col = 2 if fact_weight < 25.0 else 3
            return {"table": "5", "column": col}

    mode = str(shipment_type or "").strip().lower()
    is_transit = any(k in mode for k in ["tranzit", "transit", "транзит"])

    if is_transit:
        return {"table": "4", "column": 1}
    else:
        return {"table": "3", "column": 1}


# ------------------------------------------------------------------------------
# БЛОК 3: Адаптер (вынесен на верхний уровень файла)
# ------------------------------------------------------------------------------
def select_tariff_table_and_column(
    gng_code: str = "",
    wagon_type: str = "universal",
    shipment_type: str = "transit",
    is_empty_wagon: bool = False,
    is_empty_inventory: bool = False,
    fact_weight: float = 0.0,
    wagon_axles: int = 4
) -> dict:
    """
    Адаптер вызова выбора тарифной таблицы для calculator.py.
    """
    empty_flag = is_empty_inventory or is_empty_wagon
    res = select_tariff_table(
        wagon_category=wagon_type,
        shipment_type=shipment_type,
        is_empty_inventory=empty_flag,
        gng_code=gng_code,
        fact_weight=fact_weight
    )

    return {
        "table_number": str(res.get("table", "5")),
        "column": res.get("column", 1)
    }

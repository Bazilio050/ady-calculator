# ------------------------------------------------------------------------------
# БЛОК 1: Централизованный модуль локализации и переводов ADY 2026
# ------------------------------------------------------------------------------

# Переводы видов перевозок
SHIPMENT_TYPES_LANG = {
    "TRANSIT": {"AZ": "Tranzit", "RU": "Транзит", "EN": "Transit"},
    "IMPORT": {"AZ": "İdxal", "RU": "Импорт", "EN": "Import"},
    "EXPORT": {"AZ": "İxrac", "RU": "Экспорт", "EN": "Export"},
    "LOCAL": {"AZ": "Daxili", "RU": "Местное", "EN": "Local"}
}

# Переводы типов вагонов
WAGON_TYPES_LANG = {
    "universal": {"AZ": "Universal vaqon", "RU": "Универсальный вагон", "EN": "Universal wagon"},
    "covered": {"AZ": "Örtülü vaqon", "RU": "Крытый вагон", "EN": "Covered wagon"},
    "open": {"AZ": "Yarımvaqon", "RU": "Полувагон", "EN": "Gondola wagon"},
    "platform": {"AZ": "Platforma", "RU": "Платформа", "EN": "Flatcar"},
    "fitting_platform": {"AZ": "Fiting platforması", "RU": "Фитинговая платформа", "EN": "Fitting flatcar"},
    "cistern": {"AZ": "Çən vaqonu", "RU": "Цистерна", "EN": "Tank wagon"},
    "tank": {"AZ": "Çən vaqonu", "RU": "Цистерна", "EN": "Tank wagon"},
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

# Шаблоны веса и единиц измерения
WEIGHT_TRANSLATIONS = {
    "RU": {"unit": "т", "calc_label": "расчетный", "empty": "0 т (Порожний)"},
    "EN": {"unit": "t", "calc_label": "billable", "empty": "0 t (Empty)"},
    "AZ": {"unit": "t", "calc_label": "hesablama", "empty": "0 t (Boş)"}
}

# ------------------------------------------------------------------------------
# БЛОК 2: Универсальные функции получения переводов
# ------------------------------------------------------------------------------
def get_shipment_type_name(shipment_type: str, lang: str = "AZ") -> str:
    key = str(shipment_type or "").upper()
    current_lang = str(lang or "AZ").upper()
    return SHIPMENT_TYPES_LANG.get(key, {}).get(current_lang, key)

def get_wagon_type_name(wagon_type: str, lang: str = "AZ") -> str:
    key = str(wagon_type or "").lower()
    current_lang = str(lang or "AZ").upper()
    return WAGON_TYPES_LANG.get(key, {}).get(current_lang, key)

def format_weight_string(fact_w: float, chargeable: float, min_norm: float, lang: str = "AZ") -> str:
    """
    Форматирует строку веса без дробей (.0) для чистой отображаемости в UI.
    """
    current_lang = str(lang or "AZ").upper()
    tr = WEIGHT_TRANSLATIONS.get(current_lang, WEIGHT_TRANSLATIONS["AZ"])
    
    # Округляем до целых тонн
    fact_int = int(round(fact_w))
    chargeable_int = int(round(chargeable))
    
    if min_norm > 0 and fact_w < min_norm:
        return f"{fact_int} {tr['unit']} ({tr['calc_label']}: {chargeable_int} {tr['unit']})"
    else:
        return f"{fact_int} {tr['unit']}" if fact_int > 0 else f"{chargeable_int} {tr['unit']}"

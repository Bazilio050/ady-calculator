# ==============================================================================
# МОДУЛЬ РАСЧЕТА ТАРИФНЫХ КОЭФФИЦИЕНТОВ ADY 2026 (СТРОГИЙ ПОРЯДОК И QEYDLƏR)
# ==============================================================================
import re

# ------------------------------------------------------------------------------
# БЛОК 1: Справочник названий и примечаний к коэффициентам (UI DICTIONARY)
# ------------------------------------------------------------------------------
COEFF_LABELS = {
    "ref_section": {
        "AZ": "Refseksiya tərkib əmsalı ({count} vaqon)",
        "RU": "Коэффициент состава рефсекции ({count} вагонов)",
        "EN": "Refrigerated section composition factor ({count} wagons)",
        "note_az": "Refseksiyanın tərkibindəki yük vaqonlarının sayından asılı olaraq əmsal tətbiq olunmuşdur.",
        "note_ru": "Применен коэффициент в зависимости от количества грузовых вагонов в составе рефсекции.",
        "note_en": "Factor applied depending on the number of cargo wagons in the refrigerated section."
    },
    "fresh_produce": {
        "AZ": "Meyvə-tərəvəz güzəştı (Tarif Razılaşması ölkələri)",
        "RU": "Скидка на овощи/фрукты (страны Тарифного Соглашения)",
        "EN": "Fruit/vegetable discount (Tariff Agreement countries)",
        "note_az": "Tarif Razılaşması iştirakçısı olan ölkələrin mənşəli təzə meyvə-tərəvəz daşınmasına 0.60 güzəşt əmsalı tətbiq edilmişdir.",
        "note_ru": "Применен скидочный коэффициент 0.60 на перевозку свежих овощей и фруктов происхождения стран Тарифного Соглашения.",
        "note_en": "Discount coefficient of 0.60 applied for fresh fruits and vegetables originating from Tariff Agreement countries."
    },
    "loaded_wagon": {
        "AZ": "Yüklü vaqonlar üçün əlavə əmsal",
        "RU": "Дополнительный коэффициент для груженых вагонов",
        "EN": "Additional coefficient for loaded wagons",
        "note_az": "Yüklü vaqonların daşınmasına 1.015 əlavə əmsalı (indeksasiya) tətbiq olunmuşdur (01.03.2026 - 31.12.2026).",
        "note_ru": "Применен дополнительный коэффициент (индексация) 1.015 для перевозки груженых вагонов (01.03.2026 - 31.12.2026).",
        "note_en": "Additional coefficient (indexation) 1.015 applied for loaded wagon shipments (01.03.2026 - 31.12.2026)."
    },
    "private_wagon": {
        "AZ": "Xüsusi (SPS) vaqonlar üçün güzəşt əmsalı",
        "RU": "Коэффициент собственных/приватных вагонов",
        "EN": "Private (SPS) wagon discount coefficient",
        "note_az": "Xüsusi mülkiyyətdə olan (SPS) vaqonlara 0.85 güzəşt əmsalı tətbiq edilmişdir.",
        "note_ru": "К вагонам собственной (приватной) собственности (СПС) применен скидочный коэффициент 0.85.",
        "note_en": "Discount coefficient of 0.85 applied for private (SPS) wagons."
    },
    "long_platform": {
        "AZ": "Uzunluğu 19m-dən çox olan platformalar üçün əmsal",
        "RU": "Коэффициент для платформ длиннее 19м (п. 3.1.2.7)",
        "EN": "Coefficient for platforms over 19m (p. 3.1.2.7)",
        "note_az": "Bazasının uzunluğu 19 metrdən çox olan uzunölçülü platformalara 1.20 əmsalı tətbiq edilmişdir (bənd 3.1.2.7).",
        "note_ru": "Применен коэффициент 1.20 для длиннобазных платформ с длиной базы более 19 метров (п. 3.1.2.7).",
        "note_en": "Coefficient 1.20 applied for long-platform wagons exceeding 19m base length (clause 3.1.2.7)."
    },
    "two_tier_car_platform_discount": {
        "AZ": "İkimərtəbəli platforma əmsalı",
        "RU": "Коэффициент двухъярусной платформы",
        "EN": "Two-tier platform coefficient",
        "note_az": "Avtomobil taşıyan ikimərtəbəli platformalarda yüklərin daşınmasına 0.80 əmsalı tətbiq edilmişdir.",
        "note_ru": "Применен коэффициент 0.80 для перевозки грузов на двухъярусных платформах-автомобилевозах.",
        "note_en": "Coefficient 0.80 applied for cargo transportation on two-tier car-carrying platforms."
    },
    "import_export_150": {
        "AZ": "İdxal / İxrac əmsalı",
        "RU": "Коэффициент импорт/экспорт",
        "EN": "Import / Export coefficient",
        "note_az": "İdxal və ya ixrac rejimində daşınan yüklərə 1.50 əmsalı tətbiq edilmişdir.",
        "note_ru": "Применен коэффициент 1.50 для грузов, перевозимых в режиме импорта или экспорта.",
        "note_en": "Coefficient 1.50 applied for cargo transported in import or export mode."
    },
    "wood_metal_import": {
        "AZ": "Meşə və ya metal yükləri üçün əmsal (İdxal)",
        "RU": "Специальный коэффициент для леса/металла (Импорт)",
        "EN": "Special coefficient for timber/metal (Import)",
        "note_az": "İdxal daşımaları zamanı meşə materiallarına və ya qara metallara 1.04 əmsalı tətbiq olunmuşdur.",
        "note_ru": "При импортных перевозках лесоматериалов или черных металлов применен коэффициент 1.04.",
        "note_en": "Coefficient 1.04 applied for import shipments of timber or ferrous metals."
    },
    "non_ferrous_metal": {
        "AZ": "Əlvan metallar üçün artırıcı əmsal",
        "RU": "Повышающий коэффициент для цветных металлов (стр. 18)",
        "EN": "Surcharge coefficient for non-ferrous metals (p. 18)",
        "note_az": "Əlvan metallar və onların ərintilərinin daşınmasına 1.20 artırıcı əmsalı tətbiq olunmuşdur.",
        "note_ru": "Применен повышающий коэффициент 1.20 для перевозок цветных металлов и их сплавов.",
        "note_en": "Surcharge coefficient of 1.20 applied for non-ferrous metals and alloys."
    },
    "transit_alat_bk": {
        "AZ": "Tranzit əmsalı (Ələt - Böyük Kəsik)",
        "RU": "Транзитный коэффициент (Алят - Беюк Кясик)",
        "EN": "Transit coefficient (Alat - Boyuk Kasik)",
        "note_az": "Ələt - Böyük Kəsik istiqamətində tranzit daşımalara 1.20 əmsalı tətbiq olunmuşdur.",
        "note_ru": "Применен транзитный коэффициент 1.20 для перевозок по маршруту Алят - Беюк Кясик.",
        "note_en": "Transit coefficient of 1.20 applied for shipments on the Alat - Boyuk Kasik route."
    },
    "oil_products": {
        "AZ": "Neft və neft məhsulları üçün əmsal",
        "RU": "Специальный коэффициент для нефти/нефтепродуктов",
        "EN": "Special coefficient for oil and petroleum products",
        "note_az": "Neft və neft məhsullarının İdxal/Tranzit daşınmasına 1.20 əmsalı tətbiq olunmuşdur.",
        "note_ru": "Применен специальный коэффициент 1.20 для импорта и транзита нефти и нефтепродуктов.",
        "note_en": "Special coefficient of 1.20 applied for import and transit of crude oil and petroleum products."
    },
    "ref_transit": {
        "AZ": "Refrijerator vaqonları üçün tranzit əmsalı",
        "RU": "Специальный коэффициент для рефрижераторного подвижного состава",
        "EN": "Special transit coefficient for refrigerated wagons",
        "note_az": "Refrijerator vaqonları ilə tranzit daşımalara 1.20 əmsalı tətbiq edilmişdir.",
        "note_ru": "Применен коэффициент 1.20 для транзитных перевозок в рефрижераторных вагонах.",
        "note_en": "Special coefficient 1.20 applied for transit shipments in refrigerated wagons."
    }
}

# ------------------------------------------------------------------------------
# БЛОК 2: Вспомогательная функция определения цветных металлов
# ------------------------------------------------------------------------------
def is_special_non_ferrous_metal(gng_code: str) -> bool:
    """Проверяет принадлежность кода ГНГ к категории цветных металлов."""
    code = re.sub(r'\D', '', str(gng_code or ""))
    if not code:
        return False

    exact_codes = {"28045090", "28049", "28054", "32121", "7115", "8302", "83079", "8309", "8311", "85481"}
    if code in exact_codes:
        return True

    if any(code.startswith(str(c)) for c in range(7106, 7113)):
        return True
    if code.startswith("74") and not code.startswith(("7401", "7418")):
        return True
    if code.startswith("75") and not code.startswith("7501"):
        return True
    if code.startswith("76") and not code.startswith("7615"):
        return True
    if code.startswith(("78", "79", "80")):
        return True
    if code.startswith("81") and not code.startswith("81052"):
        return True

    return False

# ------------------------------------------------------------------------------
# БЛОК 3: Вспомогательная функция определения коэффициента рефсекции
# ------------------------------------------------------------------------------
def get_ref_section_coefficient(ref_cars_count: int) -> tuple[float, int]:
    """Возвращает коэффициент рефсекции в зависимости от количества грузовых вагонов."""
    count = int(ref_cars_count or 4)
    if count in [1, 2, 3]:
        coeff_map = {1: 1.7, 2: 1.4, 3: 1.1}
        return coeff_map[count], count
    elif count >= 5:
        return 0.85, count
    return 1.0, count

# ------------------------------------------------------------------------------
# БЛОК 4: Основная функция расчета всех применимых коэффициентов
# ------------------------------------------------------------------------------
def get_applicable_coefficients(
    shipment_type: str,
    gng_code: str,
    table_number: str = "5",
    wagon_type: str = "",
    from_station: str = "",
    to_station: str = "",
    is_loaded: bool = True,
    is_private_wagon: bool = False,
    ref_cars_count: int = None,
    apply_fresh_produce_discount: bool = False,
    is_long_platform_over_19m: bool = False,
    is_tariff_agreement_member: bool = False,
    lang: str = "AZ"
) -> dict:
    """Собирает список всех применимых коэффициентов и итоговый множитель."""
    mode = str(shipment_type or "").strip().lower()
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    table_str = str(table_number or "").strip()
    wagon_lower = str(wagon_type or "").lower()
    l_code = lang.upper() if lang in ["AZ", "RU", "EN"] else "AZ"
    
    is_export = any(k in mode for k in ["ixrac", "export", "экспорт"])
    is_import = any(k in mode for k in ["idxal", "import", "импорт"])
    is_transit = any(k in mode for k in ["tranzit", "transit", "транзит"])

    coeffs = []

    def add_coeff(key: str, val: float, **kwargs):
        cfg = COEFF_LABELS[key]
        name_template = cfg.get(l_code, cfg["AZ"])
        note_text = cfg.get(f"note_{l_code.lower()}", cfg["note_az"])
        
        coeffs.append({
            "name": name_template.format(**kwargs),
            "value": val,
            "note": note_text,
            "applied": True
        })

    # (A) Схема состава рефсекции
    if "ref" in wagon_lower or "реф" in wagon_lower or "seksiy" in wagon_lower:
        coeff, count = get_ref_section_coefficient(ref_cars_count)
        if coeff != 1.0:
            add_coeff("ref_section", coeff, count=count)

    # (B) Двухъярусная платформа-автомобилевоз (коэффициент 0.80)
    if "two_tier_car_platform" in wagon_lower or "двухъярусная" in wagon_lower or "ikimərtəbəli" in wagon_lower:
        add_coeff("two_tier_car_platform_discount", 0.80)

    # (C) Скидка на плодоовощную продукцию (0.60)
    is_fresh_produce = clean_gng.startswith(("04100", "04200", "04300", "04400", "05100", "05200", "05300", "0701", "0702", "0703", "0704", "0705", "0706", "0707", "0708", "0709", "0710", "0803", "0804", "0805", "0806", "0807", "0808", "0809", "0810", "12129100"))
    if (is_fresh_produce or apply_fresh_produce_discount) and is_tariff_agreement_member:
        add_coeff("fresh_produce", 0.60)

    # (D) Индексация груженых вагонов (1.015) и приватный парк (0.85)
    if is_loaded:
        add_coeff("loaded_wagon", 1.015)

    if is_private_wagon:
        add_coeff("private_wagon", 0.85)

    # (E) Длиннобазные платформы более 19 метров (1.20)
    if is_long_platform_over_19m:
        add_coeff("long_platform", 1.20)

    # (F) Импорт / Экспорт общий коэффициент (1.50)
    is_wood = clean_gng.startswith(("4403", "4404")) or any(clean_gng.startswith(f"44{i:02d}") for i in range(7, 14))
    is_black_metal = clean_gng.startswith("72") or any(clean_gng.startswith(f"730{i}") for i in range(1, 8))

    if shipment_type.lower() in ["import", "export", "idxal", "ixrac", "импорт", "экспорт"]:
        is_table_3_exempt = (str(table_number) == "3")
        is_universal = any(w in wagon_lower for w in ["universal", "универсаль", "крытый", "полувагон", "платформа"])
        is_wood_exempt = is_universal and is_wood
        is_metal_exempt = is_universal and is_black_metal

        is_methanol = ("290511" in clean_gng or "метанол" in wagon_lower or "methanol" in wagon_lower)
        is_tank_or_bunker = any(w in wagon_lower for w in ["tank", "cistern", "цистерн", "bunker", "бункер"])
        is_methanol_exempt = is_methanol and is_tank_or_bunker

        is_oil_table6_exempt = (str(table_number) == "6")

        if not (is_table_3_exempt or is_wood_exempt or is_metal_exempt or is_methanol_exempt or is_oil_table6_exempt):
            add_coeff("import_export_150", 1.50)

    # (G) Специальные номенклатурные коэффициенты (Лес, Металлы)
    if is_import and (is_wood or is_black_metal):
        add_coeff("wood_metal_import", 1.04)

    if is_special_non_ferrous_metal(clean_gng):
        add_coeff("non_ferrous_metal", 1.20)

    # (H) Правило "BIR DƏFƏ" для коэффициента 1.20
    has_120_applied = False

    if (is_import or is_transit) and table_str == "6":
        add_coeff("oil_products", 1.20)
        has_120_applied = True

    is_ref = any(k in wagon_lower for k in ["arv", "рефрижератор", "ref", "seksiy"])
    if is_transit and is_ref and not has_120_applied:
        add_coeff("ref_transit", 1.20)
        has_120_applied = True

    st_from = str(from_station or "").strip().lower()
    st_to = str(to_station or "").strip().lower()
    is_alat = any(k in st_from or k in st_to for k in ["alat", "ələt", "алят"])
    is_bk = any(k in st_from or k in st_to for k in ["boyuk kesik", "böyük kəsik", "беюк-кесик", "беюк кесик"])
    
    if is_transit and (is_alat and is_bk) and not has_120_applied:
        add_coeff("transit_alat_bk", 1.20)
        has_120_applied = True

    # Сортировка порядка вывода
    def get_coeff_priority(c):
        val = c.get("value")
        if val == 0.85:
            return 99
        elif val == 1.015:
            return 98
        return 1

    coeffs.sort(key=get_coeff_priority)

    total_multiplier = 1.0
    for c in coeffs:
        total_multiplier *= c["value"]

    return {
        "coefficients_list": coeffs,
        "total_multiplier": round(total_multiplier, 6)
    }

# ------------------------------------------------------------------------------
# БЛОК 5: Адаптер для совместимости с calculator.py
# ------------------------------------------------------------------------------
def get_all_coefficients(
    gng_code: str = "",
    wagon_type: str = "universal",
    shipment_type: str = "transit",
    is_private_wagon: bool = False,
    is_round_trip: bool = False,
    wagon_axles: int = 4
) -> list[dict]:
    """Адаптер вызова коэффициентов для calculator.py."""
    res = get_applicable_coefficients(
        shipment_type=shipment_type,
        gng_code=gng_code,
        wagon_type=wagon_type,
        is_private_wagon=is_private_wagon
    )
    return res["coefficients_list"]

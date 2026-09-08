# core/main_rules.py

from typing import List, Dict, Any


def check_gng_match(gng_code: str, target: str) -> bool:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Проверяет соответствие ГНГ кода указанному образцу из правил.
    """
    clean_gng = str(gng_code).strip()
    clean_target = str(target).strip()
    return clean_gng.startswith(clean_target)


def check_precious_metals_multiplier(gng_code: str) -> bool:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Проверяет, входит ли код ГНГ в перечень цветных, драгоценных металлов 
    и специфических грузов из пункта 3.1.1.
    """
    gng = str(gng_code).strip()

    # Точные совпадения по кодам ГНГ
    exact_codes = {"28045090", "28049", "28054", "32121", "8302", "83079", "8309", "8311", "85481"}
    if any(gng.startswith(code) for code in exact_codes):
        return True

    # Драгоценные металлы: диапазон 7106-7112 и код 7115
    if any(gng.startswith(f"71{i:02d}") for i in range(6, 13)) or gng.startswith("7115"):
        return True

    # Группы цветных металлов с учетом исключений
    if gng.startswith("74") and not (gng.startswith("7401") or gng.startswith("7418")):
        return True
    if gng.startswith("75") and not gng.startswith("7501"):
        return True
    if gng.startswith("76") and not gng.startswith("7615"):
        return True
    if gng.startswith("78") or gng.startswith("79") or gng.startswith("80"):
        return True
    if gng.startswith("81") and not gng.startswith("81052"):
        return True

    return False


def apply_main_rules(
    shipment_type: str,           # 'import', 'export', 'transit', 'local'
    gng_code: str,                # Полный код ГНГ
    wagon_type: str,              # Тип вагона
    from_canonical_name: str,     # Каноническое имя станции отправления
    to_canonical_name: str,       # Каноническое имя станции назначения
    is_table_3: bool = False,     # Флаг: расчет выполняется строго по Таблице 3
    is_methanol: bool = False,    # Флаг: является ли груз метанолом
    is_oil_product: bool = False, # Флаг: нефть/нефтепродукты (Таблица 6, столбец 2)
    is_empty: bool = False,       # Флаг: порожний возврат вагона
    is_private_wagon: bool = False # Флаг: собственный/приватный вагон (СПС)
) -> Dict[str, Any]:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Расчет коэффициентов по Главным (сквозным) правилам Тарифного руководства ADY.
    """
    applied_rules: List[Dict[str, Any]] = []
    final_coeff: float = 1.0

    gng = str(gng_code).strip()
    shipment = str(shipment_type).lower().strip()

    # Проверка условий групп кодов ГНГ
    is_wood_group = any(
        check_gng_match(gng, code) 
        for code in ["4403", "4404", "4407", "4408", "4409", "4410", "4411", "4412", "4413"]
    )
    
    is_metal_group = check_gng_match(gng, "72") or any(
        check_gng_match(gng, code) 
        for code in ["7301", "7302", "7303", "7304", "7305", "7306", "7307"]
    )

    # --------------------------------------------------------------------------
    # ПРАВИЛО 1: Коэффициент 1.50 на Импорт и Экспорт (с учетом исключений)
    # --------------------------------------------------------------------------
    if shipment in ["import", "export"]:
        # Исключение срабатывает строго для Таблицы 3 и перечисленных специфических грузов
        is_exception = (
            is_table_3
            or is_wood_group
            or is_metal_group
            or (is_methanol and wagon_type in ["tank", "bunker"])
            or (is_oil_product and wagon_type == "tank")
        )

        if not is_exception:
            final_coeff *= 1.50
            applied_rules.append({
                "calculated_value": 1.50,
                "rule_code": "MAIN_COEFF_1_50_IMPORT_EXPORT",
                "params": {"shipment_type": shipment, "gng_code": gng}
            })

    # --------------------------------------------------------------------------
    # ПРАВИЛО 2: Коэффициент 1.04 для Импорта леса и металлов
    # --------------------------------------------------------------------------
    if shipment == "import" and (is_wood_group or is_metal_group):
        final_coeff *= 1.04
        applied_rules.append({
            "calculated_value": 1.04,
            "rule_code": "MAIN_COEFF_1_04_IMPORT_WOOD_METAL",
            "params": {"gng_code": gng}
        })

    # --------------------------------------------------------------------------
    # ПРАВИЛО 3: Коэффициент 1.20 для транзита Алят — Беюк-Кесик — Алят
    # --------------------------------------------------------------------------
    alat_border_names = {
        "Ələt-eksp.",
        "Ələt eksport-Kurik",
        "Ələt eksport-Türk.",
        "Ələt eksport-Aktau",
    }
    boyuk_kesik_names = {
        "Böyük Kəsik",
        "Böyük Kəsik (eksport)"
    }

    is_alat_route = (
        (from_canonical_name in boyuk_kesik_names and to_canonical_name in alat_border_names) or
        (from_canonical_name in alat_border_names and to_canonical_name in boyuk_kesik_names)
    )

    if shipment == "transit" and is_alat_route:
        final_coeff *= 1.20
        applied_rules.append({
            "calculated_value": 1.20,
            "rule_code": "MAIN_COEFF_1_20_TRANSIT_ALAT",
            "params": {"from": from_canonical_name, "to": to_canonical_name}
        })

    # --------------------------------------------------------------------------
    # ПРАВИЛО 4: Коэффициент 1.20 на Нефтепродукты в цистернах (Однократно)
    # --------------------------------------------------------------------------
    if shipment in ["import", "transit"] and is_oil_product and wagon_type in ["tank", "bunker"]:
        if not any(rule["calculated_value"] == 1.20 for rule in applied_rules):
            final_coeff *= 1.20
            applied_rules.append({
                "calculated_value": 1.20,
                "rule_code": "MAIN_COEFF_1_20_OIL_TANK",
                "params": {"shipment_type": shipment, "wagon_type": wagon_type}
            })

    # --------------------------------------------------------------------------
    # ПРАВИЛО 5: Коэффициент 1.20 для Рефрижераторов при транзите (Однократно)
    # --------------------------------------------------------------------------
    if shipment == "transit" and wagon_type in ["ref_section", "ref_container", "arv"]:
        if not any(rule["calculated_value"] == 1.20 for rule in applied_rules):
            final_coeff *= 1.20
            applied_rules.append({
                "calculated_value": 1.20,
                "rule_code": "MAIN_COEFF_1_20_REFRIGERATOR_TRANSIT",
                "params": {"wagon_type": wagon_type}
            })

    # --------------------------------------------------------------------------
    # ПРАВИЛО 6: Коэффициент 1.20 для цветных и драгоценных металлов (п. 3.1.1)
    # --------------------------------------------------------------------------
    if check_precious_metals_multiplier(gng):
        final_coeff *= 1.20
        applied_rules.append({
            "calculated_value": 1.20,
            "rule_code": "MAIN_COEFF_1_20_PRECIOUS_METALS",
            "params": {"gng_code": gng}
        })

    # --------------------------------------------------------------------------
    # ПРАВИЛО 7: Коэффициент 1.015 на груженые международные перевозки (2026)
    # --------------------------------------------------------------------------
    if shipment in ["import", "export", "transit"] and not is_empty:
        final_coeff *= 1.015
        applied_rules.append({
            "calculated_value": 1.015,
            "rule_code": "MAIN_COEFF_1_015_INTERNATIONAL_LOADED",
            "params": {"shipment_type": shipment, "is_empty": is_empty}
        })

    # --------------------------------------------------------------------------
    # ПРАВИЛО 8: Коэффициент 0.85 на собственные (приватные) вагоны
    # --------------------------------------------------------------------------
    if is_private_wagon:
        final_coeff *= 0.85
        applied_rules.append({
            "calculated_value": 0.85,
            "rule_code": "MAIN_COEFF_0_85_PRIVATE_WAGON",
            "params": {"is_private_wagon": is_private_wagon}
        })

    return {
        "calculated_value": round(final_coeff, 4),
        "rules": applied_rules
    }

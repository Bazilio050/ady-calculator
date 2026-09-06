# core/main_rules.py

from typing import List, Dict, Any


def check_gng_match(gng_code: str, target: str) -> bool:
    """
    Проверяет соответствие ГНГ кода указанному образцу из правил:
    - Если в правиле 2-значный код (например, '72'), проверяется совпадение первых 2 цифр.
    - Если в правиле 4-значный код (например, '4403'), проверяется совпадение первых 4 цифр.
    """
    clean_gng = str(gng_code).strip()
    clean_target = str(target).strip()
    return clean_gng.startswith(clean_target)


def apply_main_rules(
    shipment_type: str,           # 'import', 'export', 'transit', 'local'
    gng_code: str,                # Полный код ГНГ
    wagon_type: str,              # 'tank', 'bunker', 'ref_section', 'ref_container', 'arv', 'other'
    from_canonical_name: str,     # Каноническое имя станции отправления из stations_mapping.py
    to_canonical_name: str,       # Каноническое имя станции назначения из stations_mapping.py
    is_table_3: bool = False,     # Флаг: выполняется ли расчет по Таблице 3
    is_methanol: bool = False,    # Флаг: является ли груз метанолом
    is_oil_product: bool = False  # Флаг: нефть/нефтепродукты (Таблица 6, столбец 2)
) -> Dict[str, Any]:
    """
    Расчет коэффициентов по Главным (сквозным) правилам Тарифного руководства ADY.
    Возвращает итоговый коэффициент и список сработавших правил.
    """
    applied_rules: List[Dict[str, Any]] = []
    final_coeff: float = 1.0

    gng = str(gng_code).strip()
    shipment = str(shipment_type).lower().strip()

    # --- ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ: Проверка условий кодов ГНГ по правилам ---
    # Лес и пиломатериалы: 4403, 4404, 4407-4413 (4-значные)
    is_wood_group = any(
        check_gng_match(gng, code) 
        for code in ["4403", "4404", "4407", "4408", "4409", "4410", "4411", "4412", "4413"]
    )
    
    # Черные металлы: 72 (2-значный) и 7301-7307 (4-значные)
    is_metal_group = check_gng_match(gng, "72") or any(
        check_gng_match(gng, code) 
        for code in ["7301", "7302", "7303", "7304", "7305", "7306", "7307"]
    )

    # --------------------------------------------------------------------------
    # ПРАВИЛО 1: Коэффициент 1.50 на Импорт и Экспорт (с учетом исключений)
    # --------------------------------------------------------------------------
    # --- ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ: Применяется 1.50 на импорт/экспорт, если нет исключений ---
    if shipment in ["import", "export"]:
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
    # --- ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ: При импорте указанных кодов леса и черных металлов применяется 1.04 ---
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
    # --- ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ: Повышающий 1.20 при транзите между Беюк-Кесик и портами Алят ---
    alat_border_names = {
        "Ələt eksport-Kurik",
        "Ələt eksport-Türk.",
        "Ələt eksport-Aktau"
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
    # --- ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ: 1.20 при импорте или транзите нефти/нефтепродуктов в цистернах ---
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
    # --- ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ: 1.20 при транзите реф-секций, реф-контейнеров и ИВ-термосов ---
    if shipment == "transit" and wagon_type in ["ref_section", "ref_container", "arv"]:
        if not any(rule["calculated_value"] == 1.20 for rule in applied_rules):
            final_coeff *= 1.20
            applied_rules.append({
                "calculated_value": 1.20,
                "rule_code": "MAIN_COEFF_1_20_REFRIGERATOR_TRANSIT",
                "params": {"wagon_type": wagon_type}
            })

    return {
        "calculated_value": round(final_coeff, 4),
        "rules": applied_rules
    }

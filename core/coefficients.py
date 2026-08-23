# ==============================================================================
# МОДУЛЬ РАСЧЕТА ТАРИФНЫХ КОЭФФИЦИЕНТОВ ADY 2026
# ==============================================================================
import re

def get_applicable_coefficients(
    shipment_type: str,
    gng_code: str,
    table_number: str,
    wagon_type: str = "",
    from_station: str = "",
    to_station: str = ""
) -> dict:
    """
    Вычисляет применимые коэффициенты на основе правил ADY 2026.
    """
    mode = str(shipment_type or "").strip().lower()
    clean_gng = re.sub(r'\D', '', str(gng_code or ""))
    table_str = str(table_number or "").strip()
    
    is_export = any(k in mode for k in ["ixrac", "export", "экспорт"])
    is_import = any(k in mode for k in ["idxal", "import", "импорт"])
    is_transit = any(k in mode for k in ["tranzit", "transit", "транзит"])

    coeffs = []
    
    # Флаги категорий грузов
    is_table_3 = (table_str == "3")
    is_wood = clean_gng.startswith(("4403", "4404", "4407", "4408", "4409", "4410", "4411", "4412", "4413"))
    is_black_metal = clean_gng.startswith("72") or any(clean_gng.startswith(str(code)) for code in range(7301, 7308))
    is_methanol = ("метанол" in wagon_type.lower() or "methanol" in wagon_type.lower())
    is_oil_tab6_col2 = (table_str == "6")  # Нефть и нефтепродукты

    # 1. Проверка исключений для коэффициента 1.50 (Импорт / Экспорт)
    excluded_from_1_50 = is_table_3 or is_wood or is_black_metal or is_methanol or is_oil_tab6_col2

    if (is_import or is_export) and not excluded_from_1_50:
        coeffs.append({"name": "Коэффициент импорт/экспорт", "value": 1.50})

    # 2. Коэффициент 1.04 для леса и черных металлов при Импорте
    if is_import and (is_wood or is_black_metal):
        coeffs.append({"name": "Специальный коэффициент для леса/металла (Импорт)", "value": 1.04})

    # 3. Коэффициент 1.20 для транзита Ələt — Böyük Kəsik (в обе стороны)
    st_from = str(from_station or "").strip().lower()
    st_to = str(to_station or "").strip().lower()
    
    is_alat = any(k in st_from or k in st_to for k in ["alat", "ələt", "алят"])
    is_bk = any(k in st_from or k in st_to for k in ["boyuk kesik", "böyük kəsik", "беюк-кесик", "беюк кесик"])
    
    route_via_alat_bk = is_alat and is_bk

    if is_transit and route_via_alat_bk:
        coeffs.append({"name": "Транзитный коэффициент (Ələt - Böyük Kəsik)", "value": 1.20})

    # 4. Коэффициент 1.20 для нефти и нефтепродуктов (Импорт или Транзит)
    if (is_import or is_transit) and is_oil_tab6_col2:
        coeffs.append({"name": "Специальный коэффициент для нефти/нефтепродуктов", "value": 1.20})

    # 5. Коэффициент 1.20 для ARV / рефрижераторов при Транзите
    is_ref = any(k in wagon_type.lower() for k in ["arv", "рефрижератор", "ref"])
    if is_transit and is_ref:
        coeffs.append({"name": "Специальный коэффициент для рефрижераторного подвижного состава", "value": 1.20})

    # Итоговый перемноженный коэффициент
    total_multiplier = 1.0
    for c in coeffs:
        total_multiplier *= c["value"]

    return {
        "coefficients_list": coeffs,
        "total_multiplier": round(total_multiplier, 4)
    }

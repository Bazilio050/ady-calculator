# ==============================================================================
# МОДУЛЬ РАСЧЕТА ТАРИФНЫХ КОЭФФИЦИЕНТОВ ADY 2026
# ==============================================================================
import re

def is_special_non_ferrous_metal(gng_code: str) -> bool:
    """
    Проверяет, входит ли код ГНГ в список цветных металлов со стр. 18 (коэф 1.20).
    """
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


def parse_ref_section_schema(schema_str: str) -> dict:
    """
    Разбирает схемы рефсекций вида '4+1', '1+4', '5+1', '1+6' и возвращает коэффициент.
    """
    if not schema_str:
        return {"coeff": 1.0, "cargo_wagons": 4}
    
    nums = [int(n) for n in re.findall(r'\d+', str(schema_str))]
    if len(nums) < 2:
        return {"coeff": 1.0, "cargo_wagons": 4}

    cargo_wagons = max(nums) if min(nums) == 1 else nums[0]

    if cargo_wagons in [1, 2, 3]:
        coeff_map = {1: 1.7, 2: 1.4, 3: 1.1}
        return {"coeff": coeff_map[cargo_wagons], "cargo_wagons": cargo_wagons}
    elif cargo_wagons >= 5:
        return {"coeff": 0.85, "cargo_wagons": cargo_wagons}
    
    return {"coeff": 1.0, "cargo_wagons": 4}


def get_applicable_coefficients(
    shipment_type: str,
    gng_code: str,
    table_number: str,
    wagon_type: str = "",
    from_station: str = "",
    to_station: str = "",
    is_loaded: bool = True,
    is_private_wagon: bool = True,
    ref_schema: str = "",
    is_tariff_agreement_member: bool = False
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
    is_table_5 = (table_str == "5")
    is_wood = clean_gng.startswith(("4403", "4404", "4407", "4408", "4409", "4410", "4411", "4412", "4413"))
    is_black_metal = clean_gng.startswith("72") or any(clean_gng.startswith(str(code)) for code in range(7301, 7308))
    is_methanol = ("метанол" in wagon_type.lower() or "methanol" in wagon_type.lower())
    is_oil_tab6_col2 = (table_str == "6")

    # 1. Схема состава рефсекции (1+3, 4+1, 5+1 и т.д.)
    if "ref" in wagon_type.lower() or "реф" in wagon_type.lower():
        ref_info = parse_ref_section_schema(ref_schema)
        if ref_info["coeff"] != 1.0:
            coeffs.append({
                "name": f"Коэффициент состава рефсекции ({ref_info['cargo_wagons']} вагонов)", 
                "value": ref_info["coeff"]
            })

    # 2. Скидка 0.60 на фрукты/овощи (только при явном указании в запросе)
    is_fresh_produce = clean_gng.startswith(("04100", "04200", "04300", "04400", "05100", "05200", "05300", "0701", "0702", "0703", "0704", "0705", "0706", "0707", "0708", "0709", "0710", "0803", "0804", "0805", "0806", "0807", "0808", "0809", "0810", "12129100"))
    if is_fresh_produce and is_tariff_agreement_member:
        coeffs.append({"name": "Скидка на овощи/фрукты (страны Тарифного Соглашения)", "value": 0.60})

    # 3. Дополнительный коэффициент 1.015 для всех груженых вагонов
    if is_loaded:
        coeffs.append({"name": "Дополнительный коэффициент для груженых вагонов", "value": 1.015})

    # 4. Коэффициент 0.85 для собственных (приватных) вагонов
    if is_private_wagon:
        coeffs.append({"name": "Коэффициент собственных/приватных вагонов", "value": 0.85})

    # 5. Проверка исключений для коэффициента 1.50 (Импорт / Экспорт)
    excluded_from_1_50 = is_table_3 or is_table_5 or is_wood or is_black_metal or is_methanol or is_oil_tab6_col2

    if (is_import or is_export) and not excluded_from_1_50:
        coeffs.append({"name": "Коэффициент импорт/экспорт", "value": 1.50})

    # 6. Коэффициент 1.04 для леса и черных металлов при Импорте
    if is_import and (is_wood or is_black_metal):
        coeffs.append({"name": "Специальный коэффициент для леса/металла (Импорт)", "value": 1.04})

    # 7. Повышающий коэффициент 1.20 для цветных металлов (стр. 18)
    if is_special_non_ferrous_metal(clean_gng):
        coeffs.append({"name": "Повышающий коэффициент для цветных металлов (стр. 18)", "value": 1.20})

    # 8. Коэффициент 1.20 для транзита Ələt — Böyük Kəsik (в обе стороны)
    st_from = str(from_station or "").strip().lower()
    st_to = str(to_station or "").strip().lower()
    
    is_alat = any(k in st_from or k in st_to for k in ["alat", "ələt", "алят"])
    is_bk = any(k in st_from or k in st_to for k in ["boyuk kesik", "böyük kəsik", "беюк-кесик", "беюк кесик"])
    
    if is_transit and (is_alat and is_bk):
        coeffs.append({"name": "Транзитный коэффициент (Ələt - Böyük Kəsik)", "value": 1.20})

    # 9. Коэффициент 1.20 для нефти и нефтепродуктов (Импорт или Транзит)
    if (is_import or is_transit) and is_oil_tab6_col2:
        coeffs.append({"name": "Специальный коэффициент для нефти/нефтепродуктов", "value": 1.20})

    # 10. Коэффициент 1.20 для ARV / рефрижераторов при Транзите
    is_ref = any(k in wagon_type.lower() for k in ["arv", "рефрижератор", "ref"])
    if is_transit and is_ref:
        coeffs.append({"name": "Специальный коэффициент для рефрижераторного подвижного состава", "value": 1.20})

    # Итоговый перемноженный коэффициент
    total_multiplier = 1.0
    for c in coeffs:
        total_multiplier *= c["value"]

    return {
        "coefficients_list": coeffs,
        "total_multiplier": round(total_multiplier, 6)
    }

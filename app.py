import math

# Коды цветных металлов и хим. веществ (п. 3.1.1 - коэффициент 1.20)
SPECIAL_METALS_GNG = {
    "28045090", "28049", "28054", "32121", "7115", 
    "8302", "83079", "8309", "8311", "85481"
}

# Коды свежих фруктов и овощей (п. 3.1.2.1 - коэффициент 0.60)
FRUITS_VEG_GNG = {
    "04100", "04200", "04300", "04400", "05100", "05200", "05300",
    "12129100"
}
FRUITS_VEG_PREFIXES = ("0701", "0702", "0703", "0704", "0705", "0706", "0707", "0708", "0709", "0710",
                       "0803", "0804", "0805", "0806", "0807", "0808", "0809", "0810")

def is_special_metal(gng_code: str) -> bool:
    """Проверка кода ГНГ (YHN) на попадание под повышающий коэффициент 1.20."""
    gng = str(gng_code).strip()
    if gng in SPECIAL_METALS_GNG:
        return True
    
    # Диапазоны 7106-7112
    if len(gng) >= 4 and gng[:4] in [str(x) for x in range(7106, 7113)]:
        return True
        
    # Группа 74 (кроме 7401, 7418)
    if gng.startswith("74") and not (gng.startswith("7401") or gng.startswith("7418")):
        return True
        
    # Группа 75 (кроме 7501)
    if gng.startswith("75") and not gng.startswith("7501"):
        return True
        
    # Группа 76 (кроме 7615)
    if gng.startswith("76") and not gng.startswith("7615"):
        return True
        
    # Группы 78, 79, 80, 81 (в 81 кроме 81052)
    if any(gng.startswith(p) for p in ["78", "79", "80"]) or (gng.startswith("81") and not gng.startswith("81052")):
        return True
        
    return False

def is_fruit_or_veg(gng_code: str) -> bool:
    """Проверка кода ГНГ (YHN) на фрукты/овощи для льготы 0.60 в рефвагонах."""
    gng = str(gng_code).strip()
    if gng in FRUITS_VEG_GNG:
        return True
    return any(gng.startswith(pref) for pref in FRUITS_VEG_PREFIXES)


def calculate_freight_tariff(
    shipment_type: str,     # 'import', 'export', 'transit'
    wagon_type: str,        # 'universal', 'ref_section', 'arv', 'thermos', 'autovoz', 'autovoz_2deck'
    weight_tons: float,     # Масса груза в тоннах
    distance_km: int,       # Расстояние транспортировки
    gng_code: str = "",     # Код ГНГ груза
    ref_composition: str = "1+4", # Состав рефсекции: "1+1", "1+2", "1+3", "1+4", "1+5", "1+6" и т.д.
    is_empty_return: bool = False, # Возврат порожнего инвентарного вагона
    mark: str = ""          # Отметки в накладной: 'IZVK', 'IZVT', 'VTVK'
) -> dict:
    
    # 1. Инвентарный порожний вагон (МПС), возвращаемый в страну принадлежности (п. 3.1.1)
    if is_empty_return and wagon_type == 'universal':
        return {"base_rate": 0.0, "total_chf": 0.0, "note": "Порожний возврат инвентарного вагона — без оплаты"}

    coeffs = []
    
    # 2. Обработка особых заменок (отметок в накладной)
    if mark == "IZVK":
        # Рефвагон вместо крытого универсального (расчетная масса не менее 40 тн)
        wagon_type = "universal"
        weight_tons = max(weight_tons, 40.0)
    elif mark == "VTVK":
        # Вагон-термос вместо крытого универсального (расчетная масса не менее 60 тн)
        wagon_type = "universal"
        weight_tons = max(weight_tons, 60.0)

    # 3. Выбор базовой таблицы и логика расчета
    if wagon_type == "universal":
        # Таблица 3 (Импорт/Экспорт) или Таблица 4 (Транзит)
        table_name = "Cadval_4" if shipment_type.lower() == "transit" else "Cadval_3"
        
        # Проверка коэффициента на цветные металлы и химикаты (1.20)
        if is_special_metal(gng_code):
            coeffs.append(("Спец. металлы/химия (п. 3.1.1)", 1.20))
            
    elif wagon_type in ["ref_section", "arv"]:
        table_name = "Cadval_5"
        
        # Коэффициенты от количества вагонов в секции (п. 3.1.2.1)
        if "+" in ref_composition:
            try:
                # Извлечение количества грузовых вагонов из "1+6" или "6+1"
                parts = [int(p) for p in ref_composition.split("+")]
                cargo_wagons = max(parts) if min(parts) == 1 else parts[0]
            except ValueError:
                cargo_wagons = 4
        else:
            cargo_wagons = 4

        if cargo_wagons == 1:
            coeffs.append(("Рефсекция 1+1", 1.70))
        elif cargo_wagons == 2:
            coeffs.append(("Рефсекция 1+2", 1.40))
        elif cargo_wagons == 3:
            coeffs.append(("Рефсекция 1+3", 1.10))
        elif cargo_wagons >= 5:
            coeffs.append((f"Рефсекция 1+{cargo_wagons} (>=5 вагонов)", 0.85))

        # Льгота 0.60 на фрукты и овощи
        if is_fruit_or_veg(gng_code):
            coeffs.append(("Фрукты/овощи Тарифного соглашения", 0.60))

    elif wagon_type == "thermos":
        table_name = "Cadval_5"
        
    elif wagon_type in ["autovoz", "autovoz_2deck"]:
        table_name = "Cadval_5"
        weight_tons = max(weight_tons, 10.0) # Мин. вес 10 тонн
        if wagon_type == "autovoz_2deck":
            coeffs.append(("Двухъярусная платформа-автовоз (п. 3.1.2.3)", 0.80))

    # Расчет итоговой суммы
    total_coeff = 1.0
    for name, val in coeffs:
        total_coeff *= val

    return {
        "table_used": table_name,
        "wagon_type": wagon_type,
        "calc_weight_tons": weight_tons,
        "applied_coefficients": coeffs,
        "total_multiplier": round(total_coeff, 4)
    }

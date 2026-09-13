# core/asco_calculator.py

from typing import Dict, Any, Optional

# Тарифные ставки ASCO в USD за 1 погонный метр длины вагона
ASCO_RATES = {
    "turkmenbashi": {
        "base": {"loaded": 45.0, "empty": 36.0},
        "oil_cistern": {"loaded": 70.0, "empty": 32.0, "fixed_length": 13.0},
        "oil_covered": {"loaded": 70.0, "empty": 36.0, "fixed_length": 15.0},
        "alcohol": {"loaded": 72.0, "empty": 36.0},
        "lpg": {"loaded": 119.0, "empty": 36.0},
        "dangerous": {"loaded": 50.0, "empty": 36.0},
        "export_az": {"loaded": 43.0, "empty": 36.0},
    },
    "kuryk": {
        "base": {"loaded": 50.0, "empty": 41.0},
        "oil_cistern": {"loaded": 83.0, "empty": 37.0, "fixed_length": 13.0},
        "oil_covered": {"loaded": 83.0, "empty": 41.0, "fixed_length": 15.0},
        "alcohol": {"loaded": 77.0, "empty": 41.0},
        "lpg": {"loaded": 135.0, "empty": 41.0},
        "dangerous": {"loaded": 55.0, "empty": 41.0},
        "export_az": {"loaded": 48.0, "empty": 41.0},
    }
}


def determine_asco_cargo_category(
    gng_code: str, 
    wagon_type: str, 
    shipment_type: str = "transit"
) -> str:
    """
    Автоматическое определение категории груза ASCO по ГНГ коду и типу вагона.
    """
    clean_gng = str(gng_code).strip()
    w_type = wagon_type.lower()
    ship_type = shipment_type.lower()

    # Нефть и нефтепродукты (ГНГ 2709, 2710)
    if clean_gng.startswith(("2709", "2710")):
        if w_type in ("cistern", "tank", "цистерна", "бункер", "bunker"):
            return "oil_cistern"
        elif w_type in ("covered", "крытый"):
            return "oil_covered"

    # Спирт, вина и алкогольная продукция (вся 22 группа ГНГ, кроме воды 2201 и напитков 2202)
    if clean_gng.startswith("22") and not clean_gng.startswith(("2201", "2202")):
        return "alcohol"

    # Сжиженный газ (ГНГ 2711)
    if clean_gng.startswith("2711"):
        return "lpg"

    # Экспорт из Азербайджана (неопасные грузы)
    if ship_type in ("export", "экспорт", "ixrac"):
        return "export_az"

    return "base"


class AscoFerryCalculator:
    """
    Центральный модуль расчета морского фрахта ASCO (Каспийское море).
    """

    @classmethod
    def calculate(
        cls,
        route_from: str,
        route_to: str,
        gng_code: str,
        wagon_type: str,
        shipment_type: str = "transit",
        wagon_length_m: float = 14.0,
        is_empty: bool = False,
        is_dangerous: bool = False,
        dangerous_class: Optional[int] = None,
        wagon_width_m: Optional[float] = None,
        is_locomotive: bool = False
    ) -> Dict[str, Any]:
        from_st = str(route_from).strip().lower()
        to_st = str(route_to).strip().lower()

        # Определение порта назначения
        if "трк" in from_st or "трк" in to_st or "туркменбаши" in from_st or "туркменбаши" in to_st:
            port_key = "turkmenbashi"
        elif "курык" in from_st or "курык" in to_st or "актау" in from_st or "актау" in to_st:
            port_key = "kuryk"
        else:
            return {
                "status": "NOT_APPLICABLE",
                "message": "Маршрут не содержит каспийских морских портов ASCO",
                "total_asco_usd": 0.0
            }

        # Определение категории груза по ГНГ и типу вагона
        cargo_category = determine_asco_cargo_category(gng_code, wagon_type, shipment_type)

        # ----------------------------------------------------------------------
        # Проверка опасных грузов: ТОЛЬКО ЕСЛИ ЯВНО УКАЗАНО В ЗАПРОСЕ
        # ----------------------------------------------------------------------
        if is_dangerous or dangerous_class is not None:
            # Классы 1, 2, 3, 7 требуют индивидуального согласования
            if dangerous_class in [1, 2, 3, 7] and cargo_category not in ["oil_cistern", "oil_covered", "alcohol", "lpg"]:
                return {
                    "status": "REQUIRES_AGREEMENT",
                    "message": f"Опасный груз (класс {dangerous_class}) требует индивидуального согласования тарифной ставки ASCO",
                    "total_asco_usd": 0.0
                }
            
            # Для остальных классов опасности (4, 5, 6, 8, 9) или если указан флаг is_dangerous=True
            if cargo_category == "base":
                cargo_category = "dangerous"

        rates_data = ASCO_RATES[port_key].get(cargo_category, ASCO_RATES[port_key]["base"])

        # Фиксированная длина для нефтяных грузов или ручной ввод
        calc_length = rates_data.get("fixed_length", wagon_length_m)
        state_key = "empty" if is_empty else "loaded"
        rate_per_meter = rates_data[state_key]

        # Расчет коэффициентов
        coeff = 1.0
        applied_coeffs = []

        # Вагоны длиной более 15 метров
        if calc_length > 15.0:
            coeff *= 1.3
            applied_coeffs.append({"code": "ASCO_LENGTH_OVER_15M", "coeff": 1.3})

        # Негабарит по ширине или локомотив
        if wagon_width_m and wagon_width_m >= 4.0:
            coeff *= 2.0
            applied_coeffs.append({"code": "ASCO_WIDTH_OVER_4M", "coeff": 2.0})
        elif (wagon_width_m and 3.25 <= wagon_width_m < 4.0) or is_locomotive:
            coeff *= 1.4
            applied_coeffs.append({"code": "ASCO_OVERSIZED_WIDTH_OR_LOCO", "coeff": 1.4})

        # Итоговый расчет фрахта: Длина * Ставка/метр * Коэффициент
        total_freight_usd = round(calc_length * rate_per_meter * coeff, 2)

        return {
            "status": "SUCCESS",
            "port": port_key,
            "cargo_category": cargo_category,
            "length_meters": calc_length,
            "rate_per_meter": rate_per_meter,
            "coeff": round(coeff, 4),
            "applied_coeffs": applied_coeffs,
            "total_asco_usd": total_freight_usd
        }

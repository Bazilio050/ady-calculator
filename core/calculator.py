# core/calculator.py

from typing import Dict, Any, Optional
from core.router import RailwayRouter
from core.tables.table_1_weight import Table1Calculator
from core.tables.table_min_load import TableMinLoadCalculator
from core.main_rules import apply_main_rules
from data.translations import RULE_MESSAGES


# Инициализируем компоненты один раз при загрузке модуля
router = RailwayRouter()
table3 = Table3Calculator()
table4 = Table4Calculator()


def calculate_freight(
    from_station: str,
    to_station: str,
    gng_code: str,
    weight_tons: float,
    wagon_type: str,
    lang: str = "AZ",
    raw_prompt: str = ""
) -> Dict[str, Any]:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Главная функция расчета стоимости перевозки. 
    Собирает результаты из router.py, таблицы ставок (Таблица 3 или 4) и main_rules.py,
    после чего формирует 3 блока данных (part1, part2, part3) для отображения в app.py.
    """
    # 1. Расчет маршрута и типа перевозки через router.py
    route_info = router.calculate_route(from_station, to_station)
    distance_km = route_info.distance_km
    shipment_type = route_info.shipment_type.value  # 'import', 'export', 'transit', 'local'

    # 2. Выбор таблицы и расчет базовой ставки за 1 тонну в CHF
    is_table_3 = shipment_type in ["import", "export"]
    
    if is_table_3:
        rate_res = table3.calculate_rate(distance_km=distance_km, weight_tons=weight_tons)
        table_code = "TABLE_3_BASE_RATE"
    else:
        rate_res = table4.calculate_rate(distance_km=distance_km, weight_tons=weight_tons)
        table_code = "TABLE_4_BASE_RATE"

    base_rate_per_ton = rate_res["calculated_value"]

    # 3. Применение главных сквозных правил и коэффициентов из main_rules.py
    rules_res = apply_main_rules(
        shipment_type=shipment_type,
        gng_code=gng_code,
        wagon_type=wagon_type,
        from_canonical_name=route_info.from_station.canonical_name,
        to_canonical_name=route_info.to_station.canonical_name,
        is_table_3=is_table_3
    )

    total_coeff = rules_res["calculated_value"]

    # 4. Расчет итоговой суммы за вагон в CHF
    # Формула: (Базовая ставка за тонну) * (Вес в тоннах) * (Итоговый коэффициент)
    total_cost_chf = round(base_rate_per_ton * weight_tons * total_coeff, 2)

    # 5. Сбор текстовых пояснений и примечаний к правилам на выбранном языке
    notes_list = []
    
    # Текст примененной таблицы
    if table_code in RULE_MESSAGES:
        notes_list.append(RULE_MESSAGES[table_code].get(lang, RULE_MESSAGES[table_code]["AZ"]))

    # Тексты примененных коэффициентов из main_rules
    coefficients_list = []
    for r in rules_res["rules"]:
        code = r["rule_code"]
        coeff_val = r["calculated_value"]
        msg = RULE_MESSAGES.get(code, {}).get(lang, code)
        coefficients_list.append({"name": msg, "value": f"x{coeff_val}"})
        notes_list.append(msg)

    # 6. Формирование структуры из 3 частей для UI (app.py)
    return {
        "part1": {
            "route": f"{route_info.from_station.canonical_name} → {route_info.to_station.canonical_name}",
            "shipment_type": shipment_type.upper(),
            "distance": f"{distance_km} km",
            "cargo_and_wagon": f"GNG: {gng_code} | Вагон: {wagon_type}",
            "weight_info": f"{weight_tons} t",
            "period": "2026"
        },
        "part2": {
            "base_tariff": f"{base_rate_per_ton} CHF / ton",
            "coefficients": coefficients_list
        },
        "part3": {
            "formula": f"{base_rate_per_ton} CHF * {weight_tons} t * {total_coeff} = {total_cost_chf} CHF",
            "net_ady_rate": f"{total_cost_chf} CHF",
            "notes": notes_list
        }
    }

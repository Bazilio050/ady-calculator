import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

# ------------------------------------------------------------------------------
# БЛОК 1: ПУТИ И КЭШ ДАННЫХ
# ------------------------------------------------------------------------------
TABLE_5_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "Table_5_Tariffs.txt"
)

_TABLE_5_CACHE: Optional[Dict[Tuple[int, int], Dict[str, float]]] = None


# ------------------------------------------------------------------------------
# БЛОК 2: ПАРСИНГ И КЭШИРОВАНИЕ ФАЙЛА ТАРИФОВ (Таблица 5)
# ------------------------------------------------------------------------------
def _parse_distance_range(raw_dist: str) -> Tuple[int, int]:
    """Преобразует строку диапазона '1-10' в кортеж целых чисел (1, 10)."""
    parts = raw_dist.strip().split("-")
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    raise ValueError(f"Некорректный формат интервала расстояния в Таблице 5: {raw_dist}")


def load_table_5_data(force_reload: bool = False) -> Dict[Tuple[int, int], Dict[str, float]]:
    """
    Загружает и кэширует базовые тарифные ставки Таблицы 5 (в CHF) из текстового файла.
    """
    global _TABLE_5_CACHE

    if _TABLE_5_CACHE is not None and not force_reload:
        return _TABLE_5_CACHE

    if not os.path.exists(TABLE_5_DATA_PATH):
        raise FileNotFoundError(f"Файл с тарифами Таблицы 5 не найден: {TABLE_5_DATA_PATH}")

    tariffs: Dict[Tuple[int, int], Dict[str, float]] = {}

    with open(TABLE_5_DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or line_str.startswith("=") or "Məsafə" in line_str or "Колонки:" in line_str:
                continue

            parts = [p.strip() for p in line_str.split("|")]
            if len(parts) < 8:
                continue

            try:
                dist_range = _parse_distance_range(parts[0])
                tariffs[dist_range] = {
                    "col_2": float(parts[1]),  # Рефрижераторы / ARV (<25т за вагон)
                    "col_3": float(parts[2]),  # Рефрижераторы / ARV (>=25т за 1т)
                    "col_4": float(parts[3]),  # Термосы / ледники (<25т за вагон)
                    "col_5": float(parts[4]),  # Термосы / ледники (>=25т за 1т)
                    "col_6": float(parts[5]),  # Автовозы (>=10т за 1т)
                    "col_7": float(parts[6]),  # ИНВ / АНВ груженый (за 1т)
                    "col_8": float(parts[7]),  # ИНВ / АНВ порожний (за вагон)
                }
            except (ValueError, IndexError):
                continue

    _TABLE_5_CACHE = tariffs
    return _TABLE_5_CACHE

# ------------------------------------------------------------------------------
# БЛОК 3: ЛОГИКА РАСЧЕТА СТАВКИ И КОЭФФИЦИЕНТОВ ТАБЛИЦЫ 5
# ------------------------------------------------------------------------------
def get_table_5_rate(
    distance_km: int,
    equipment_type: str,
    weight_tons: float = 0.0,
    is_empty: bool = False,
    ref_section_wagons_count: Optional[int] = None,
    is_cis_fruits_veg: bool = False,
    replacement_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Вычисляет базовую тарифную ставку в CHF по Таблице 5 с учетом всех коэффициентов
    и условий правил 3.1.2.1 - 3.1.2.3 Тарифной Политики.

    Параметры:
        distance_km: Тарифное расстояние в километрах.
        equipment_type: Тип вагона ("refrigerator", "arv", "thermos", "car_carrier", "two_tier_platform", "inv_anv").
        weight_tons: Фактическая масса груза в тоннах.
        is_empty: Флаг порожнего пробега (для ИНВ/АНВ).
        ref_section_wagons_count: Количество грузовых вагонов в рефсекции (1, 2, 3, 4, 5+).
        is_cis_fruits_veg: Флаг перевозки плодоовощной продукции стран Тарифного Соглашения (коэффициент 0.60).
        replacement_code: Код специальной замены вагонов ('IZVK', 'IZVT', 'VTVK').
    """
    tariffs = load_table_5_data()

    # 1. Поиск диапазона расстояний
    matched_rates = None
    for (min_dist, max_dist), rates in tariffs.items():
        if min_dist <= distance_km <= max_dist:
            matched_rates = rates
            break

    if matched_rates is None:
        raise ValueError(f"Расстояние {distance_km} км вышло за пределы тарифной сетки Таблицы 5")

    applied_coefficients = []

    # 2. Обработка особых замен вагонов
    # Замена рефвагона на крытый без температуры ("IZVK") -> расчет как за универсальный вагон (мин. 40т)
    if replacement_code == "IZVK":
        billable_weight = max(weight_tons, 40.0)
        return {
            "rate_chf": None,  # Должен перенаправляться в Таблицу 3/4 как универсальный вагон
            "calculation_type": "universal_replacement",
            "billable_weight": billable_weight,
            "note": "Подача рефвагона вместо крытого (IZVK). Расчет по правилам универсальных вагонов."
        }

    # Замена вагона-термоса на крытый ("VTVK") -> расчет как за универсальный вагон (мин. 60т)
    if replacement_code == "VTVK":
        billable_weight = max(weight_tons, 60.0)
        return {
            "rate_chf": None,  # Должен перенаправляться в Таблицу 3/4 как универсальный вагон
            "calculation_type": "universal_replacement",
            "billable_weight": billable_weight,
            "note": "Подача вагона-термоса вместо крытого (VTVK). Расчет по правилам универсальных вагонов."
        }

    # Замена рефвагона на термос ("IZVT") -> расчет по ставкам вагона-термоса
    if replacement_code == "IZVT":
        equipment_type = "thermos"

    # 3. Расчет по видам подвижного состава
    # А. Рефрижераторы и АРВ (п. 3.1.2.1)
    if equipment_type in ("refrigerator", "arv"):
        if weight_tons < 25.0:
            base_chf = matched_rates["col_2"]
            calc_type = "per_wagon"
            col_used = 2
        else:
            base_chf = matched_rates["col_3"] * weight_tons
            calc_type = "per_ton"
            col_used = 3

        # Коэффициенты от количества грузовых вагонов в секции
        if ref_section_wagons_count == 1:
            base_chf *= 1.7
            applied_coefficients.append(1.7)
        elif ref_section_wagons_count == 2:
            base_chf *= 1.4
            applied_coefficients.append(1.4)
        elif ref_section_wagons_count == 3:
            base_chf *= 1.1
            applied_coefficients.append(1.1)
        elif ref_section_wagons_count is not None and ref_section_wagons_count >= 5:
            base_chf *= 0.85
            applied_coefficients.append(0.85)

        # Коэффициент 0.60 на плодоовощную продукцию стран-участниц
        if is_cis_fruits_veg:
            base_chf *= 0.60
            applied_coefficients.append(0.60)

        return {
            "rate_chf": round(base_chf, 4),
            "calculation_type": calc_type,
            "column_used": col_used,
            "billable_weight": weight_tons,
            "coefficients": applied_coefficients
        }

    # Б. Вагоны-термосы и вагоны-ледники (п. 3.1.2.2)
    elif equipment_type in ("thermos", "ice_wagon"):
        if weight_tons < 25.0:
            base_chf = matched_rates["col_4"]
            calc_type = "per_wagon"
            col_used = 4
        else:
            base_chf = matched_rates["col_5"] * weight_tons
            calc_type = "per_ton"
            col_used = 5

        return {
            "rate_chf": round(base_chf, 4),
            "calculation_type": calc_type,
            "column_used": col_used,
            "billable_weight": weight_tons,
            "coefficients": applied_coefficients
        }

    # В. Автовозы и двухярусные платформы (п. 3.1.2.3)
    elif equipment_type in ("car_carrier", "two_tier_platform"):
        billable_weight = max(weight_tons, 10.0)
        base_chf = matched_rates["col_6"] * billable_weight

        # Понижающий коэффициент 0.80 для двухярусных платформ
        if equipment_type == "two_tier_platform":
            base_chf *= 0.80
            applied_coefficients.append(0.80)

        return {
            "rate_chf": round(base_chf, 4),
            "calculation_type": "per_ton",
            "column_used": 6,
            "billable_weight": billable_weight,
            "coefficients": applied_coefficients
        }

    # Г. Перевозки ИНВ / АНВ
    elif equipment_type in ("inv", "anv", "inv_anv"):
        if is_empty:
            return {
                "rate_chf": matched_rates["col_8"],
                "calculation_type": "per_wagon",
                "column_used": 8,
                "billable_weight": 0.0,
                "coefficients": []
            }
        else:
            return {
                "rate_chf": round(matched_rates["col_7"] * weight_tons, 4),
                "calculation_type": "per_ton",
                "column_used": 7,
                "billable_weight": weight_tons,
                "coefficients": []
            }

    else:
        raise ValueError(f"Неизвестный тип специализированного подвижного состава: {equipment_type}")

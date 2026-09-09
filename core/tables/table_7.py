
# ------------------------------------------------------------------------------
# БЛОК 1: Импорт библиотек и объявления типа
# ------------------------------------------------------------------------------
import os
from typing import Dict, Tuple, Optional, Any, List


class Table7Calculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Считывает тарифные ставки Таблицы 7 из файла data/Table_7_Tariffs.txt
    и вычисляет базовую ставку в CHF для:
    1. Повагонных отправок малой тоннажности (5, 10, 15, 20, 25 тонн) — ставка за 1 тонну.
    2. Пассажирских вагонов и почтовых отправлений (ГНГ 99910000) по колонке 6 — ставка за 1 тонну (мин. 66 т).
    3. Среднетоннажных контейнеров (3 и 5 тонн, гружёных и порожних) — ставка за 1 контейнер.
    """

    DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Table_7_Tariffs.txt")

    _rates_cache: Optional[Dict[Tuple[int, int], Dict[str, float]]] = None

    # --------------------------------------------------------------------------
    # БЛОК 2: Загрузка и кэширование тарифных ставок
    # --------------------------------------------------------------------------
    @classmethod
    def _parse_distance_range(cls, raw_dist: str) -> Tuple[int, int]:
        """Разбирает строку диапазона '1-10' в кортеж (1, 10)."""
        parts = raw_dist.strip().split("-")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        raise ValueError(f"Некорректный формат диапазона расстояний в Таблице 7: {raw_dist}")

    @classmethod
    def _load_data(cls) -> Dict[Tuple[int, int], Dict[str, float]]:
        """Считывает и кэширует данные из Table_7_Tariffs.txt один раз."""
        if cls._rates_cache is not None:
            return cls._rates_cache

        file_path = os.path.abspath(cls.DATA_FILE_PATH)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл Таблицы 7 не найден по пути: {file_path}")

        tariffs: Dict[Tuple[int, int], Dict[str, float]] = {}

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if (
                    not line_str
                    or line_str.startswith("=")
                    or line_str.startswith("CƏDVƏL")
                    or "Məsafə" in line_str
                    or "Колонки:" in line_str
                ):
                    continue

                parts = [p.strip() for p in line_str.split("|")]
                if len(parts) < 10:
                    continue

                try:
                    dist_range = cls._parse_distance_range(parts[0])
                    tariffs[dist_range] = {
                        "col_2": float(parts[1]),  # Вагон: 5 тонн
                        "col_3": float(parts[2]),  # Вагон: 10 тонн
                        "col_4": float(parts[3]),  # Вагон: 15 тонн
                        "col_5": float(parts[4]),  # Вагон: 20 тонн
                        "col_6": float(parts[5]),  # Вагон: 25 тонн / Пассажирский / Почта (ГНГ 99910000)
                        "col_7": float(parts[6]),  # Контейнер 3т (гружёный)
                        "col_8": float(parts[7]),  # Контейнер 5т (гружёный)
                        "col_9": float(parts[8]),  # Контейнер 3т (порожний)
                        "col_10": float(parts[9]), # Контейнер 5т (порожний)
                    }
                except (ValueError, IndexError):
                    continue

        cls._rates_cache = tariffs
        return cls._rates_cache

    # --------------------------------------------------------------------------
    # БЛОК 3: Определение колонки таблицы
    # --------------------------------------------------------------------------
    @classmethod
    def determine_column(
        cls,
        calc_type: str,
        weight_category: Optional[int] = None,
        container_category_tons: Optional[int] = None,
        is_loaded: bool = True,
        cargo_code_gng: Optional[str] = None,
        is_passenger_wagon: bool = False
    ) -> Tuple[str, str]:
        """
        Динамически определяет код колонки (col_2 ... col_10) и код правила локализации.
        """
        clean_gng = str(cargo_code_gng).strip() if cargo_code_gng else ""

        # 1. Почтовые отправления (ГНГ 99910000) или Пассажирские вагоны -> Колонка 6
        if is_passenger_wagon or clean_gng == "99910000":
            return "col_6", "TABLE_7_COL_6_PASSENGER_POSTAL"

        # 2. Малотоннажные повагонные отправки (Колонки 2 - 6)
        if calc_type == "wagon_small_tonnage":
            if weight_category == 5:
                return "col_2", "TABLE_7_COL_2_WAGON_5T"
            elif weight_category == 10:
                return "col_3", "TABLE_7_COL_3_WAGON_10T"
            elif weight_category == 15:
                return "col_4", "TABLE_7_COL_4_WAGON_15T"
            elif weight_category == 20:
                return "col_5", "TABLE_7_COL_5_WAGON_20T"
            elif weight_category == 25:
                return "col_6", "TABLE_7_COL_6_WAGON_25T"
            else:
                raise ValueError(f"Неподдерживаемая категория веса вагона: {weight_category}")

        # 3. Среднетоннажные контейнеры (Колонки 7 - 10)
        elif calc_type == "medium_container":
            if container_category_tons == 3:
                return ("col_7", "TABLE_7_COL_7_CONTAINER_3T_LOADED") if is_loaded else ("col_9", "TABLE_7_COL_9_CONTAINER_3T_EMPTY")
            elif container_category_tons == 5:
                return ("col_8", "TABLE_7_COL_8_CONTAINER_5T_LOADED") if is_loaded else ("col_10", "TABLE_7_COL_10_CONTAINER_5T_EMPTY")
            else:
                raise ValueError(f"Неподдерживаемая категория среднетоннажного контейнера: {container_category_tons}")

        else:
            raise ValueError(f"Неизвестный тип расчета для Таблицы 7: {calc_type}")

    # --------------------------------------------------------------------------
    # БЛОК 4: Вычисление ставки и возврат результата
    # --------------------------------------------------------------------------
    @classmethod
    def calculate(
        cls,
        distance_km: float,
        calc_type: str,  # "wagon_small_tonnage" или "medium_container"
        weight_tons: float = 0.0,
        weight_category: Optional[int] = None,
        container_category_tons: Optional[int] = None,
        is_loaded: bool = True,
        cargo_code_gng: Optional[str] = None,
        is_passenger_wagon: bool = False
    ) -> Dict[str, Any]:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Находит базовую ставку CHF и выполняет первоначальный расчет для Таблицы 7.
        """
        dist = int(round(distance_km))
        tariffs = cls._load_data()

        matched_rates = None
        matched_range = None
        for (min_dist, max_dist), rates in tariffs.items():
            if min_dist <= dist <= max_dist:
                matched_rates = rates
                matched_range = (min_dist, max_dist)
                break

        if matched_rates is None:
            if dist > 1000 and (991, 1000) in tariffs:
                matched_rates = tariffs[(991, 1000)]
                matched_range = (991, 1000)
            else:
                raise ValueError(f"Расстояние {dist} км выходит за пределы Таблицы 7.")

        column_name, col_rule_code = cls.determine_column(
            calc_type=calc_type,
            weight_category=weight_category,
            container_category_tons=container_category_tons,
            is_loaded=is_loaded,
            cargo_code_gng=cargo_code_gng,
            is_passenger_wagon=is_passenger_wagon
        )

        base_rate = matched_rates[column_name]
        applied_rules: List[Dict[str, Any]] = []

        applied_rules.append({
            "rule_code": "TABLE_7_BASE_LOOKUP",
            "params": {
                "distance_km": dist,
                "interval": f"{matched_range[0]}-{matched_range[1]}",
                "column": column_name,
                "base_rate_chf": base_rate
            }
        })

        applied_rules.append({
            "rule_code": col_rule_code,
            "params": {"column": column_name}
        })

        # Вычисление итоговой ставки CHF для данного этапа
        clean_gng = str(cargo_code_gng).strip() if cargo_code_gng else ""
        if calc_type == "wagon_small_tonnage" or is_passenger_wagon or clean_gng == "99910000":
            billable_weight = weight_tons
            if is_passenger_wagon or clean_gng == "99910000":
                if billable_weight < 66.0:
                    billable_weight = 66.0
                    applied_rules.append({
                        "rule_code": "TABLE_7_MIN_PASSENGER_POSTAL_WEIGHT_66T",
                        "params": {"actual_weight": weight_tons, "applied_weight": 66.0}
                    })
            calculated_rate_chf = round(base_rate * billable_weight, 2)
        else:
            calculated_rate_chf = round(base_rate, 2)

        return {
            "base_rate": base_rate,
            "column_name": column_name,
            "calculated_rate_chf": calculated_rate_chf,
            "applied_rules": applied_rules
        }

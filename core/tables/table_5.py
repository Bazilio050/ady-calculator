# core/tables/table_5.py

import os
from typing import Dict, Tuple, Optional, Any


class Table5Calculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Считывает тарифные ставки Таблицы 5 из файла data/Table_5_Tariffs.txt 
    и вычисляет базовую ставку для специализированного подвижного состава (СПС).
    """

    DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Table_5_Tariffs.txt")

    _rates_cache: Optional[Dict[Tuple[int, int], Dict[str, float]]] = None

    FRUIT_VEG_GNG_PREFIXES = (
        "0701", "0702", "0703", "0704", "0705", "0706", "0707", "0708", "0709", "0710",
        "0803", "0804", "0805", "0806", "0807", "0808", "0809", "0810",
        "12129100"
    )

    @classmethod
    def _parse_distance_range(cls, raw_dist: str) -> Tuple[int, int]:
        """Разбирает строку диапазона '1-10' в кортеж (1, 10)."""
        parts = raw_dist.strip().split("-")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        raise ValueError(f"Некорректный формат диапазона расстояний в Таблице 5: {raw_dist}")

    @classmethod
    def _load_data(cls) -> Dict[Tuple[int, int], Dict[str, float]]:
        """Считывает и кэширует данные из Table_5_Tariffs.txt один раз."""
        if cls._rates_cache is not None:
            return cls._rates_cache

        file_path = os.path.abspath(cls.DATA_FILE_PATH)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл Таблицы 5 не найден по пути: {file_path}")

        tariffs: Dict[Tuple[int, int], Dict[str, float]] = {}

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("#") or line_str.startswith("=") or "Məsafə" in line_str or "Колонки:" in line_str:
                    continue

                parts = [p.strip() for p in line_str.split("|")]
                if len(parts) < 8:
                    continue

                try:
                    dist_range = cls._parse_distance_range(parts[0])
                    tariffs[dist_range] = {
                        "col_2": float(parts[1]),  # Рефрижераторы <25т (за вагон)
                        "col_3": float(parts[2]),  # Рефрижераторы >=25т (за 1т)
                        "col_4": float(parts[3]),  # Термосы/ледники <25т (за вагон)
                        "col_5": float(parts[4]),  # Термосы/ледники >=25т (за 1т)
                        "col_6": float(parts[5]),  # Автовозы >=10т (за 1т)
                        "col_7": float(parts[6]),  # ИНВ / АНВ груженый (за 1т)
                        "col_8": float(parts[7]),  # ИНВ / АНВ порожний (за вагон)
                    }
                except (ValueError, IndexError):
                    continue

        cls._rates_cache = tariffs
        return cls._rates_cache

    @classmethod
    def calculate(
        cls,
        distance_km: float,
        weight_tons: float = 0.0,
        equipment_type: str = "refrigerator",
        is_empty: bool = False,
        ref_section_wagons_count: Optional[int] = None,
        gng_code: Optional[str] = None,
        is_tariff_agreement_origin: bool = False,
        axle_count: int = 4,
        is_in_loaded_ref_section: bool = False
    ) -> Dict[str, Any]:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Расчитывает базовую ставку CHF/т по Таблице 5 и спецвагонам, включая коэффициенты
        составности рефсекции, скидку 0.60 на овощи/фрукты, аксиальную ставку 0.12 CHF/ось-км 
        для дизель-генераторов и 0.10 CHF/ось-км для порожних вагонов в гружёных секциях.
        """
        dist = int(round(distance_km))
        eq_lower = equipment_type.lower()
        applied_rules = []

        # 0. Дизель-генераторный вагон в составе приватной рефсекции (0.12 CHF / ось-км)
        if eq_lower in ("diesel_generator", "diesel_gen", "дизель_генератор"):
            rate_per_axle_km = 0.12
            total_chf_flat = round(rate_per_axle_km * axle_count * dist, 2)
            
            applied_rules.append({
                "rule_code": "REF_DIESEL_GENERATOR_AXLE_RATE",
                "calculated_value": rate_per_axle_km,
                "params": {
                    "axle_count": axle_count,
                    "distance_km": dist,
                    "rate_per_axle_km": rate_per_axle_km
                }
            })
            
            return {
                "base_rate": total_chf_flat,
                "raw_base_rate": total_chf_flat,
                "is_flat_fee": True,
                "applied_rules": applied_rules
            }

        tariffs = cls._load_data()
        matched_rates = None
        for (min_dist, max_dist), rates in tariffs.items():
            if min_dist <= dist <= max_dist:
                matched_rates = rates
                break

        if matched_rates is None:
            raise ValueError(f"Расстояние {dist} км выходит за пределы Таблицы 5.")

        base_rate = 0.0

        # 1. Рефрижераторы и ARV
        if eq_lower in ("refrigerator", "arv", "ref_section"):
            # Порожний вагон в составе гружёной рефсекции (0.10 CHF / ось-км)
            if is_empty and is_in_loaded_ref_section:
                rate_per_axle_km = 0.10
                total_chf_flat = round(rate_per_axle_km * axle_count * dist, 2)
                applied_rules.append({
                    "rule_code": "REF_EMPTY_WAGON_IN_LOADED_SECTION_AXLE_RATE",
                    "calculated_value": rate_per_axle_km,
                    "params": {
                        "axle_count": axle_count,
                        "distance_km": dist,
                        "rate_per_axle_km": rate_per_axle_km
                    }
                })
                return {
                    "base_rate": total_chf_flat,
                    "raw_base_rate": total_chf_flat,
                    "is_flat_fee": True,
                    "applied_rules": applied_rules
                }

            base_rate = matched_rates["col_2"] if weight_tons < 25.0 else matched_rates["col_3"]

            # Коэффициенты от количества вагонов в секции (п. 3.1.2.1 / Таблица 5)
            coeff_val = 1.0
            rule_code = None

            if ref_section_wagons_count == 1:
                coeff_val = 1.70
                rule_code = "REF_SECTION_COEFF_1_70"
            elif ref_section_wagons_count == 2:
                coeff_val = 1.40
                rule_code = "REF_SECTION_COEFF_1_40"
            elif ref_section_wagons_count == 3:
                coeff_val = 1.10
                rule_code = "REF_SECTION_COEFF_1_10"
            elif ref_section_wagons_count == 4:
                coeff_val = 1.00
                rule_code = "REF_SECTION_COEFF_1_00"
            elif ref_section_wagons_count and ref_section_wagons_count >= 5:
                coeff_val = 0.85
                rule_code = "REF_SECTION_COEFF_0_85"

            if rule_code:
                applied_rules.append({
                    "rule_code": rule_code,
                    "calculated_value": coeff_val,
                    "params": {"ref_section_wagons_count": ref_section_wagons_count}
                })

            # Скидка 0.60 на плодоовощную продукцию стран Тарифного Соглашения
            if is_tariff_agreement_origin and gng_code:
                clean_gng = str(gng_code).strip()
                if any(clean_gng.startswith(prefix) for prefix in cls.FRUIT_VEG_GNG_PREFIXES):
                    coeff_val *= 0.60
                    applied_rules.append({
                        "rule_code": "REF_FRUIT_VEG_COEFF_0_60",
                        "calculated_value": 0.60,
                        "params": {"gng_code": clean_gng}
                    })

            final_rate = base_rate * coeff_val
            return {
                "base_rate": final_rate,
                "raw_base_rate": base_rate,
                "applied_rules": applied_rules
            }

        # 2. Термосы и ледники
        elif eq_lower in ("thermos", "ice_wagon"):
            base_rate = matched_rates["col_4"] if weight_tons < 25.0 else matched_rates["col_5"]

        # 3. Автовозы и двухъярусные платформы
        elif eq_lower in ("car_carrier", "two_tier_platform", "двухъярусная_платформа"):
            base_rate = matched_rates["col_6"]
            if eq_lower in ("two_tier_platform", "двухъярусная_платформа"):
                base_rate *= 0.80
                applied_rules.append({
                    "rule_code": "CAR_CARRIER_TWO_TIER_COEFF_0_80",
                    "calculated_value": 0.80,
                    "params": {"equipment_type": equipment_type}
                })

        # 4. ИНВ / АНВ
        elif eq_lower in ("inv", "anv", "inv_anv"):
            base_rate = matched_rates["col_8"] if is_empty else matched_rates["col_7"]

        else:
            raise ValueError(f"Неизвестный тип подвижного состава для Таблицы 5: {equipment_type}")

        return {
            "base_rate": base_rate,
            "raw_base_rate": base_rate,
            "applied_rules": applied_rules
        }

    @classmethod
    def get_base_rate(
        cls,
        distance_km: float,
        weight_tons: float = 0.0,
        equipment_type: str = "refrigerator",
        is_empty: bool = False,
        ref_section_wagons_count: Optional[int] = None,
        gng_code: Optional[str] = None,
        is_tariff_agreement_origin: bool = False,
        axle_count: int = 4,
        is_in_loaded_ref_section: bool = False
    ) -> float:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Старый метод для сохранения совместимости. Возвращает только итоговую ставку float.
        """
        res = cls.calculate(
            distance_km=distance_km,
            weight_tons=weight_tons,
            equipment_type=equipment_type,
            is_empty=is_empty,
            ref_section_wagons_count=ref_section_wagons_count,
            gng_code=gng_code,
            is_tariff_agreement_origin=is_tariff_agreement_origin,
            axle_count=axle_count,
            is_in_loaded_ref_section=is_in_loaded_ref_section
        )
        return res["base_rate"]

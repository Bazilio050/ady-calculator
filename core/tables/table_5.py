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
        axle_count: int = 4
    ) -> Dict[str, Any]:
        """
        ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
        Расчитывает базовую ставку CHF/т по Таблице 5 и спецвагонам, включая коэффициенты
        составности рефсекции, скидку 0.60 на овощи/фрукты и аксиальную ставку 0.12 CHF/ось-км для дизель-генераторов.
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

        # 3. Автовозы
        elif eq_lower == "car_carrier":
            base_rate = matched_rates["col_6"]

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

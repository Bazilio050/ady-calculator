# core/tables/table_min_load.py

from typing import Dict, Any


class TableMinLoadCalculator:
    """
    ЧЕЛОВЕЧЕСКОЕ ОПИСАНИЕ:
    Проверка минимальной нормы загрузки вагонов по Тарифному руководству ADY.
    """

    @classmethod
    def get_min_load_weight(cls, gng_code: str, actual_weight: int) -> Dict[str, Any]:
        """
        Проверяет минимальную норму загрузки по коду ГНГ.
        Если фактический вес меньше нормы — берет норму.
        Если больше или равен — оставляет фактический вес.
        """
        w = int(actual_weight)

        if not gng_code:
            return {
                "calculated_weight": w,
                "rule_code": None,
                "params": {}
            }

        code = str(gng_code).strip()
        min_norm = None

        # 1. Лесоматериалы (коды начинаются с 4403, 4404, 4407) -> Норма 45 тонн
        if any(code.startswith(prefix) for prefix in ["4403", "4404", "4407"]):
            min_norm = 45

        # 2. Хлопок (код 14042 и диапазон от 5201 до 5203 включительно) -> Норма 50 тонн
        elif code.startswith("14042") or any(code.startswith(str(p)) for p in range(5201, 5204)):
            min_norm = 50

        # 3. Лом черных металлов (код 7204, кроме 72045) -> Норма 50 тонн
        elif code.startswith("7204") and not code.startswith("72045"):
            min_norm = 50

        # 4. Каменный уголь (коды 2701, 2702) -> Норма 60 тонн
        elif code.startswith("2701") or code.startswith("2702"):
            min_norm = 60

        # 5. Руды (вводная группа 26 кроме 2618-2621, а также 7203, 7401, 7501, 81052, 28182000) -> Норма 60 тонн
        elif (code.startswith("26") and not any(code.startswith(str(p)) for p in range(2618, 2622))) or \
             any(code.startswith(p) for p in ["7203", "7401", "7501", "81052", "28182000"]):
            min_norm = 60

        # 6. Чугун (код 7201) -> Норма 60 тонн
        elif code.startswith("7201"):
            min_norm = 60

        # 7. Удобрения (вся группа 31, кроме 3101) -> Норма 60 тонн
        elif code.startswith("31") and not code.startswith("3101"):
            min_norm = 60

        # 8. Сахар (код 1701) -> Норма 60 тонн
        elif code.startswith("1701"):
            min_norm = 60

        # 9. Мука (коды от 1101 до 1103 включительно: 1101, 1102, 1103) -> Норма 60 тонн
        elif any(code.startswith(str(p)) for p in range(1101, 1104)):
            min_norm = 60

        # 10. Зерновые культуры (вся группа 10, а также код 1107) -> Норма 60 тонн
        elif code.startswith("10") or code.startswith("1107"):
            min_norm = 60

        # 11. Черные металлы (вся группа 72, кроме лома 7204) -> Норма 60 тонн
        elif code.startswith("72") and not code.startswith("7204"):
            min_norm = 60

        # 12. Цветные и спец. металлы — Категория 50 тонн
        elif code.startswith("32121") or code.startswith("71101910") or \
             any(code.startswith(str(p)) for p in range(7407, 7411)) or \
             code.startswith("7413") or code.startswith("7505") or code.startswith("7506") or \
             any(code.startswith(str(p)) for p in range(7604, 7608)) or code.startswith("76149") or \
             (code.startswith("7804") and not code.startswith("78042")) or code.startswith("78060080") or \
             code.startswith("7904") or code.startswith("7905") or code.startswith("8003") or \
             code.startswith("80070010") or code.startswith("80070080") or code.startswith("81019600") or \
             code.startswith("81029500") or code.startswith("81029600") or code.startswith("81032") or \
             code.startswith("81039010") or code.startswith("81089030") or code.startswith("81089050"):
            min_norm = 50

        # 13. Цветные и спец. металлы — Категория 40 тонн
        elif code.startswith("7404") or code.startswith("7503") or code.startswith("7602") or \
             code.startswith("7802") or ((code.startswith("7902") or code.startswith("7903")) and not code.startswith("79039")) or \
             code.startswith("8002") or code.startswith("81019700") or code.startswith("81029700") or \
             code.startswith("81033000") or code.startswith("81042") or code.startswith("81043") or \
             code.startswith("81053") or code.startswith("81073") or code.startswith("81083") or \
             code.startswith("81093") or code.startswith("81102") or code.startswith("81110019") or \
             code.startswith("81121300") or code.startswith("81122200") or code.startswith("81124110") or \
             code.startswith("81125200") or code.startswith("81130040") or code.startswith("85481") or \
             code.startswith("85493") or code.startswith("85499") or code.startswith("85492000"):
            min_norm = 40

        # 14. Цветные и спец. металлы — Категория 30 тонн
        elif code.startswith("71159") or code.startswith("7411") or code.startswith("7412") or \
             code.startswith("7415") or code.startswith("7419") or code.startswith("7507") or \
             code.startswith("7508") or any(code.startswith(str(p)) for p in range(7608, 7614)) or \
             code.startswith("76152") or code.startswith("7616") or code.startswith("7806") or \
             code.startswith("7907") or code.startswith("8007") or code.startswith("81059") or \
             code.startswith("81060090") or code.startswith("81079") or code.startswith("81089") or \
             code.startswith("81099") or code.startswith("81109") or code.startswith("81110090") or \
             code.startswith("811219") or code.startswith("81122900") or code.startswith("81129920") or \
             code.startswith("81129970") or code.startswith("811259") or code.startswith("81129900") or \
             code.startswith("81129930") or code.startswith("81130090") or code.startswith("8302") or \
             code.startswith("83061") or code.startswith("83079") or code.startswith("8309") or \
             code.startswith("8311") or code.startswith("8481") or code.startswith("8482") or \
             any(code.startswith(str(p)) for p in range(84831, 84834)) or \
             any(code.startswith(f"848390{i:02d}") for i in range(0, 90)) or code.startswith("8484"):
            min_norm = 30

        # 15. Прочие металлы (кроме черных) -> Норма 60 тонн
        elif code.startswith("28045") or code.startswith("28049") or code.startswith("28053") or \
             code.startswith("28054") or any(code.startswith(str(p)) for p in range(7106, 7111)):
            min_norm = 60

        # Проверка применения нормы
        is_applied = min_norm is not None and w < min_norm
        final_w = min_norm if is_applied else w
        rule_code = "MIN_LOAD_NORM" if is_applied else None

        return {
            "calculated_weight": final_w,
            "rule_code": rule_code,
            "params": {"actual": w, "applied": final_w} if rule_code else {}
        }

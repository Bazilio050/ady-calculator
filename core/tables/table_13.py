# core/tables/table_13.py

import os
from typing import Dict, Any, Optional

def _load_table_13_data() -> Dict[str, Dict[str, Any]]:
    """
    Загружает список опасных грузов из data/Table_13_Tariffs.txt.
    Возвращает словарь, где ключ — BMT_№ (код ООН).
    """
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "Table_13_Tariffs.txt"
    )
    table_data = {}

    if not os.path.exists(file_path):
        return table_data

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Təhlükəli") or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue

            un_code = parts[1].zfill(4)  # Номер ООН (BMT №)
            table_data[un_code] = {
                "name": parts[0],
                "un_code": un_code,
                "class_code": parts[3],
                "app_type": parts[4].lower()  # ortulu_konteyner, cen, hamisi
            }

    return table_data

_TABLE_13_DATA = _load_table_13_data()


class Table13Checker:
    """Модуль проверки применимости правил Таблицы 13 для опасных грузов."""

    @classmethod
    def check_dangerous_status(
        cls,
        un_code: Optional[str],
        wagon_type: str
    ) -> bool:
        """
        Проверяет, требует ли данный груз применения повышающего коэффициента 2.00
        согласно Таблице 13.
        """
        if not un_code:
            return False

        clean_un = str(un_code).strip().zfill(4)
        if clean_un not in _TABLE_13_DATA:
            return False

        item = _TABLE_13_DATA[clean_un]
        app_type = item["app_type"]
        w_type = wagon_type.lower()

        # Проверка соответствия типа подвижного состава условию в Таблице 13
        if app_type == "hamisi":
            return True
        elif app_type == "cen" and w_type in ("cistern", "tank", "цистерна", "бункер", "bunker", "tank_container"):
            return True
        elif app_type == "ortulu_konteyner" and w_type not in ("cistern", "tank", "цистерна", "бункер", "bunker"):
            return True

        return False

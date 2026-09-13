# core/security_calculator.py

import os
from typing import Set, Dict, Any

class SecurityCalculator:
    """
    Модуль проверки ГНГ-кодов на обязательную охрану ВОХР (ADY) 
    и расчета сбора за охрану при транзите.
    """
    _security_gng_codes: Set[str] = set()

    @classmethod
    def _load_security_codes(cls):
        """Загрузка реестра ГНГ, подлежащих обязательной охране."""
        if cls._security_gng_codes:
            return

        filepath = os.path.join("data", "Security_Cargo_GNG.txt")
        if not os.path.exists(filepath):
            return

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("| Kod GNG") or line.startswith("| :---"):
                    continue
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if parts:
                    clean_code = parts[0].replace("**", "").strip()
                    if clean_code.isdigit():
                        cls._security_gng_codes.add(clean_code)

    @classmethod
    def is_security_required(cls, gng_code: str) -> bool:
        """Проверка, подлежит ли ГНГ-код обязательной охране."""
        cls._load_security_codes()
        clean_gng = str(gng_code).strip()

        # Проверка по прямому совпадению или префиксам (4, 6, 8 знаков)
        for code in cls._security_gng_codes:
            if clean_gng.startswith(code) or code.startswith(clean_gng):
                return True
        return False

    @classmethod
    def calculate(
        cls, 
        shipment_type: str, 
        gng_code: str, 
        distance_km: float
    ) -> Dict[str, Any]:
        """
        Расчет платы за охрану: применяется ТОЛЬКО при транзите.
        Формула: km * 0.1 / 0.7
        """
        ship_type = str(shipment_type).lower()
        
        if ship_type not in ("transit", "транзит", "tranzit"):
            return {
                "is_required": False,
                "security_fee_usd": 0.0,
                "message": "Охрана не применяется (не транзитная перевозка)"
            }

        if not cls.is_security_required(gng_code):
            return {
                "is_required": False,
                "security_fee_usd": 0.0,
                "message": "Груз не подлежит обязательной охране"
            }

        # Расчет по формуле: km * 0.1 / 0.7
        fee_usd = round((distance_km * 0.1) / 0.7, 2)

        return {
            "is_required": True,
            "security_fee_usd": fee_usd,
            "message": f"Обязательная охрана ВОХР: ${fee_usd} USD"
        }

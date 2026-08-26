import json
import logging
import re
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ==============================================================================
# СЛОВАРИ И СООТВЕТСТВИЯ НАЗВАНИЙ И КОДОВ ЕСР
# ==============================================================================

STATION_CODES: Dict[str, str] = {
    "Yalama": "547508",
    "Böyük Kəsik": "548004",
    "İmişli": "547103",
    "Abşeron": "548405",
    "Salyan": "547404",
    "Bakı yük": "540000",
    "Gəncə": "545000",
    "Astara": "547904",
    "Ələt": "548502",
    "Ələt yeni": "548703",
    "Ələt-eksp. Kurik": "553002",
    "Ələt-eksp. Aktau": "549204",
    "Ələt-eksp. Türk.": "548803"
}

STATION_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "Yalama": {"az": "Yalama", "ru": "Ялама", "en": "Yalama"},
    "Böyük Kəsik": {"az": "Böyük Kəsik", "ru": "Беюк Кясик", "en": "Beyuk Kasik"},
    "İmişli": {"az": "İmişli", "ru": "Имишли", "en": "Imishli"},
    "Abşeron": {"az": "Abşeron", "ru": "Апшерон", "en": "Absheron"},
    "Salyan": {"az": "Salyan", "ru": "Сальяны", "en": "Salyan"},
    "Bakı yük": {"az": "Bakı yük", "ru": "Баку гл.", "en": "Baku freight"},
    "Gəncə": {"az": "Gəncə", "ru": "Гянджа", "en": "Ganja"},
    "Astara": {"az": "Astara", "ru": "Астара", "en": "Astara"},
    "Ələt": {"az": "Ələt", "ru": "Алят", "en": "Alat"},
    "Ələt yeni": {"az": "Ələt yeni", "ru": "Алят новый", "en": "Alat yeni"}
}

EXP_SUFFIX: Dict[str, str] = {
    "az": "-eksp.",
    "ru": "-эксп.",
    "en": "-exp.",
    "AZ": "-eksp.",
    "RU": "-эксп.",
    "EN": "-exp."
}

BORDER_STATIONS = {"Yalama", "Böyük Kəsik", "Astara", "Ələt-eksp.", "Ələt-eksp. Kurik", "Ələt-eksp. Aktau", "Ələt-eksp. Türk."}

# ==============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ФОРМАТИРОВАНИЯ
# ==============================================================================

def format_station_display(st_name: str, 
                           parsed_data: dict, 
                           is_from: bool, 
                           lang: str = "ru") -> str:
    lang_lower = lang.lower()
    suf = EXP_SUFFIX.get(lang_lower, "-эксп.")
    shipment_type = parsed_data.get("shipment_type")
    alat_terminal = parsed_data.get("alat_terminal")
    is_exp_flag = parsed_data.get("is_exp_flag", False)
    
    should_have_exp = False
    if shipment_type in ["tranzit", "transit"]:
        should_have_exp = True
    elif is_exp_flag and "Ələt" in st_name:
        should_have_exp = True
    elif st_name in BORDER_STATIONS:
        if (shipment_type in ["idxal", "import"] and is_from) or (shipment_type in ["ixrac", "export"] and not is_from):
            should_have_exp = True

    if "Ələt" in st_name:
        if alat_terminal == "Kurik":
            code = STATION_CODES.get("Ələt-eksp. Kurik", "553002")
            name = "Ələt-eksp. Kurik" if lang_lower == "az" else "Алят-эксп. Курык" if lang_lower == "ru" else "Alat-exp. Kuryk"
            return f"{name} ({code})"
            
        elif alat_terminal == "Aktau":
            code = STATION_CODES.get("Ələt-eksp. Aktau", "549204")
            name = "Ələt-eksp. Aktau" if lang_lower == "az" else "Алят-эксп. Актау" if lang_lower == "ru" else "Alat-exp. Aktau"
            return f"{name} ({code})"
            
        elif alat_terminal == "Turk":
            code = STATION_CODES.get("Ələt-eksp. Türk.", "548803")
            name = "Ələt-eksp. Türk." if lang_lower == "az" else "Алят-эксп. Туркм." if lang_lower == "ru" else "Alat-exp. Turk."
            return f"{name} ({code})"
            
        elif is_exp_flag or st_name == "Ələt-eksp.":
            name = f"Ələt{suf}" if lang_lower == "az" else f"Алят{suf}" if lang_lower == "ru" else f"Alat{suf}"
            return name

        elif "yeni" in st_name.lower():
            code = STATION_CODES.get("Ələt yeni", "548703")
            name = "Ələt yeni" if lang_lower == "az" else "Алят новый" if lang_lower == "ru" else "Alat yeni"
            return f"{name} ({code})"

    code = STATION_CODES.get(st_name, "")
    code_str = f" ({code})" if code else ""
    
    translations = STATION_TRANSLATIONS.get(st_name, {"az": st_name, "ru": st_name, "en": st_name})
    base_name = translations.get(lang_lower, st_name)

    if should_have_exp:
        return f"{base_name}{suf}{code_str}"
    else:
        return f"{base_name}{code_str}"


def calculate_distance(from_st: str, to_st: str, parsed_data: dict) -> int:
    search_from = "Ələt-eksp. Kurik" if from_st in ["Ələt", "Ələt-eksp."] else from_st
    search_to = "Ələt-eksp. Kurik" if to_st in ["Ələt", "Ələt-eksp."] else to_st

    pair = tuple(sorted([search_from, search_to]))
    
    distances_db = {
        tuple(sorted(["Yalama", "Ələt-eksp. Kurik"])): 291,
        tuple(sorted(["Böyük Kəsik", "Ələt-eksp. Kurik"])): 448,
        tuple(sorted(["Yalama", "Böyük Kəsik"])): 502,
        tuple(sorted(["Yalama", "İmişli"])): 380,
        tuple(sorted(["Yalama", "Ələt yeni"])): 243,
        tuple(sorted(["Böyük Kəsik", "İmişli"])): 310,
    }
    
    return distances_db.get(pair, 300)


def get_route_summary(parsed_data: dict, lang: str = "ru") -> dict:
    from_st = parsed_data.get("from_station")
    to_st = parsed_data.get("to_station")
    
    if not from_st or not to_st:
        return {"error": "Станции отправления или назначения не распознаны"}

    display_from = format_station_display(from_st, parsed_data, is_from=True, lang=lang)
    display_to = format_station_display(to_st, parsed_data, is_from=False, lang=lang)
    
    distance_km = calculate_distance(from_st, to_st, parsed_data)

    return {
        "route_display": f"{display_from} – {display_to}",
        "route_formatted": f"{display_from} – {display_to}",
        "distance_km": distance_km,
        "shipment_type": parsed_data.get("shipment_type"),
        "from_station_raw": from_st,
        "to_station_raw": to_st
    }

# Обёртка для совместимости с app.py и calculator.py
def get_route_info(nlu_data: dict, lang: str = "AZ") -> dict:
    return get_route_summary(nlu_data, lang=lang)

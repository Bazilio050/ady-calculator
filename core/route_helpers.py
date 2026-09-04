# core/route_helpers.py
import re
from data.stations_mapping import get_canonical_station_name

def normalize_simple(text: str) -> str:
    if not text:
        return ""
    return str(text).lower().replace("ə", "e").replace("ö", "o").replace("ü", "u").replace("ç", "c").replace("ş", "s")

# ------------------------------------------------------------------------------
# БЛОК 1: Нормализация станций NLU (БЕЗ ЖЕСТКИХ ПОДМЕН СТАНЦИИ НАЗНАЧЕНИЯ)
# ------------------------------------------------------------------------------
def normalize_nlu_stations(nlu_res: dict, raw_text: str = "") -> dict:
    if not isinstance(nlu_res, dict):
        nlu_res = {}

    res = nlu_res.copy()
    raw_norm = normalize_simple(raw_text)
    
    trk_keywords = ["trk", "трк", "туркм", "turkm", "туркменбаши", "туркменбашы", "turkmenbasy"]
    aktau_keywords = ["aktau", "актау"]
    kurik_keywords = ["kurik", "курык"]
    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "bk", "бк", "astara", "астара", "culfa", "джульфа", "elet", "алят"]

    # 1. Обработка Алята и Туркменбаши (ТРК) с сохранением порядка NLU
    if any(k in raw_norm for k in trk_keywords):
        from_norm = normalize_simple(str(res.get("from_station", "")))
        to_norm = normalize_simple(str(res.get("to_station", "")))
        
        if any(k in from_norm for k in trk_keywords) or (not res.get("from_station") and not res.get("to_station")):
            res["from_station"] = "Ələt-eksp.Türk."
        elif any(k in to_norm for k in trk_keywords):
            res["to_station"] = "Ələt-eksp.Türk."

    if any(k in raw_norm for k in aktau_keywords):
        if not res.get("from_station") or any(k in normalize_simple(str(res.get("from_station"))) for k in aktau_keywords):
            res["from_station"] = "Ələt eksport Aktau"
        elif not res.get("to_station"):
            res["to_station"] = "Ələt eksport Aktau"

    if any(k in raw_norm for k in kurik_keywords):
        if not res.get("from_station") or any(k in normalize_simple(str(res.get("from_station"))) for k in kurik_keywords):
            res["from_station"] = "Ələt eksport Kurik"
        elif not res.get("to_station"):
            res["to_station"] = "Ələt eksport Kurik"

    # 2. Перехват БК
    if str(res.get("from_station", "")).strip().upper() in ["БК", "BK"]:
        res["from_station"] = "Böyük Kəsik"
    if str(res.get("to_station", "")).strip().upper() in ["БК", "BK"]:
        res["to_station"] = "Böyük Kəsik"

    # 3. Перехват Баку-Товарная
    norm_from_raw = normalize_simple(str(res.get("from_station", "")))
    norm_to_raw = normalize_simple(str(res.get("to_station", "")))

    if any(k in norm_from_raw for k in ["baku yuk", "baki yuk", "баку тов", "баку товарная", "баку грузовой"]):
        res["from_station"] = "Bakı yük"
    if any(k in norm_to_raw for k in ["baku yuk", "baki yuk", "баку тов", "баку товарная", "баку грузовой"]):
        res["to_station"] = "Bakı yük"

    # 4. Каноническая нормализация через STATIONS_MAPPING
    if res.get("from_station"):
        res["from_station"] = get_canonical_station_name(res["from_station"])
    if res.get("to_station"):
        res["to_station"] = get_canonical_station_name(res["to_station"])

    # 5. Определение вида перевозки
    norm_from = normalize_simple(str(res.get("from_station", "")))
    norm_to = normalize_simple(str(res.get("to_station", "")))

    is_from_border = any(b in norm_from for b in border_keywords)
    is_to_border = any(b in norm_to for b in border_keywords)

    if is_from_border and is_to_border:
        res["shipment_type"] = "transit"
    elif is_from_border and not is_to_border:
        res["shipment_type"] = "import"
    elif not is_from_border and is_to_border:
        res["shipment_type"] = "export"
    else:
        res["shipment_type"] = "local"

    return res

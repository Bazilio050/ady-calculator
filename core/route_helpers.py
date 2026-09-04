# core/route_helpers.py
import re
from data.stations_mapping import get_canonical_station_name

def normalize_simple(text: str) -> str:
    if not text:
        return ""
    return str(text).lower().replace("ə", "e").replace("ö", "o").replace("ü", "u").replace("ç", "c").replace("ş", "s")

def normalize_nlu_stations(nlu_res: dict, raw_text: str = "") -> dict:
    if not isinstance(nlu_res, dict):
        nlu_res = {}

    res = nlu_res.copy()
    raw_norm = normalize_simple(raw_text)
    
    # Ключевые слова для Алята и порт-паромов
    trk_keywords = ["trk", "трк", "туркм", "turkm", "туркменбаши", "туркменбашы", "turkmenbasy", "паром трк"]
    aktau_keywords = ["aktau", "актау"]
    kurik_keywords = ["kurik", "курык"]
    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "bk", "бк", "astara", "астара", "culfa", "джульфа", "elet", "алят"]

    # 1. Обработка Алята и Туркменбаши (ТРК)
    if any(k in raw_norm for k in trk_keywords):
        words = raw_norm.split()
        if words and any(k in words[0] for k in trk_keywords):
            res["from_station"] = "Ələt-eksp.Türk."
        else:
            res["to_station"] = "Ələt-eksp.Türk."

    # 2. Обработка Алята для Актау / Курык
    if any(k in raw_norm for k in aktau_keywords):
        if not res.get("from_station") or any(k in normalize_simple(str(res.get("from_station"))) for k in aktau_keywords):
            res["from_station"] = "Ələt eksport Aktau"
        else:
            res["to_station"] = "Ələt eksport Aktau"

    if any(k in raw_norm for k in kurik_keywords):
        if not res.get("from_station") or any(k in normalize_simple(str(res.get("from_station"))) for k in kurik_keywords):
            res["from_station"] = "Ələt eksport Kurik"
        else:
            res["to_station"] = "Ələt eksport Kurik"

    # 3. Перехват аббревиатуры БК (Böyük Kəsik)
    if str(res.get("from_station", "")).strip().upper() in ["БК", "BK"]:
        res["from_station"] = "Böyük Kəsik"
    if str(res.get("to_station", "")).strip().upper() in ["БК", "BK"]:
        res["to_station"] = "Böyük Kəsik"

    # 4. Каноническая нормализация станций через STATIONS_MAPPING
    # Приводит любые варианты (например, "Баку тов") к строгому ключу ("Bakı yük")
    if res.get("from_station"):
        res["from_station"] = get_canonical_station_name(res["from_station"])
    if res.get("to_station"):
        res["to_station"] = get_canonical_station_name(res["to_station"])

    # 5. Определение вида перевозки (Транзит / Импорт / Экспорт / Местная)
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

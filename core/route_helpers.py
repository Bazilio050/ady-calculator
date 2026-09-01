# core/route_helpers.py
import re

def normalize_simple(text: str) -> str:
    if not text:
        return ""
    return str(text).lower().replace("ə", "e").replace("ö", "o").replace("ü", "u").replace("ç", "c").replace("ş", "s")

def normalize_nlu_stations(nlu_res: dict, raw_text: str = "") -> dict:
    if not isinstance(nlu_res, dict):
        nlu_res = {}

    res = nlu_res.copy()
    
    # Полный список синонимов для Туркменбаши/ТРК
    trk_synonyms = ["trk", "трк", "туркм", "turkm", "туркменбаши", "туркменбашы", "turkmenbasy", "turkmenbashi", "паром трк", "паром туркмен"]
    aktau_synonyms = ["aktau", "актау"]
    kurik_synonyms = ["kurik", "курык"]

    raw_norm = normalize_simple(raw_text)
    from_st = normalize_simple(res.get("from_station", ""))
    to_st = normalize_simple(res.get("to_station", ""))

    full_text = f"{raw_norm} {from_st} {to_st}"

    # Перехватываем Туркменбаши / ТРК
    if any(s in full_text for s in trk_synonyms):
        if any(s in from_st for s in trk_synonyms) or (raw_norm.split() and any(s in raw_norm.split()[0] for s in trk_synonyms)):
            res["from_station"] = "Ələt-eksp.Türk."
        else:
            res["to_station"] = "Ələt-eksp.Türk."

    # Перехватываем Актау
    elif any(s in full_text for s in aktau_synonyms):
        if any(s in from_st for s in aktau_synonyms):
            res["from_station"] = "Ələt-eksp.Aktau"
        else:
            res["to_station"] = "Ələt-eksp.Aktau"

    # Перехватываем Курык
    elif any(s in full_text for s in kurik_synonyms):
        if any(s in from_st for s in kurik_synonyms):
            res["from_station"] = "Ələt-eksp.Kurik"
        else:
            res["to_station"] = "Ələt-eksp.Kurik"

    # Определение вида перевозки
    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "astara", "астара", "culfa", "джульфа", "elet", "алят"]
    
    norm_from = normalize_simple(res.get("from_station", ""))
    norm_to = normalize_simple(res.get("to_station", ""))

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

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

    # Очищаем сырой текст и нормализуем
    raw_norm = normalize_simple(raw_text)
    
    # Синонимы для порта Туркменбаши (ТРК)
    trk_keywords = ["trk", "трк", "туркм", "turkm", "туркменбаши", "туркменбашы", "turkmenbasy", "паром трк"]
    aktau_keywords = ["aktau", "актау"]
    kurik_keywords = ["kurik", "курык"]
    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "bk", "бк", "astara", "астара", "culfa", "джульфа", "elet", "алят"]

    # 1. ПРИНУДИТЕЛЬНЫЙ ПЕРЕХВАТ ТРК / ТУРКМЕНБАШИ
    if any(k in raw_norm for k in trk_keywords):
        words = raw_norm.split()
        if words and any(k in words[0] for k in trk_keywords):
            res["from_station"] = "Ələt-eksp.Türk."
        else:
            res["to_station"] = "Ələt-eksp.Türk."

    # 2. ПРИНУДИТЕЛЬНЫЙ ПЕРЕХВАТ АКТАУ
    elif any(k in raw_norm for k in aktau_keywords):
        words = raw_norm.split()
        if words and any(k in words[0] for k in aktau_keywords):
            res["from_station"] = "Ələt-eksp.Aktau"
        else:
            res["to_station"] = "Ələt-eksp.Aktau"

    # 3. ПРИНУДИТЕЛЬНЫЙ ПЕРЕХВАТ КУРЫК
    elif any(k in raw_norm for k in kurik_keywords):
        words = raw_norm.split()
        if words and any(k in words[0] for k in kurik_keywords):
            res["from_station"] = "Ələt-eksp.Kurik"
        else:
            res["to_station"] = "Ələt-eksp.Kurik"

    # 3.1. ПРИНУДИТЕЛЬНАЯ ЗАМЕНА АББРЕВИАТУРЫ БК -> Böyük Kəsik
    if str(res.get("from_station", "")).strip().upper() == "БК":
        res["from_station"] = "Böyük Kəsik"
    if str(res.get("to_station", "")).strip().upper() == "БК":
        res["to_station"] = "Böyük Kəsik"

    # 4. Если станция отправления все еще пустая, берем первое слово запроса
    if not res.get("from_station"):
        words = [w for w in raw_text.split() if w.lower() not in ["4407", "крытый", "35т", "спс", "вагон"]]
        if words:
            res["from_station"] = words[0].title()

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

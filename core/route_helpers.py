# core/route_helpers.py

def normalize_simple(text: str) -> str:
    if not text:
        return ""
    return str(text).lower().replace("ə", "e").replace("ö", "o").replace("ü", "u").replace("ç", "c").replace("ş", "s")

def normalize_nlu_stations(nlu_res: dict, raw_text: str = "") -> dict:
    if not isinstance(nlu_res, dict):
        nlu_res = {}

    res = nlu_res.copy()
    from_st = str(res.get("from_station", "")).strip()
    to_st = str(res.get("to_station", "")).strip()
    full_text = f"{raw_text} {from_st} {to_st}".lower()
    first_words = normalize_simple(raw_text).split()[:2]

    port_keywords = ["aktau", "актау", "kurik", "курык", "trk", "трк", "туркмен", "liman"]
    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "astara", "астара", "culfa", "джульфа"]

    is_port_first = any(p in " ".join(first_words) for p in port_keywords)
    
    # 1. Если порт указан первым словом (ИМПОРТ ИЗ ПОРТА)
    if is_port_first:
        if "kurik" in " ".join(first_words) or "курык" in " ".join(first_words):
            res["from_station"] = "Ələt-eksp.Kurik"
        elif "aktau" in " ".join(first_words) or "актау" in " ".join(first_words):
            res["from_station"] = "Ələt-eksp.Aktau"
        elif any(k in " ".join(first_words) for k in ["trk", "трк", "туркмен"]):
            res["from_station"] = "Ələt-eksp.Türk."
        else:
            res["from_station"] = "Ələt-eksp."

        # Назначением становится вторая станция (например, Сальяны)
        if not to_st or any(p in normalize_simple(to_st) for p in port_keywords):
            # Ищем второе слово запроса
            words = raw_text.split()
            if len(words) > 1 and words[1].lower() not in ["4407", "крытый", "35т", "спс"]:
                res["to_station"] = words[1]

    # 2. Если порт указан в конце/середине (ЭКСПОРТ В ПОРТ ИЛИ ТРАНЗИТ)
    else:
        is_trk = any(k in full_text for k in ["trk", "трк", "туркмен", "turkmen"])
        is_aktau = any(k in full_text for k in ["aktau", "актау"])
        is_kurik = any(k in full_text for k in ["kurik", "курык"])
        
        if is_trk:
            res["to_station"] = "Ələt-eksp.Türk."
        elif is_aktau:
            res["to_station"] = "Ələt-eksp.Aktau"
        elif is_kurik:
            res["to_station"] = "Ələt-eksp.Kurik"

    # 3. Определение вида перевозки
    norm_from = normalize_simple(res.get("from_station", ""))
    norm_to = normalize_simple(res.get("to_station", ""))

    is_from_border_or_port = any(b in norm_from for b in border_keywords + port_keywords)
    is_to_border_or_port = any(b in norm_to for b in border_keywords + port_keywords)

    if is_from_border_or_port and is_to_border_or_port:
        res["shipment_type"] = "transit"
    elif is_from_border_or_port and not is_to_border_or_port:
        res["shipment_type"] = "import"
    elif not is_from_border_or_port and is_to_border_or_port:
        res["shipment_type"] = "export"
    else:
        res["shipment_type"] = "local"

    return res

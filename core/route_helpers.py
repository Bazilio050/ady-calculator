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
    
    words = [w for w in normalize_simple(raw_text).split() if w not in ["4407", "крытый", "35т", "спс", "вагон"]]

    port_keywords = ["aktau", "актау", "kurik", "курык", "trk", "трк", "туркмен", "liman"]
    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "astara", "астара", "culfa", "джульфа"]

    # 1. Проверяем, стоит ли порт ПЕРВЫМ словом (ИМПОРТ ИЗ ПОРТА)
    is_port_first = len(words) > 0 and any(p in words[0] for p in port_keywords)

    if is_port_first:
        if "kurik" in words[0] or "курык" in words[0]:
            res["from_station"] = "Ələt-eksp.Kurik"
        elif "aktau" in words[0] or "актау" in words[0]:
            res["from_station"] = "Ələt-eksp.Aktau"
        elif any(k in words[0] for k in ["trk", "трк", "туркмен"]):
            res["from_station"] = "Ələt-eksp.Türk."
        else:
            res["from_station"] = "Ələt-eksp."

        if len(words) > 1 and not any(p in words[1] for p in port_keywords):
            res["to_station"] = words[1].title()

    # 2. Во всех остальных случаях (ЭКСПОРТ В ПОРТ ИЛИ ТРАНЗИТ ЧЕРЕЗ ПОРТ)
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
        elif any(k in full_text for k in ["алят", "alat", "elet"]) and not res.get("to_station"):
            res["to_station"] = "Ələt-eksp."

        # Если первая станция — Апшерон / Ялама и т.д.
        if len(words) > 0 and not is_port_first:
            res["from_station"] = words[0].title()

    # 3. Определение вида перевозки
    norm_from = normalize_simple(res.get("from_station", ""))
    norm_to = normalize_simple(res.get("to_station", ""))

    is_from_border = any(b in norm_from for b in border_keywords)
    is_from_port = any(p in norm_from for p in port_keywords)
    is_to_border = any(b in norm_to for b in border_keywords)
    is_to_port = any(p in norm_to for p in port_keywords)

    if (is_from_border or is_from_port) and (is_to_border or is_to_port):
        res["shipment_type"] = "transit"
    elif (is_from_border or is_from_port) and not (is_to_border or is_to_port):
        res["shipment_type"] = "import"
    elif not (is_from_border or is_from_port) and (is_to_border or is_to_port):
        res["shipment_type"] = "export"
    else:
        res["shipment_type"] = "local"

    return res

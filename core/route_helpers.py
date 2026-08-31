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

    # 1. Автоматическое извлечение станции назначения из сырого текста, если NLU её упустил
    is_trk = any(k in full_text for k in ["trk", "трк", "туркмен", "turkmen"])
    is_aktau = any(k in full_text for k in ["aktau", "актау"])
    is_kurik = any(k in full_text for k in ["kurik", "курык"])
    
    if is_trk:
        res["to_station"] = "Ələt-eksp.Türk."
    elif is_aktau:
        res["to_station"] = "Ələt-eksp.Aktau"
    elif is_kurik:
        res["to_station"] = "Ələt-eksp.Kurik"
    elif not to_st and any(k in full_text for k in ["алят", "alat", "elet"]):
        res["to_station"] = "Ələt-eksp."

    # 2. Обновляем переменные после определения назначения
    from_st = str(res.get("from_station", "")).strip()
    to_st = str(res.get("to_station", "")).strip()

    norm_from = normalize_simple(from_st)
    norm_to = normalize_simple(to_st)
    norm_raw = normalize_simple(raw_text)

    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "astara", "астара", "culfa", "джульфа"]
    port_keywords = ["aktau", "актау", "kurik", "курык", "trk", "трк", "туркмен", "alat", "elet", "алят", "liman"]

    is_from_border = any(b in norm_from or b in norm_raw.split()[:2] for b in border_keywords)
    is_to_border = any(b in norm_to for b in border_keywords)
    is_to_port_or_export = any(p in full_text for p in port_keywords)
    is_to_absheron = "absheron" in norm_to or "abseron" in norm_to or "апшерон" in full_text or "абшерон" in full_text

    # 3. Определение вида перевозки
    if is_from_border and is_to_absheron:
        res["shipment_type"] = "import"
    elif is_from_border and (is_to_border or is_to_port_or_export):
        res["shipment_type"] = "transit"
    elif is_from_border and not (is_to_border or is_to_port_or_export):
        res["shipment_type"] = "import"
    elif not is_from_border and (is_to_border or is_to_port_or_export):
        res["shipment_type"] = "export"

    return res

# core/route_helpers.py

def normalize_simple(text: str) -> str:
    return str(text).lower().replace("ə", "e").replace("ö", "o").replace("ü", "u")

def normalize_nlu_stations(nlu_res: dict, raw_text: str = "") -> dict:
    if not isinstance(nlu_res, dict):
        return nlu_res

    res = nlu_res.copy()
    from_st = str(res.get("from_station", "")).strip()
    to_st = str(res.get("to_station", "")).strip()
    full_text = f"{raw_text} {from_st} {to_st}".lower()
    
    norm_from = normalize_simple(from_st)
    norm_to = normalize_simple(to_st)
    norm_raw = normalize_simple(raw_text)

    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "astara", "астара", "culfa", "джульфа"]
    port_keywords = ["aktau", "актау", "kurik", "курык", "trk", "туркмен", "alat", "elet", "алят", "liman"]

    is_from_border = any(b in norm_from or b in norm_raw.split()[:2] for b in border_keywords)
    is_to_border = any(b in norm_to for b in border_keywords)
    is_to_port_or_export = any(p in full_text for p in port_keywords) and any(e in full_text for e in ["eksp", "эксп", "экс", "export", "aktau", "актау", "kurik", "курык", "liman"])

    is_to_absheron = "absheron" in norm_to or "abseron" in norm_to or "апшерон" in full_text or "абшерон" in full_text

    # Определение вида перевозки
    if is_from_border and is_to_absheron:
        res["shipment_type"] = "import"
    elif is_from_border and (is_to_border or is_to_port_or_export):
        res["shipment_type"] = "transit"
    elif is_from_border and not (is_to_border or is_to_port_or_export):
        res["shipment_type"] = "import"
    elif not is_from_border and (is_to_border or is_to_port_or_export):
        res["shipment_type"] = "export"

    shipment_type = res.get("shipment_type", "export")
    is_transit_or_export = shipment_type in ["transit", "export"]

    # Приведение станций назначения к экспортным стыкам
    if any(a in full_text for a in ["alat", "elet", "алят", "aktau", "актау", "kurik", "курык"]):
        if "kurik" in full_text or "курык" in full_text:
            res["to_station"] = "Ələt-eksp.Kurik"
        elif "aktau" in full_text or "актау" in full_text:
            res["to_station"] = "Ələt-eksp.Aktau"
        elif "türk" in full_text or "туркмен" in full_text or "трк" in full_text:
            res["to_station"] = "Ələt-eksp.Türk."
        elif any(e in full_text for e in ["eksp", "эксп", "экс", "export"]) or is_transit_or_export:
            res["to_station"] = "Ələt-eksp."
        else:
            res["to_station"] = "Ələt"

    elif any(k in full_text for k in ["kesik", "кясик", "касик"]):
        if is_transit_or_export or any(e in full_text for e in ["eksp", "эксп", "экс"]):
            res["to_station"] = "Böyük Kəsik-eksp."
        else:
            res["to_station"] = "Böyük Kəsik"

    elif "astara" in full_text or "астара" in full_text:
        if is_transit_or_export or any(e in full_text for e in ["eksp", "эксп", "экс"]):
            res["to_station"] = "Astara (eks.aşır)"
        else:
            res["to_station"] = "Astara"

    return res

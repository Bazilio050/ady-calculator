# core/route_helpers.py

def normalize_nlu_stations(nlu_res: dict, raw_text: str = "") -> dict:
    if not isinstance(nlu_res, dict):
        return nlu_res

    res = nlu_res.copy()
    from_st = str(res.get("from_station", "")).strip()
    to_st = str(res.get("to_station", "")).strip()
    full_text = f"{raw_text} {from_st} {to_st}".lower()

    # Списки ключевых слов
    border_keywords = ["yalama", "ялама", "böyük kəsik", "boyuk", "беюк", "кясик", "astara", "астара", "culfa", "джульфа"]
    port_keywords = ["aktau", "актау", "kurik", "курык", "trk", "туркмен"]

    # Определение граничных точек
    is_from_border = any(b in normalize_simple(from_st) or b in full_text for b in border_keywords if b in full_text)
    is_to_border = any(b in normalize_simple(to_st) or b in full_text for b in border_keywords if b in full_text)
    is_to_port = any(p in full_text for p in port_keywords)

    is_from_border_or_port = is_from_border
    is_to_border_or_port = is_to_border or is_to_port

    # 1. Жесткое определение вида перевозки (shipment_type)
    if is_from_border_or_port and is_to_border_or_port:
        res["shipment_type"] = "transit"
    elif is_from_border and not is_to_border_or_port:
        res["shipment_type"] = "import"
    elif not is_from_border_or_port and is_to_border_or_port:
        res["shipment_type"] = "export"

    shipment_type = res.get("shipment_type", "export")
    is_transit_or_export = shipment_type in ["transit", "export"]

    # 2. Нормализация станции НАЗНАЧЕНИЯ (to_station)
    # Алят и Порты
    if any(a in full_text for a in ["alat", "ələt", "алят"]):
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

    # Беюк Кясик
    elif any(k in full_text for k in ["kesik", "кясик", "касик"]):
        if is_transit_or_export or any(e in full_text for e in ["eksp", "эксп", "экс"]):
            res["to_station"] = "Böyük Kəsik-eksp."
        else:
            res["to_station"] = "Böyük Kəsik"

    # Астара
    elif "astara" in full_text or "астара" in full_text:
        if is_transit_or_export or any(e in full_text for e in ["eksp", "эксп", "экс"]):
            res["to_station"] = "Astara (eks.aşır)"
        else:
            res["to_station"] = "Astara"

    return res

def normalize_simple(text: str) -> str:
    return str(text).lower().replace("ə", "e").replace("ö", "o").replace("ü", "u")

# core/route_helpers.py

def normalize_nlu_stations(nlu_res: dict, raw_text: str = "") -> dict:
    """
    Модуль бизнес-логики нормализации станций и определения типа перевозки (ADY).
    """
    if not isinstance(nlu_res, dict):
        return nlu_res

    res = nlu_res.copy()
    from_st = str(res.get("from_station", "")).strip()
    to_st = str(res.get("to_station", "")).strip()

    from_lower = from_st.lower()
    to_lower = to_st.lower()
    full_text = f"{raw_text} {from_lower} {to_lower}".lower()

    # Пограничные стыки ADY
    border_keywords = [
        "yalama", "ялама", 
        "böyük kəsik", "boyuk", "беюк", "кясик", 
        "astara", "астара", 
        "culfa", "джульфа"
    ]

    is_from_border = any(b in from_lower for b in border_keywords)
    is_to_border = any(b in to_lower for b in border_keywords)

    is_from_port = any(b in full_text for b in ["aktau", "актау", "kurik", "курык", "trk", "туркмен"])
    is_to_port = any(b in full_text for b in ["aktau", "актау", "kurik", "курык", "trk", "туркмен"])

    if (is_from_border or is_from_port) and (is_to_border or is_to_port):
        res["shipment_type"] = "transit"

    shipment_type = res.get("shipment_type", "export")

    # Обработка станции назначения
    if "kurik" in full_text or "курык" in full_text:
        res["to_station"] = "Ələt eksport Kurik"
    elif "aktau" in full_text or "актау" in full_text:
        res["to_station"] = "Ələt eksport Aktau"
    elif "türk" in full_text or "туркмен" in full_text or "трк" in full_text:
        res["to_station"] = "Ələt eksport-Türk."
    elif any(b in full_text for b in ["alat", "ələt", "алят"]):
        if any(e in full_text for e in ["eksp", "эксп", "экс", "export"]) or shipment_type == "export":
            res["to_station"] = "Ələt-eksp."
        else:
            res["to_station"] = "Ələt"

    return res

    res = nlu_res.copy()
    from_st = str(res.get("from_station", "")).strip()
    to_st = str(res.get("to_station", "")).strip()

    from_lower = from_st.lower()
    to_lower = to_st.lower()

    # Пограничные стыки ADY
    border_keywords = [
        "yalama", "ялама", 
        "böyük kəsik", "boyuk", "беюк", "кясик", 
        "astara", "астара", 
        "culfa", "джульфа"
    ]

    is_from_border = any(b in from_lower for b in border_keywords)
    is_to_border = any(b in to_lower for b in border_keywords)

    is_from_port = any(b in from_lower for b in ["aktau", "актау", "kurik", "курык", "trk", "туркмен"])
    is_to_port = any(b in to_lower for b in ["aktau", "актау", "kurik", "курык", "trk", "туркмен"])

    # Определение транзита
    if (is_from_border or is_from_port) and (is_to_border or is_to_port):
        res["shipment_type"] = "transit"

    shipment_type = res.get("shipment_type", "export")

    # Обработка станции назначения (TO)
    if "kurik" in to_lower or "курык" in to_lower:
        res["to_station"] = "Ələt eksport Kurik"
    elif "aktau" in to_lower or "актау" in to_lower:
        res["to_station"] = "Ələt eksport Aktau"
    elif "türk" in to_lower or "туркмен" in to_lower or "трк" in to_lower:
        res["to_station"] = "Ələt eksport-Türk."
    elif any(b in to_lower for b in ["alat", "ələt", "алят"]):
        if shipment_type == "transit":
            res["to_station"] = "Ələt eksport Kurik"
        else:
            # Мапим экспортный Алят на эталонную станцию матрицы Distances.txt
            res["to_station"] = "Ələt"

    # Обработка станции отправления (FROM)
    if shipment_type == "transit":
        if any(b in to_lower for b in ["böyük kəsik", "boyuk", "кясик", "беюк"]):
            res["to_station"] = "Böyük Kəsik (eksport)"
        elif any(b in to_lower for b in ["astara", "астара"]):
            res["to_station"] = "Astara (eks.aşır)"
        elif any(b in to_lower for b in ["yalama", "ялама"]):
            res["to_station"] = "Yalama (eksport)"

        if any(b in from_lower for b in ["böyük kəsik", "boyuk", "кясик", "беюк"]):
            res["from_station"] = "Böyük Kəsik (eksport)"
        elif any(b in from_lower for b in ["astara", "астара"]):
            res["from_station"] = "Astara (eks.aşır)"
        elif any(b in from_lower for b in ["yalama", "ялама"]):
            res["from_station"] = "Yalama (eksport)"

    return res

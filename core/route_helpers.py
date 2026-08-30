# core/route_helpers.py

def normalize_nlu_stations(nlu_res: dict) -> dict:
    """
    Модуль бизнес-логики нормализации станций и определения типа перевозки (ADY).
    Приводит пользовательский ввод от NLU к эталонным названиям из Distances.txt.
    """
    if not isinstance(nlu_res, dict):
        return nlu_res

    res = nlu_res.copy()
    from_st = str(res.get("from_station", "")).strip()
    to_st = str(res.get("to_station", "")).strip()

    from_lower = from_st.lower()
    to_lower = to_st.lower()

    # Ключевые слова пограничных стыков и портов ADY
    border_keywords = [
        "yalama", "ялама", 
        "böyük kəsik", "boyuk", "беюк", "кясик", 
        "astara", "астара", 
        "culfa", "джульфа",
        "alat", "ələt", "алят",
        "aktau", "актау", "kurik", "курык", "trk", "туркмен"
    ]

    is_from_border = any(b in from_lower for b in border_keywords)
    is_to_border = any(b in to_lower for b in border_keywords)

    # Правило 1: Принцип двух границ — если обе станции являются стыками/портами, это 100% транзит
    if is_from_border and is_to_border:
        res["shipment_type"] = "transit"

    shipment_type = res.get("shipment_type", "import")

    # Правило 2: Обработка станции назначения (TO)
    if "kurik" in to_lower or "курык" in to_lower:
        res["to_station"] = "Ələt eksport Kurik"
    elif "aktau" in to_lower or "актау" in to_lower:
        res["to_station"] = "Ələt eksport Aktau"
    elif "türk" in to_lower or "туркмен" in to_lower or "трк" in to_lower:
        res["to_station"] = "Ələt eksport-Türk."
    elif shipment_type == "transit":
        if any(b in to_lower for b in ["böyük kəsik", "boyuk", "кясик", "беюк"]):
            res["to_station"] = "Böyük Kəsik (eksport)"
        elif any(b in to_lower for b in ["astara", "астара"]):
            res["to_station"] = "Astara (eks.aşır)"
        elif any(b in to_lower for b in ["yalama", "ялама"]):
            res["to_station"] = "Yalama (eksport)"
        elif any(b in to_lower for b in ["alat", "ələt", "алят"]):
            res["to_station"] = "Ələt eksport"

    # Правило 3: Обработка станции отправления (FROM)
    if shipment_type == "transit":
        if any(b in from_lower for b in ["böyük kəsik", "boyuk", "кясик", "беюк"]):
            res["from_station"] = "Böyük Kəsik (eksport)"
        elif any(b in from_lower for b in ["astara", "астара"]):
            res["from_station"] = "Astara (eks.aşır)"
        elif any(b in from_lower for b in ["yalama", "ялама"]):
            res["from_station"] = "Yalama (eksport)"
        elif any(b in from_lower for b in ["alat", "ələt", "алят"]):
            res["from_station"] = "Ələt eksport"

    return res

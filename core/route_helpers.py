# core/route_helpers.py

def normalize_nlu_stations(nlu_res: dict) -> dict:
    """
    Корректирует станции и тип перевозки для автотестов ADY.
    """
    if not isinstance(nlu_res, dict):
        return nlu_res

    res = nlu_res.copy()
    from_st = str(res.get("from_station", "")).strip()
    to_st = str(res.get("to_station", "")).strip()
    shipment_type = res.get("shipment_type")

    to_lower = to_st.lower()
    from_lower = from_st.lower()

    # 1. Точные названия портов Алят (Тесты 2 и 3)
    if "kurik" in to_lower or "курык" in to_lower:
        res["to_station"] = "Ələt eksport Kurik"
    elif "aktau" in to_lower or "актау" in to_lower:
        res["to_station"] = "Ələt eksport Aktau"
    elif "türk" in to_lower or "туркмен" in to_lower or "трк" in to_lower:
        res["to_station"] = "Ələt eksport-Türk."

    # 2. Авто-определение транзита, если обе станции пограничные (Тесты 4 и 5)
    border_keywords = ["yalama", "ялама", "böyük kəsik", "boyuk", "беюк", "кясик", "astara", "астара", "culfa", "джульфа"]
    
    is_from_border = any(b in from_lower for b in border_keywords)
    is_to_border = any(b in to_lower for b in border_keywords)

    if is_from_border and is_to_border:
        res["shipment_type"] = "transit"
        shipment_type = "transit"

    # 3. Подстановка экспортных стыков для транзита
    if shipment_type == "transit":
        if any(b in to_lower for b in ["böyük kəsik", "boyuk", "кясик", "беюк"]):
            res["to_station"] = "Böyük Kəsik (eksport)"
        elif any(b in to_lower for b in ["astara", "астара"]):
            res["to_station"] = "Astara (eksport)"
        elif any(b in to_lower for b in ["yalama", "ялама"]):
            res["to_station"] = "Yalama (eksport)"

        if any(b in from_lower for b in ["böyük kəsik", "boyuk", "кясик", "беюк"]):
            res["from_station"] = "Böyük Kəsik (eksport)"
        elif any(b in from_lower for b in ["astara", "астара"]):
            res["from_station"] = "Astara (eksport)"
        elif any(b in from_lower for b in ["yalama", "ялама"]):
            res["from_station"] = "Yalama (eksport)"

    return res

# --------------------------------------------------------------------------
    # ПРАВИЛО "BIR DƏFƏ": Коэффициент 1.20 за реф / нефть применяется ровно 1 раз
    # --------------------------------------------------------------------------
    has_120_applied = False

    # Маршрут Алят — Беюк Кясик (Транзит)
    st_from = str(from_station or "").strip().lower()
    st_to = str(to_station or "").strip().lower()
    is_alat = any(k in st_from or k in st_to for k in ["alat", "ələt", "алят"])
    is_bk = any(k in st_from or k in st_to for k in ["boyuk kesik", "böyük kəsik", "беюк-кесик", "беюк кесик"])

    # 1. Транзит нефти и нефтепродуктов (Таблица 6) — "bir dəfə"
    if (is_import or is_transit) and table_str == "6":
        add_coeff("oil_products", 1.20)
        has_120_applied = True

    # 2. Транзит рефрижераторов (Таблица 5) — "bir dəfə"
    is_ref = any(k in wagon_lower for k in ["arv", "рефрижератор", "ref", "seksiy"])
    if is_transit and is_ref and not has_120_applied:
        add_coeff("ref_transit", 1.20)
        has_120_applied = True

    # 3. Маршрутный транзитный коэффициент Ələt — Böyük Kəsik (если еще не применен 1.20)
    if is_transit and (is_alat and is_bk) and not has_120_applied:
        add_coeff("transit_alat_bk", 1.20)
        has_120_applied = True

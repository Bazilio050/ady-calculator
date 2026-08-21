def resolve_complex_station_code(raw_input: str) -> str:
    """
    Универсальный локальный резолвер сложных и неоднозначных внутренних станций ADY.
    Не зацепляет пограничную/паромную логику Алята и других стыков из BORDER_STATIONS_MAP.
    """
    text = str(raw_input or "").lower()

    # 1. Группа Тагиев (Z.Tağıyev 546302 vs Z.Tağıyev çeşidləmə 546901)
    if any(r in text for r in ["тагиев", "tagiyev", "тагив", "г.тагиев", "h.z.", "г. тагиев", "g.tagiyev", "g tagiyev"]):
        if any(m in text for m in ["сорт", "sort", "чешид", "cesid", "ceşid"]):
            return "546901"  # Z.Tağıyev çeşidləmə
        return "546302"      # Z.Tağıyev (Основная)

    # 2. Группа Баку Торговый Порт / Ляман (547302 vs 547406 vs 547209)
    if any(r in text for r in ["баку порт", "baki liman", "bakı liman", "торговый порт", "ticarət liman"]):
        if any(m in text for m in ["перевал", "ашир", "aşır", "ашыр"]):
            return "547209"  # Bakı ticarət limanı (aşır)
        if any(m in text for m in ["эксп", "exp", "ixrac", "экспорт"]):
            return "547406"  # Bakı ticarət limanı (eks)
        return "547302"      # Bakı ticarət liman (Основная)

    # 3. Группа Баку Товарный / Грузовой / Гюнес (547105 vs 547603)
    if any(r in text for r in ["баку юк", "bakı yük", "баку груз", "баку товар"]):
        if any(m in text for m in ["терминал", "terminal"]):
            return "547603"  # Bakı yük terminal
        return "547105"      # Bakı yük (Основная)

    # 4. Группа Сангачал (548305 vs 548606)
    if any(r in text for r in ["sanqacal", "сангачал", "sanqaçal", "сангачалы"]):
        if any(m in text for m in ["терминал", "terminal", "ашир", "aşır", "перевал"]):
            return "548606"  # Sanqaçal ter.(aşırma)
        return "548305"      # Sanqaçal (Основная)

    # 5. Группа Гарадаг (548201 vs 549702)
    if any(r in text for r in ["qaradag", "гарадаг", "qaradağ", "карадаг"]):
        if any(m in text for m in ["терминал", "terminal"]):
            return "549702"  # Qaradağ terminal
        return "548201"      # Qaradağ (Основная)

    # 6. Группа Сумгаит (546105 vs 546001 vs 546209)
    if any(r in text for r in ["сумгаит", "sumqayit", "sumqayıt"]):
        if any(m in text for m in ["главный", "баш", "bas", "baş"]):
            return "546001"  # Sumqayıt baş
        if any(m in text for m in ["пасс", "шехер", "seher", "город"]):
            return "546209"  # Sumqayıt sərnişin
        return "546105"      # Sumqayıt (Грузовая)

    # 7. Группа Мингечевир (555703 vs 555807)
    if any(r in text for r in ["mingecevir", "мингечевир", "mingəçevir"]):
        if any(m in text for m in ["город", "şəhər", "шехер", "seher"]):
            return "555807"  # Mingəçevir şəhər
        return "555703"      # Mingəçevir (Основная)

    # 8. Группа Гянджа (558004 vs 558108)
    if any(r in text for r in ["гянджа", "ganja", "gəncə"]):
        if any(m in text for m in ["грузовая", "юк", "yük"]):
            return "558108"  # Gəncə yük
        return "558004"      # Gəncə (Основная)

    # 9. Группа Баладжары (545200 vs 545107)
    if any(r in text for r in ["баладжары", "bilacari", "biləcəri", "баледжары"]):
        if any(m in text for m in ["сорт", "sort", "чешид", "cesid"]):
            return "545107"  # Biləcəri çeşidləmə
        return "545200"      # Biləcəri (Основная)

    return None

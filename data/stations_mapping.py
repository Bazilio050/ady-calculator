# ==============================================================================
# СПРАВОЧНИК ЛОКАЛИЗАЦИИ НАЗВАНИЙ СТАНЦИЙ ADY (AZ / RU / EN)
# ==============================================================================

STATIONS_MAPPING = {
    "Yalama (eksport)": {
        "AZ": "Yalama-eksp.",
        "RU": "Ялама-эксп.",
        "EN": "Yalama-exp."
    },
    "Böyük Kəsik (eksport)": {
        "AZ": "Böyük Kəsik-eksp.",
        "RU": "Беюк-Кясик-эксп.",
        "EN": "Boyuk Kasik-exp."
    },
    "Böyük Kəsik": {
        "AZ": "Böyük Kəsik",
        "RU": "Беюк-Кясик",
        "EN": "Boyuk Kasik"
    },
    "Astara (eksport)": {
        "AZ": "Astara-eksp.",
        "RU": "Астара-эксп.",
        "EN": "Astara-exp."
    },
    "Astara": {
        "AZ": "Astara",
        "RU": "Астара",
        "EN": "Astara"
    },
    "Culfa (eksport)": {
        "AZ": "Culfa-eksp.",
        "RU": "Джульфа-эксп.",
        "EN": "Julfa-exp."
    },
    "Culfa": {
        "AZ": "Culfa",
        "RU": "Джульфа",
        "EN": "Julfa"
    },
    "Ələt eksport": {
        "AZ": "Ələt-eksp.",
        "RU": "Алят-эксп.",
        "EN": "Alat-exp."
    },
    "Ələt-eksp.": {
        "AZ": "Ələt-eksp.",
        "RU": "Алят-эксп.",
        "EN": "Alat-exp."
    },
    "Ələt eksport Kurik": {
        "AZ": "Ələt-eksp.Kurik",
        "RU": "Алят-эксп.Курык",
        "EN": "Alat-exp.Kuryk"
    },
    "Ələt eksport Aktau": {
        "AZ": "Ələt-eksp.Aktau",
        "RU": "Алят-эксп.Актау",
        "EN": "Alat-exp.Aktau"
    },
    "Ələt eksport-Türk.": {
        "AZ": "Ələt-eksp.Türk.",
        "RU": "Алят-эксп.Турк.",
        "EN": "Alat-exp.Turk."
    },
    "Ələt": {
        "AZ": "Ələt",
        "RU": "Алят",
        "EN": "Alat"
    },
    "Ələt yeni": {
        "AZ": "Ələt yeni",
        "RU": "Алят-Новый",
        "EN": "Alat-New"
    },
    "Abşeron": {
        "AZ": "Abşeron",
        "RU": "Апшерон",
        "EN": "Absheron"
    },
    "Bakı yük": {
        "AZ": "Bakı yük",
        "RU": "Баку-Товарная",
        "EN": "Baku Freight"
    },
    "Bakı yük terminal": {
        "AZ": "Bakı yük terminalı",
        "RU": "Баку-Товарная (терминал)",
        "EN": "Baku Freight Terminal"
    },
    "Biləcəri": {
        "AZ": "Biləcəri",
        "RU": "Баладжары",
        "EN": "Bilajari"
    },
    "Gəncə": {
        "AZ": "Gəncə",
        "RU": "Гянджа",
        "EN": "Ganja"
    },
    "Sumqayıt": {
        "AZ": "Sumqayıt",
        "RU": "Сумгаит",
        "EN": "Sumgayit"
    },
    "Xırdalan": {
        "AZ": "Xırdalan",
        "RU": "Хырдалан",
        "EN": "Khirdalan"
    },
    "Salyan": {
        "AZ": "Salyan",
        "RU": "Сальяны",
        "EN": "Salyan"
    },
    "İmişli": {
        "AZ": "İmişli",
        "RU": "Имишли",
        "EN": "Imishli"
    },
    "Yevlax": {
        "AZ": "Yevlax",
        "RU": "Евлах",
        "EN": "Yevlakh"
    },
    "Mingəçevir": {
        "AZ": "Mingəçevir",
        "RU": "Мингечевир",
        "EN": "Mingachevir"
    },
    "Tovuz": {
        "AZ": "Tovuz",
        "RU": "Товуз",
        "EN": "Tovuz"
    },
    "Ağstafa": {
        "AZ": "Ağstafa",
        "RU": "Акстафа",
        "EN": "Agstafa"
    },
    "Qazax": {
        "AZ": "Qazax",
        "RU": "Казах",
        "EN": "Gazakh"
    },
    "Şəmkir": {
        "AZ": "Şəmkir",
        "RU": "Шамхор",
        "EN": "Shamkir"
    },
    "Xaçmaz": {
        "AZ": "Xaçmaz",
        "RU": "Хачмаз",
        "EN": "Khachmaz"
    },
    "Xudat": {
        "AZ": "Xudat",
        "RU": "Худат",
        "EN": "Khudat"
    },
    "Şirvan": {
        "AZ": "Şirvan",
        "RU": "Ширван",
        "EN": "Shirvan"
    }
}

def get_localized_station_name(station_name: str, lang: str = "AZ") -> str:
    if not station_name:
        return ""

    clean_name = station_name.strip()
    if clean_name in ["Ələt eksport", "Ələt-eksp."]:
        return STATIONS_MAPPING["Ələt eksport"].get(lang, "Ələt-eksp.")

    if clean_name in STATIONS_MAPPING:
        return STATIONS_MAPPING[clean_name].get(lang, clean_name)

    return clean_name

def format_station_display(station_name: str, station_code: str = "", lang: str = "AZ") -> str:
    """
    Безопасное форматирование названия станции и кода для UI.
    Не влияет на внутренний поиск калькулятора.
    """
    if not station_name:
        return ""
    
    localized_name = get_localized_station_name(station_name, lang=lang)
    
    if station_code and str(station_code).strip():
        return f"{localized_name} ({str(station_code).strip()})"
    
    return localized_name

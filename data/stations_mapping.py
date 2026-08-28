# ==============================================================================
# СПРАВОЧНИК ЛОКАЛИЗАЦИИ НАЗВАНИЙ СТАНЦИЙ ADY (AZ / RU / EN)
# ==============================================================================

STATIONS_MAPPING = {
    "Yalama (eksport)": {
        "AZ": "Yalama eksport",
        "RU": "Ялама (эксп)",
        "EN": "Yalama (exp)"
    },
    "Böyük Kəsik (eksport)": {
        "AZ": "Böyük Kəsik eksport",
        "RU": "Беюк-Кясик (эксп)",
        "EN": "Boyuk Kasik (exp)"
    },
    "Böyük Kəsik": {
        "AZ": "Böyük Kəsik",
        "RU": "Беюк-Кясик",
        "EN": "Boyuk Kasik"
    },
    "Astara (eksport)": {
        "AZ": "Astara eksport",
        "RU": "Астара (эксп)",
        "EN": "Astara (exp)"
    },
    "Astara": {
        "AZ": "Astara",
        "RU": "Астара",
        "EN": "Astara"
    },
    "Culfa (eksport)": {
        "AZ": "Culfa eksport",
        "RU": "Джульфа (эксп)",
        "EN": "Julfa (exp)"
    },
    "Culfa": {
        "AZ": "Culfa",
        "RU": "Джульфа",
        "EN": "Julfa"
    },
    "Ələt eksport": {
        "AZ": "Ələt eksport",
        "RU": "Алят (эксп)",
        "EN": "Alat (exp)"
    },
    "Ələt-eksp.": {
        "AZ": "Ələt eksport",
        "RU": "Алят (эксп)",
        "EN": "Alat (exp)"
    },
    "Ələt eksport Kurik": {
        "AZ": "Ələt eksport Kurik",
        "RU": "Алят эксп. (Курык)",
        "EN": "Alat exp. (Kuryk)"
    },
    "Ələt eksport Aktau": {
        "AZ": "Ələt eksport Aktau",
        "RU": "Алят эксп. (Актау)",
        "EN": "Alat exp. (Aktau)"
    },
    "Ələt eksport-Türk.": {
        "AZ": "Ələt eksport Türkmenbaşı",
        "RU": "Алят эксп. (Туркменбаши)",
        "EN": "Alat exp. (Turkmenbashi)"
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
    """Возвращает переведенное название станции или оригинал, если перевода нет"""
    if not station_name:
        return ""
    
    # Прямая проверка по словарю
    if station_name in STATIONS_MAPPING:
        return STATIONS_MAPPING[station_name].get(lang, station_name)
    
    return station_name

# ==============================================================================
# СПРАВОЧНИК И ДВИЖОК ПОИСКА СТАНЦИЙ ADY (AZ / RU / EN / ЕСР)
# ==============================================================================

STATIONS_MAPPING = {
    # --- Буквы A, B, C ---
    "Abşeron": {"code": "548004", "AZ": ["Abşeron"], "RU": ["Апшерон", "Абшерон"], "EN": ["Absheron"]},
    "Ağdam": {"code": "555506", "AZ": ["Ağdam"], "RU": ["Агдам"], "EN": ["Aghdam"]},
    "Ağstafa": {"code": "557200", "AZ": ["Ağstafa"], "RU": ["Акстафа", "Агстафа"], "EN": ["Agstafa"]},
    "Alabaşlı": {"code": "556602", "AZ": ["Alabaşlı"], "RU": ["Алабашлы"], "EN": ["Alabashli"]},
    "Astara": {"code": "554109", "AZ": ["Astara"], "RU": ["Астара"], "EN": ["Astara"]},
    "Astara (eks.aşır)": {"code": "554503", "AZ": ["Astara (eks.aşır)"], "RU": ["Астара (эксп.перевалка)"], "EN": ["Astara (exp.transshipment)"]},
    "Atbulaq": {"code": "548907", "AZ": ["Atbulaq"], "RU": ["Атбулак"], "EN": ["Atbulag"]},
    "Bakı yük": {
        "code": "547105", 
        "AZ": ["Bakı yük", "Bakı yuk", "Baku yuk", "Bakı-Yük"], 
        "RU": ["Баку-Товарная", "Баку тов", "Баку-тов", "Баку грузовой", "Баку товарный"], 
        "EN": ["Baku Freight", "Baku freight", "Baku tov"]
    },
    "Bakı yük terminal": {
        "code": "547603", 
        "AZ": ["Bakı yük terminalı"], 
        "RU": ["Баку-Товарная (терминал)", "Баку тов terminal"], 
        "EN": ["Baku Freight Terminal"]
    },
    "Balakən": {"code": "559704", "AZ": ["Balakən"], "RU": ["Белоканы"], "EN": ["Balakan"]},
    "Bartaz": {"code": "551308", "AZ": ["Bartaz"], "RU": ["Бартаз"], "EN": ["Bartaz"]},
    "Barxudarlı": {"code": "557501", "AZ": ["Barxudarlı"], "RU": ["Бархударлы"], "EN": ["Barkhudarli"]},
    "Başbaşı": {"code": "550700", "AZ": ["Başbaşı"], "RU": ["Башбаши"], "EN": ["Bashbashi"]},
    "Bərdə": {"code": "555309", "AZ": ["Bərdə"], "RU": ["Барда"], "EN": ["Barda"]},
    "Bərguşad": {"code": "554804", "AZ": ["Bərguşad"], "RU": ["Баргюшад"], "EN": ["Bargushad"]},
    "Biləcəri": {"code": "546808", "AZ": ["Biləcəri"], "RU": ["Баладжары"], "EN": ["Bilajari"]},
    "Binə": {"code": "547707", "AZ": ["Binə"], "RU": ["Бина"], "EN": ["Bina"]},
    "Böyük Kəsik": {
        "code": "558631", 
        "AZ": ["Böyük Kəsik-eksp.", "Böyük Kəsik", "Boyuk Kesik", "BK"], 
        "RU": ["Беюк-Кясик-эксп.", "Беюк Кясик", "БК"], 
        "EN": ["Boyuk Kasik-exp.", "Boyuk Kasik", "BK"]
    },
    "Böyük Kəsik (eksport)": {
        "code": "558701", 
        "AZ": ["Böyük Kəsik-eksp."], 
        "RU": ["Беюк-Кясик-эксп."], 
        "EN": ["Boyuk Kasik-exp."]
    },
    "Çarxı": {"code": "545400", "AZ": ["Çarxı"], "RU": ["Чархи"], "EN": ["Charkhi"]},
    "Cəlilabad": {"code": "553303", "AZ": ["Cəlilabad"], "RU": ["Джалилабад"], "EN": ["Jalilabad"]},
    "Culfa": {"code": "550004", "AZ": ["Culfa"], "RU": ["Джульфа"], "EN": ["Julfa"]},
    "Culfa (eksport)": {"code": "550108", "AZ": ["Culfa-eksp."], "RU": ["Джульфа-эксп."], "EN": ["Julfa-exp."]},

    # --- Буквы D, Ə, E, G, H, İ ---
    "Daşburun": {"code": "551906", "AZ": ["Daşburun"], "RU": ["Дашбурун"], "EN": ["Dashburun"]},
    "Dəllər": {"code": "556803", "AZ": ["Dəllər"], "RU": ["Далляр"], "EN": ["Dallar"]},
    "Dəlməmmədli": {"code": "556000", "AZ": ["Dəlməmmədli"], "RU": ["Дельмамедли"], "EN": ["Dalmamadli"]},
    "Dübəndi": {"code": "547904", "AZ": ["Dübəndi"], "RU": ["Дюбенди"], "EN": ["Dubendi"]},
    "Ələt": {"code": "548502", "AZ": ["Ələt"], "RU": ["Алят"], "EN": ["Alat"]},
    "Ələt eksport-Aktau": {"code": "549204", "AZ": ["Ələt-eksp.Aktau"], "RU": ["Алят-эксп.Актау"], "EN": ["Alat-exp.Aktau"]},
    "Ələt eksport-Kurik": {"code": "553002", "AZ": ["Ələt-eksp.Kurik"], "RU": ["Алят-эксп.Курык"], "EN": ["Alat-exp.Kuryk"]},
    "Ələt eksport-Türk.": {"code": "548803", "AZ": ["Ələt-eksp.Türk."], "RU": ["Алят-эксп.Турк."], "EN": ["Alat-exp.Turk."]},
    "Bakı ticarət liman": {"code": "547302", "AZ": ["Bakı ticarət limanı"], "RU": ["Бакинский торг. порт"], "EN": ["Baku Trade Port"]},
    "Bakı ticarət limanı (eks)": {"code": "547406", "AZ": ["Bakı ticarət limanı (eks)"], "RU": ["Бакинский торг. порт (эксп)"], "EN": ["Baku Trade Port (exp)"]},
    "Bakı ticarət limanı (aşır)": {"code": "547209", "AZ": ["Bakı ticarət limanı (aşır)"], "RU": ["Бакинский торг. порт (перевалка)"], "EN": ["Baku Trade Port (transshipment)"]},
    "Ələt yeni": {"code": "548703", "AZ": ["Ələt yeni"], "RU": ["Алят-Новый"], "EN": ["Alat-New"]},
    "Əsgəran": {"code": "557304", "AZ": ["Əsgəran"], "RU": ["Аскеран"], "EN": ["Asgaran"]},
    "Gəncə": {"code": "556208", "AZ": ["Gəncə"], "RU": ["Гянджа"], "EN": ["Ganja"]},
    "Giləzi": {"code": "546009", "AZ": ["Giləzi"], "RU": ["Гилязи"], "EN": ["Gilyazi"]},
    "Goran": {"code": "555900", "AZ": ["Goran"], "RU": ["Герань"], "EN": ["Goran"]},
    "Göylərçöl": {"code": "554402", "AZ": ["Göylərçöl"], "RU": ["Гейлярчель"], "EN": ["Goylarchol"]},
    "Gövşaban": {"code": "553801", "AZ": ["Gövşaban"], "RU": ["Гевшабан"], "EN": ["Govshaban"]},
    "Güzdək": {"code": "546600", "AZ": ["Güzdək"], "RU": ["Гюздек"], "EN": ["Guzdek"]},
    "Hacıqabul": {"code": "554202", "AZ": ["Hacıqabul"], "RU": ["Кази-Магомед"], "EN": ["Hajigabul"]},
    "Həkəri": {"code": "551505", "AZ": ["Həkəri"], "RU": ["Акари"], "EN": ["Hakari"]},
    "Horadiz": {"code": "551806", "AZ": ["Horadiz"], "RU": ["Горадиз"], "EN": ["Horadiz"]},
    "Hövsan": {"code": "547800", "AZ": ["Hövsan"], "RU": ["Говсаны"], "EN": ["Hovsan"]},
    "İmişli": {"code": "552207", "AZ": ["İmişli"], "RU": ["Имишли"], "EN": ["Imishli"]},

    # --- Буквы K, L, M ---
    "Karçevan": {"code": "551007", "AZ": ["Karçevan"], "RU": ["Карчевань"], "EN": ["Karchevan"]},
    "Keşlə": {
        "code": "547001", 
        "AZ": ["Keşlə", "Keshle"], 
        "RU": ["Кишлы", "Кешля"], 
        "EN": ["Kishli", "Keshla"]
    },
    "Köçərli": {"code": "555205", "AZ": ["Köçərli"], "RU": ["Кочарли"], "EN": ["Kocharli"]},
    "Kürdəmir": {"code": "554607", "AZ": ["Kürdəmir"], "RU": ["Кюрдамир"], "EN": ["Kurdamir"]},
    "Kürəkçay": {"code": "557605", "AZ": ["Kürəkçay"], "RU": ["Кюрекчай"], "EN": ["Kurakchay"]},
    "Ləcət": {"code": "549505", "AZ": ["Ləcət"], "RU": ["Ладжат"], "EN": ["Lajat"]},
    "Ləki": {"code": "555008", "AZ": ["Ləki"], "RU": ["Ляки"], "EN": ["Laki"]},
    "Lənkəran": {"code": "553905", "AZ": ["Lənkəran"], "RU": ["Ленкорань"], "EN": ["Lankaran"]},
    "Liman": {"code": "553604", "AZ": ["Liman"], "RU": ["Лиман"], "EN": ["Liman"]},
    "Mahmudlu": {"code": "551702", "AZ": ["Mahmudlu"], "RU": ["Махмудлы"], "EN": ["Mahmudlu"]},
    "Masallı": {"code": "553407", "AZ": ["Masallı"], "RU": ["Масаллы"], "EN": ["Masalli"]},
    "Maştağa": {"code": "549609", "AZ": ["Maştağa"], "RU": ["Маштаги"], "EN": ["Mashtaga"]},
    "Mehri": {"code": "551100", "AZ": ["Mehri"], "RU": ["Мегри"], "EN": ["Mehri"]},
    "Mincivan": {"code": "551204", "AZ": ["Mincivan"], "RU": ["Миндживань"], "EN": ["Minjivan"]},
    "Mingəçevir": {"code": "555703", "AZ": ["Mingəçevir"], "RU": ["Мингечевир"], "EN": ["Mingachevir"]},
    "Mingəçevir şəhər": {"code": "555807", "AZ": ["Mingəçevir şəhər"], "RU": ["Мингечевир-Город"], "EN": ["Mingachevir City"]},
    "Muğan": {"code": "554306", "AZ": ["Muğan"], "RU": ["Мугань"], "EN": ["Mugan"]},
    "Mürsəlli": {"code": "552601", "AZ": ["Mürsəlli"], "RU": ["Мурселли"], "EN": ["Mursalli"]},
    "Müsüslü": {"code": "554700", "AZ": ["Müsüslü"], "RU": ["Мюсюсли"], "EN": ["Mususli"]},
    # --- Буквы N, O, P, Q ---
    "Naxçıvan": {"code": "550803", "AZ": ["Naxçıvan"], "RU": ["Нахичевань"], "EN": ["Nakhchivan"]},
    "Neftçala": {"code": "553207", "AZ": ["Neftçala"], "RU": ["Нефтечала"], "EN": ["Neftchala"]},
    "Nəvahi": {"code": "549007", "AZ": ["Nəvahi"], "RU": ["Наваги"], "EN": ["Navahi"]},
    "Ordubad": {"code": "550907", "AZ": ["Ordubad"], "RU": ["Ордубад"], "EN": ["Ordubad"]},
    "Pirsaat": {"code": "549100", "AZ": ["Pirsaat"], "RU": ["Пирсаат"], "EN": ["Pirsaat"]},
    "Pirşağı": {"code": "546507", "AZ": ["Pirşağı"], "RU": ["Пиршаги"], "EN": ["Pirshagi"]},
    "Poylu": {"code": "558400", "AZ": ["Poylu"], "RU": ["Пойлы"], "EN": ["Poylu"]},
    "Puta": {"code": "548108", "AZ": ["Puta"], "RU": ["Пута"], "EN": ["Puta"]},
    "Qafan": {"code": "551401", "AZ": ["Qafan"], "RU": ["Кафан"], "EN": ["Gafan"]},
    "Qamışlıq": {"code": "554005", "AZ": ["Qamışlıq"], "RU": ["Камышлыг"], "EN": ["Gamishlig"]},
    "Qaradağ": {"code": "548201", "AZ": ["Qaradağ"], "RU": ["Карадаг"], "EN": ["Garadagh"]},
    "Qaradağ terminal": {"code": "549702", "AZ": ["Qaradağ terminalı"], "RU": ["Карадаг (терминал)"], "EN": ["Garadagh Terminal"]},
    "Qasımlı": {"code": "553500", "AZ": ["Qasımlı"], "RU": ["Касымлы"], "EN": ["Gasimli"]},
    "Qax": {"code": "559507", "AZ": ["Qax"], "RU": ["Кахи"], "EN": ["Gakh"]},
    "Qazax": {"code": "557408", "AZ": ["Qazax"], "RU": ["Казах"], "EN": ["Gazakh"]},
    "Qırıxlı": {"code": "556509", "AZ": ["Qırıxlı"], "RU": ["Кырыхлы"], "EN": ["Girikhli"]},
    "Qızılburun": {"code": "545805", "AZ": ["Qızılburun"], "RU": ["Кызыл-Бурун"], "EN": ["Gizilburun"]},
    "Qızılca": {"code": "556405", "AZ": ["Qızılca"], "RU": ["Кызылджа"], "EN": ["Gizilja"]},
    "Qobustan": {"code": "548409", "AZ": ["Qobustan"], "RU": ["Гобустан"], "EN": ["Gobustan"]},
    "Qovlar": {"code": "557003", "AZ": ["Qovlar"], "RU": ["Говлар"], "EN": ["Govlar"]},
    "Quşçu körpü": {"code": "556301", "AZ": ["Quşçu körpü"], "RU": ["Кушчу-Керпю"], "EN": ["Gushchu Korpu"]},

    # --- Буквы S, Ş, T, U, V, X, Y, Z ---
    "Saatlı": {"code": "552300", "AZ": ["Saatlı"], "RU": ["Саатлы"], "EN": ["Saatly"]},
    "Sabir": {"code": "552508", "AZ": ["Sabir"], "RU": ["Сабир"], "EN": ["Sabir"]},
    "Şabran": {"code": "545608", "AZ": ["Şabran"], "RU": ["Шабран (Дивичи)", "Шабран"], "EN": ["Shabran"]},
    "Salahlı": {"code": "558504", "AZ": ["Salahlı"], "RU": ["Салахлы"], "EN": ["Salahli"]},
    "Salyan": {"code": "553106", "AZ": ["Salyan"], "RU": ["Сальяны"], "EN": ["Salyan"]},
    "Saracalar": {"code": "552404", "AZ": ["Saracalar"], "RU": ["Сараджалар"], "EN": ["Sarajalar"]},
    "Şahtaxtı": {"code": "550606", "AZ": ["Şahtaxtı"], "RU": ["Шахтахты"], "EN": ["Shahtakhti"]},
    "Şəki": {"code": "559403", "AZ": ["Şəki"], "RU": ["Шеки"], "EN": ["Sheki"]},
    "Şəmkir": {"code": "556706", "AZ": ["Şəmkir"], "RU": ["Шамхор", "Шамкир"], "EN": ["Shamkir"]},
    "Sanqaçal": {"code": "548305", "AZ": ["Sanqaçal"], "RU": ["Сангачалы"], "EN": ["Sangachal"]},
    "Sanqaçal ter.(aşırma)": {"code": "548606", "AZ": ["Sanqaçal ter.(aşırma)"], "RU": ["Сангачалы (перевалка)"], "EN": ["Sangachal Transshipment"]},
    "Şərur": {"code": "550502", "AZ": ["Şərur"], "RU": ["Шарур (Ильичевск)", "Шарур"], "EN": ["Sharur"]},
    "Şərur (eksport)": {"code": "550409", "AZ": ["Şərur-eksp."], "RU": ["Шарур-эксп."], "EN": ["Sharur-exp."]},
    "Şirvan": {"code": "552705", "AZ": ["Şirvan"], "RU": ["Ширван"], "EN": ["Shirvan"]},
    "Sitalçay": {"code": "546102", "AZ": ["Sitalçay"], "RU": ["Ситалчай"], "EN": ["Sitalchay"]},
    "Siyəzən": {"code": "545909", "AZ": ["Siyəzən"], "RU": ["Сиязань"], "EN": ["Siyazan"]},
    "Soltanlı": {"code": "552902", "AZ": ["Soltanlı"], "RU": ["Султанлы"], "EN": ["Soltanli"]},
    "Soyuq-Bulaq": {"code": "558608", "AZ": ["Soyuq-Bulaq"], "RU": ["Союк-Булак"], "EN": ["Soyug-Bulag"]},
    "Sumqayıt": {"code": "546403", "AZ": ["Sumqayıt"], "RU": ["Сумгаит", "Сумгайыт"], "EN": ["Sumgayit"]},
    "Suraxanı": {"code": "549401", "AZ": ["Suraxanı"], "RU": ["Сураханы"], "EN": ["Surakhani"]},
    "Təzəkənd": {"code": "555402", "AZ": ["Təzəkənd"], "RU": ["Тазакенд"], "EN": ["Tazakand"]},
    "Tovuz": {"code": "557107", "AZ": ["Tovuz"], "RU": ["Товуз"], "EN": ["Tovuz"]},
    "Ucar": {"code": "554908", "AZ": ["Ucar"], "RU": ["Уджары", "Уджар"], "EN": ["Ujar"]},
    "Vətəqə": {"code": "552103", "AZ": ["Vətəqə"], "RU": ["Ватага"], "EN": ["Vataga"]},
    "Xaçmaz": {"code": "545307", "AZ": ["Xaçmaz"], "RU": ["Хачмаз"], "EN": ["Khachmaz"]},
    "Xanabad": {"code": "559300", "AZ": ["Xanabad"], "RU": ["Ханабад"], "EN": ["Khanabad"]},
    "Xankəndi": {"code": "555608", "AZ": ["Xankəndi"], "RU": ["Ханкенди (Степанакерт)", "Ханкенди"], "EN": ["Khankendi"]},
    "Xələc": {"code": "552001", "AZ": ["Xələc"], "RU": ["Халадж"], "EN": ["Khalaj"]},
    "Xələfli": {"code": "551609", "AZ": ["Xələfli"], "RU": ["Халафли"], "EN": ["Khalafli"]},
    "Xırdalan": {"code": "546704", "AZ": ["Xırdalan"], "RU": ["Хырдалан"], "EN": ["Khirdalan"]},
    "Xudat": {"code": "545107", "AZ": ["Xudat"], "RU": ["Худат"], "EN": ["Khudat"]},
    "Yalama": {
        "code": "545006", 
        "AZ": ["Yalama-eksp.", "Yalama"], 
        "RU": ["Ялама-эксп.", "Ялама"], 
        "EN": ["Yalama-exp.", "Yalama"]
    },
    "Yalama (eksport)": {
        "code": "547508", 
        "AZ": ["Yalama-eksp.", "Yalama eksport"], 
        "RU": ["Ялама-эксп.", "Ялама экспорт"], 
        "EN": ["Yalama-exp."]
    },
    "Yevlax": {"code": "555101", "AZ": ["Yevlax"], "RU": ["Евлах"], "EN": ["Yevlakh"]},
    "Z.Tağıyev": {"code": "546302", "AZ": ["Z.Tağıyev"], "RU": ["З.Тагиев (Насосный)", "З.Тагиев"], "EN": ["Z.Taghiyev"]},
    "Z.Tağıyev çeşidləmə": {"code": "546901", "AZ": ["Z.Tağıyev çeşidləmə"], "RU": ["З.Тагиев (сортировочная)"], "EN": ["Z.Taghiyev Sorting"]},
    "Zabrat II": {"code": "557802", "AZ": ["Zabrat II"], "RU": ["Забрат II"], "EN": ["Zabrat II"]},
    "Zaqatala": {"code": "559600", "AZ": ["Zaqatala"], "RU": ["Закаталы"], "EN": ["Zagatala"]},
    "Zazalı": {"code": "556104", "AZ": ["Zazalı"], "RU": ["Зазалы"], "EN": ["Zazali"]},
    "Zəyəm": {"code": "556903", "AZ": ["Zəyəm"], "RU": ["Заям"], "EN": ["Zayam"]},
    "Zirə": {"code": "549308", "AZ": ["Zirə"], "RU": ["Зиря"], "EN": ["Zira"]},
    "Zorat": {"code": "549806", "AZ": ["Zorat"], "RU": ["Зорат"], "EN": ["Zorat"]},
}


# ------------------------------------------------------------------------------
# БЛОК 2: Поисковые функции для парсера и UI
# ------------------------------------------------------------------------------
def get_localized_station_name(station_input: str, lang: str = "AZ") -> str:
    if not station_input:
        return ""

    query = str(station_input).strip().lower()

    # 1. Поиск по коду ЕСР
    for main_key, data in STATIONS_MAPPING.items():
        if data.get("code") == query:
            names = data.get(lang, data.get("AZ", [main_key]))
            return names[0] if isinstance(names, list) else names

    # 2. Поиск по алиасам на всех языках
    for main_key, data in STATIONS_MAPPING.items():
        for lang_code in ["AZ", "RU", "EN"]:
            names = data.get(lang_code, [])
            if isinstance(names, str):
                names = [names]
            for name in names:
                if name.lower() == query or name.lower().replace("-", " ").replace(".", "") == query.replace("-", " ").replace(".", ""):
                    target_names = data.get(lang, data.get("AZ", [main_key]))
                    return target_names[0] if isinstance(target_names, list) else target_names

    return station_input.strip()


def get_station_code(station_input: str) -> str:
    if not station_input:
        return ""
    query = str(station_input).strip().lower()
    for main_key, data in STATIONS_MAPPING.items():
        if data.get("code") == query:
            return data.get("code", "")
        for lang_code in ["AZ", "RU", "EN"]:
            names = data.get(lang_code, [])
            if isinstance(names, str):
                names = [names]
            for name in names:
                if name.lower() == query or name.lower().replace("-", " ").replace(".", "") == query.replace("-", " ").replace(".", ""):
                    return data.get("code", "")
    return ""


def format_station_display(station_name: str, station_code: str = "", lang: str = "AZ") -> str:
    if not station_name:
        return ""

    localized_name = get_localized_station_name(station_name, lang=lang)
    code = station_code or get_station_code(station_name)

    if localized_name in ["Ələt-eksp.", "Алят-эксп.", "Alat-exp."]:
        return localized_name

    if code:
        return f"{localized_name} ({code})"

    return localized_name


def get_canonical_station_name(station_input: str) -> str:
    """Возвращает главный ключ станции на AZ (например, 'Bakı yük') для любого ввода на AZ/RU/EN или кода ЕСР."""
    if not station_input:
        return ""
    
    query = str(station_input).strip().lower()
    
    # 1. Поиск по коду ЕСР
    for main_key, data in STATIONS_MAPPING.items():
        if data.get("code") == query:
            return main_key

    # 2. Поиск по синонимам на любых языках (AZ, RU, EN)
    for main_key, data in STATIONS_MAPPING.items():
        for lang_code in ["AZ", "RU", "EN"]:
            names = data.get(lang_code, [])
            if isinstance(names, str):
                names = [names]
            for name in names:
                if name.lower() == query or name.lower().replace("-", " ").replace(".", "") == query.replace("-", " ").replace(".", ""):
                    return main_key

    return station_input.strip()


# ------------------------------------------------------------------------------
# Дополнение: Получение пограничного статуса станции
# ------------------------------------------------------------------------------
def get_station_border_status(station_input: str) -> bool:
    """Возвращает True, если станция является пограничным переходом или терминалом."""
    if not station_input:
        return False
    
    canonical_name = get_canonical_station_name(station_input)
    
    # Канонические имена пограничных узлов ADY
    border_canonical_names = {
        "Yalama", "Yalama (eksport)",
        "Böyük Kəsik", "Böyük Kəsik (eksport)",
        "Astara", "Astara (eks.aşır)",
        "Culfa", "Culfa (eksport)",
        "Şərur", "Şərur (eksport)",
        "Ələt eksport-Aktau", "Ələt eksport-Kurik", "Ələt eksport-Türk.",
        "Bakı ticarət liman", "Bakı ticarət limanı (eks)", "Bakı ticarət limanı (aşır)"
    }
    
    return canonical_name in border_canonical_names

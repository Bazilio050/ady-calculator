# ==============================================================================
# СПРАВОЧНИК И ДВИЖОК ПОИСКА СТАНЦИЙ ADY (AZ / RU / EN / ЕСР)
# ==============================================================================

STATIONS_MAPPING = {
    # --- Буквы A, B, C ---
    "Abşeron": {"code": "548003", "AZ": ["Abşeron"], "RU": ["Апшерон", "Абшерон"], "EN": ["Absheron"]},
    "Ağdam": {"code": "546206", "AZ": ["Ağdam"], "RU": ["Агдам"], "EN": ["Aghdam"]},
    "Ağstafa": {"code": "548605", "AZ": ["Ağstafa"], "RU": ["Акстафа", "Агстафа"], "EN": ["Agstafa"]},
    "Alabaşlı": {"code": "548408", "AZ": ["Alabaşlı"], "RU": ["Алабашлы"], "EN": ["Alabashli"]},
    "Astara": {"code": "549504", "AZ": ["Astara"], "RU": ["Астара"], "EN": ["Astara"]},
    "Astara (eks.aşır)": {"code": "549504", "AZ": ["Astara (eks.aşır)"], "RU": ["Астара (эксп.перевалка)"], "EN": ["Astara (exp.transshipment)"]},
    "Atbulaq": {"code": "547908", "AZ": ["Atbulaq"], "RU": ["Атбулак"], "EN": ["Atbulag"]},
    "Bakı yük": {
        "code": "547105", 
        "AZ": ["Bakı yük", "Bakı yuk", "Baku yuk", "Bakı-Yük"], 
        "RU": ["Баку-Товарная", "Баку тов", "Баку-тов", "Баку грузовой", "Баку товарный"], 
        "EN": ["Baku Freight", "Baku freight", "Baku tov"]
    },
    "Bakı yük terminal": {
        "code": "547105", 
        "AZ": ["Bakı yük terminalı"], 
        "RU": ["Баку-Товарная (терминал)", "Баку тов terminal"], 
        "EN": ["Baku Freight Terminal"]
    },
    "Balakən": {"code": "546600", "AZ": ["Balakən"], "RU": ["Белоканы"], "EN": ["Balakan"]},
    "Bartaz": {"code": "553303", "AZ": ["Bartaz"], "RU": ["Бартаз"], "EN": ["Bartaz"]},
    "Barxudarlı": {"code": "548808", "AZ": ["Barxudarlı"], "RU": ["Бархударлы"], "EN": ["Barkhudarli"]},
    "Başbaşı": {"code": "553708", "AZ": ["Başbaşı"], "RU": ["Башбаши"], "EN": ["Bashbashi"]},
    "Bərdə": {"code": "546102", "AZ": ["Bərdə"], "RU": ["Барда"], "EN": ["Barda"]},
    "Bərguşad": {"code": "545400", "AZ": ["Bərguşad"], "RU": ["Баргюшад"], "EN": ["Bargushad"]},
    "Biləcəri": {"code": "547302", "AZ": ["Biləcəri"], "RU": ["Баладжары"], "EN": ["Bilajari"]},
    "Binə": {"code": "547209", "AZ": ["Binə"], "RU": ["Бина"], "EN": ["Bina"]},
    "Böyük Kəsik": {
        "code": "558701", 
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
    "Çarxı": {"code": "547406", "AZ": ["Çarxı"], "RU": ["Чархи"], "EN": ["Charkhi"]},
    "Cəlilabad": {"code": "549203", "AZ": ["Cəlilabad"], "RU": ["Джалилабад"], "EN": ["Jalilabad"]},
    "Culfa": {"code": "553500", "AZ": ["Culfa"], "RU": ["Джульфа"], "EN": ["Julfa"]},
    "Culfa (eksport)": {"code": "553500", "AZ": ["Culfa-eksp."], "RU": ["Джульфа-эксп."], "EN": ["Julfa-exp."]},

    # --- Буквы D, Ə, E, G, H, İ ---
    "Daşburun": {"code": "552601", "AZ": ["Daşburun"], "RU": ["Дашбурун"], "EN": ["Dashburun"]},
    "Dəllər": {"code": "548501", "AZ": ["Dəllər"], "RU": ["Далляр"], "EN": ["Dallar"]},
    "Dəlməmmədli": {"code": "548200", "AZ": ["Dəlməmmədli"], "RU": ["Дельмамедли"], "EN": ["Dalmamadli"]},
    "Dübəndi": {"code": "547213", "AZ": ["Dübəndi"], "RU": ["Дюбенди"], "EN": ["Dubendi"]},
    "Ələt": {"code": "548008", "AZ": ["Ələt"], "RU": ["Алят"], "EN": ["Alat"]},
    "Ələt eksport-Aktau": {"code": "548801", "AZ": ["Ələt-eksp.Aktau"], "RU": ["Алят-эксп.Актау"], "EN": ["Alat-exp.Aktau"]},
    "Ələt eksport-Kurik": {"code": "548802", "AZ": ["Ələt-eksp.Kurik"], "RU": ["Алят-эксп.Курык"], "EN": ["Alat-exp.Kuryk"]},
    "Ələt eksport-Türk.": {"code": "548803", "AZ": ["Ələt-eksp.Türk."], "RU": ["Алят-эксп.Турк."], "EN": ["Alat-exp.Turk."]},
    "Bakı ticarət liman": {"code": "548008", "AZ": ["Bakı ticarət limanı"], "RU": ["Бакинский торг. порт"], "EN": ["Baku Trade Port"]},
    "Bakı ticarət limanı (eks)": {"code": "548008", "AZ": ["Bakı ticarət limanı (eks)"], "RU": ["Бакинский торг. порт (эксп)"], "EN": ["Baku Trade Port (exp)"]},
    "Bakı ticarət limanı (aşır)": {"code": "548008", "AZ": ["Bakı ticarət limanı (aşır)"], "RU": ["Бакинский торг. порт (перевалка)"], "EN": ["Baku Trade Port (transshipment)"]},
    "Ələt yeni": {"code": "548012", "AZ": ["Ələt yeni"], "RU": ["Алят-Новый"], "EN": ["Alat-New"]},
    "Əsgəran": {"code": "546300", "AZ": ["Əsgəran"], "RU": ["Аскеран"], "EN": ["Asgaran"]},
    "Gəncə": {"code": "548304", "AZ": ["Gəncə"], "RU": ["Гянджа"], "EN": ["Ganja"]},
    "Giləzi": {"code": "547502", "AZ": ["Giləzi"], "RU": ["Гилязи"], "EN": ["Gilyazi"]},
    "Goran": {"code": "548101", "AZ": ["Goran"], "RU": ["Герань"], "EN": ["Goran"]},
    "Göylərçöl": {"code": "545203", "AZ": ["Göylərçöl"], "RU": ["Гейлярчель"], "EN": ["Goylarchol"]},
    "Gövşaban": {"code": "549400", "AZ": ["Gövşaban"], "RU": ["Гевшабан"], "EN": ["Govshaban"]},
    "Güzdək": {"code": "547705", "AZ": ["Güzdək"], "RU": ["Гюздек"], "EN": ["Guzdek"]},
    "Hacıqabul": {"code": "545006", "AZ": ["Hacıqabul"], "RU": ["Кази-Магомед"], "EN": ["Hajigabul"]},
    "Həkəri": {"code": "553002", "AZ": ["Həkəri"], "RU": ["Акари"], "EN": ["Hakari"]},
    "Horadiz": {"code": "552705", "AZ": ["Horadiz"], "RU": ["Горадиз"], "EN": ["Horadiz"]},
    "Hövsan": {"code": "547124", "AZ": ["Hövsan"], "RU": ["Говсаны"], "EN": ["Hovsan"]},
    "İmişli": {"code": "552207", "AZ": ["İmişli"], "RU": ["Имишли"], "EN": ["Imishli"]},

    # --- Буквы K, L, M, N, O, P, Q ---
    "Karçevan": {"code": "553401", "AZ": ["Karçevan"], "RU": ["Карчевань"], "EN": ["Karchevan"]},
    "Keşlə": {
        "code": "547001", 
        "AZ": ["Keşlə", "Keshle"], 
        "RU": ["Кишлы", "Кешля"], 
        "EN": ["Kishli", "Keshla"]
    },
    "Köçərli": {"code": "545805", "AZ": ["Köçərli"], "RU": ["Кочарли"], "EN": ["Kocharli"]},
    "Kürdəmir": {"code": "545307", "AZ": ["Kürdəmir"], "RU": ["Кюрдамир"], "EN": ["Kurdamir"]},
    "Kürəkçay": {"code": "548116", "AZ": ["Kürəkçay"], "RU": ["Кюрекчай"], "EN": ["Kurakchay"]},
    "Ləcət": {"code": "547410", "AZ": ["Ləcət"], "RU": ["Ладжат"], "EN": ["Lajat"]},
    "Ləki": {"code": "545608", "AZ": ["Ləki"], "RU": ["Ляки"], "EN": ["Laki"]},
    "Lənkəran": {"code": "549307", "AZ": ["Lənkəran"], "RU": ["Ленкорань"], "EN": ["Lankaran"]},
    "Liman": {"code": "549311", "AZ": ["Liman"], "RU": ["Лиман"], "EN": ["Liman"]},
    "Mahmudlu": {"code": "552508", "AZ": ["Mahmudlu"], "RU": ["Махмудлы"], "EN": ["Mahmudlu"]},
    "Masallı": {"code": "549100", "AZ": ["Masallı"], "RU": ["Масаллы"], "EN": ["Masalli"]},
    "Maştağa": {"code": "547204", "AZ": ["Maştağa"], "RU": ["Маштаги"], "EN": ["Mashtaga"]},
    "Mehri": {"code": "553200", "AZ": ["Mehri"], "RU": ["Мегри"], "EN": ["Mehri"]},
    "Mincivan": {"code": "552902", "AZ": ["Mincivan"], "RU": ["Миндживань"], "EN": ["Minjivan"]},
    "Mingəçevir": {"code": "545701", "AZ": ["Mingəçevir"], "RU": ["Мингечевир"], "EN": ["Mingachevir"]},
    "Mingəçevir şəhər": {"code": "545716", "AZ": ["Mingəçevir şəhər"], "RU": ["Мингечевир-Город"], "EN": ["Mingachevir City"]},
    "Muğan": {"code": "545010", "AZ": ["Muğan"], "RU": ["Мугань"], "EN": ["Mugan"]},
    "Mürsəlli": {"code": "545100", "AZ": ["Mürsəlli"], "RU": ["Мурселли"], "EN": ["Mursalli"]},
    "Müsüslü": {"code": "545504", "AZ": ["Müsüslü"], "RU": ["Мюсюсли"], "EN": ["Mususli"]},
    "Naxçıvan": {"code": "553604", "AZ": ["Naxçıvan"], "RU": ["Нахичевань"], "EN": ["Nakhchivan"]},
    "Neftçala": {"code": "549805", "AZ": ["Neftçala"], "RU": ["Нефтечала"], "EN": ["Neftchala"]},
    "Nəvahi": {"code": "547804", "AZ": ["Nəvahi"], "RU": ["Наваги"], "EN": ["Navahi"]},
    "Ordubad": {"code": "553905", "AZ": ["Ordubad"], "RU": ["Ордубад"], "EN": ["Ordubad"]},
    "Pirsaat": {"code": "547819", "AZ": ["Pirsaat"], "RU": ["Пирсаат"], "EN": ["Pirsaat"]},
    "Pirşağı": {"code": "547616", "AZ": ["Pirşağı"], "RU": ["Пиршаги"], "EN": ["Pirshagi"]},
    "Poylu": {"code": "548709", "AZ": ["Poylu"], "RU": ["Пойлы"], "EN": ["Poylu"]},
    "Puta": {"code": "547800", "AZ": ["Puta"], "RU": ["Пута"], "EN": ["Puta"]},
    "Qafan": {"code": "553106", "AZ": ["Qafan"], "RU": ["Кафан"], "EN": ["Gafan"]},
    "Qamışlıq": {"code": "545114", "AZ": ["Qamışlıq"], "RU": ["Камышлыг"], "EN": ["Gamishlig"]},
    "Qaradağ": {"code": "547900", "AZ": ["Qaradağ"], "RU": ["Карадаг"], "EN": ["Garadagh"]},
    "Qaradağ terminal": {"code": "547900", "AZ": ["Qaradağ terminalı"], "RU": ["Карадаг (терминал)"], "EN": ["Garadagh Terminal"]},
    "Qasımlı": {"code": "548319", "AZ": ["Qasımlı"], "RU": ["Касымлы"], "EN": ["Gasimli"]},
    "Qax": {"code": "546808", "AZ": ["Qax"], "RU": ["Кахи"], "EN": ["Gakh"]},
    "Qazax": {"code": "548901", "AZ": ["Qazax"], "RU": ["Казах"], "EN": ["Gazakh"]},
    "Qırıxlı": {"code": "546009", "AZ": ["Qırıxlı"], "RU": ["Кырыхлы"], "EN": ["Girikhli"]},
    "Qızılburun": {"code": "547425", "AZ": ["Qızılburun"], "RU": ["Кызыл-Бурун"], "EN": ["Gizilburun"]},
    "Qızılca": {"code": "548215", "AZ": ["Qızılca"], "RU": ["Кызылджа"], "EN": ["Gizilja"]},
    "Qobustan": {"code": "547912", "AZ": ["Qobustan"], "RU": ["Гобустан"], "EN": ["Gobustan"]},
    "Qovlar": {"code": "548612", "AZ": ["Qovlar"], "RU": ["Говлар"], "EN": ["Govlar"]},
    "Quşçu körpü": {"code": "548812", "AZ": ["Quşçu körpü"], "RU": ["Кушчу-Керпю"], "EN": ["Gushchu Korpu"]},

    # --- Буквы S, Ş, T, U, V, X, Y, Z ---
    "Saatlı": {"code": "552103", "AZ": ["Saatlı"], "RU": ["Саатлы"], "EN": ["Saatly"]},
    "Sabir": {"code": "552000", "AZ": ["Sabir"], "RU": ["Сабир"], "EN": ["Sabir"]},
    "Şabran": {"code": "547406", "AZ": ["Şabran"], "RU": ["Шабран (Дивичи)", "Шабран"], "EN": ["Shabran"]},
    "Salahlı": {"code": "548713", "AZ": ["Salahlı"], "RU": ["Салахлы"], "EN": ["Salahli"]},
    "Salyan": {"code": "549001", "AZ": ["Salyan"], "RU": ["Сальяны"], "EN": ["Salyan"]},
    "Saracalar": {"code": "552300", "AZ": ["Saracalar"], "RU": ["Сараджалар"], "EN": ["Sarajalar"]},
    "Şahtaxtı": {"code": "553712", "AZ": ["Şahtaxtı"], "RU": ["Шахтахты"], "EN": ["Shahtakhti"]},
    "Şəki": {"code": "546704", "AZ": ["Şəki"], "RU": ["Шеки"], "EN": ["Sheki"]},
    "Şəmkir": {"code": "548400", "AZ": ["Şəmkir"], "RU": ["Шамхор", "Шамкир"], "EN": ["Shamkir"]},
    "Sanqaçal": {"code": "547927", "AZ": ["Sanqaçal"], "RU": ["Сангачалы"], "EN": ["Sangachal"]},
    "Sanqaçal ter.(aşırma)": {"code": "547927", "AZ": ["Sanqaçal ter.(aşırma)"], "RU": ["Сангачалы (перевалка)"], "EN": ["Sangachal Transshipment"]},
    "Şərur": {"code": "553801", "AZ": ["Şərur"], "RU": ["Шарур (Ильичевск)", "Шарур"], "EN": ["Sharur"]},
    "Şərur (eksport)": {"code": "553801", "AZ": ["Şərur-eksp."], "RU": ["Шарур-эксп."], "EN": ["Sharur-exp."]},
    "Şirvan": {"code": "545129", "AZ": ["Şirvan"], "RU": ["Ширван"], "EN": ["Shirvan"]},
    "Sitalçay": {"code": "547512", "AZ": ["Sitalçay"], "RU": ["Ситалчай"], "EN": ["Sitalchay"]},
    "Siyəzən": {"code": "547432", "AZ": ["Siyəzən"], "RU": ["Сиязань"], "EN": ["Siyazan"]},
    "Soltanlı": {"code": "552808", "AZ": ["Soltanlı"], "RU": ["Султанлы"], "EN": ["Soltanli"]},
    "Soyuq-Bulaq": {"code": "548827", "AZ": ["Soyuq-Bulaq"], "RU": ["Союк-Булак"], "EN": ["Soyug-Bulag"]},
    "Sumqayıt": {"code": "547601", "AZ": ["Sumqayıt"], "RU": ["Сумгаит", "Сумгайыт"], "EN": ["Sumgayit"]},
    "Suraxanı": {"code": "547218", "AZ": ["Suraxanı"], "RU": ["Сураханы"], "EN": ["Surakhani"]},
    "Təzəkənd": {"code": "546117", "AZ": ["Təzəkənd"], "RU": ["Тазакенд"], "EN": ["Tazakand"]},
    "Tovuz": {"code": "548516", "AZ": ["Tovuz"], "RU": ["Товуз"], "EN": ["Tovuz"]},
    "Ucar": {"code": "545519", "AZ": ["Ucar"], "RU": ["Уджары", "Уджар"], "EN": ["Ujar"]},
    "Vətəqə": {"code": "549701", "AZ": ["Vətəqə"], "RU": ["Ватага"], "EN": ["Vataga"]},
    "Xaçmaz": {"code": "547441", "AZ": ["Xaçmaz"], "RU": ["Хачмаз"], "EN": ["Khachmaz"]},
    "Xanabad": {"code": "545720", "AZ": ["Xanabad"], "RU": ["Ханабад"], "EN": ["Khanabad"]},
    "Xankəndi": {"code": "546404", "AZ": ["Xankəndi"], "RU": ["Ханкенди (Степанакерт)", "Ханкенди"], "EN": ["Khankendi"]},
    "Xələc": {"code": "549608", "AZ": ["Xələc"], "RU": ["Халадж"], "EN": ["Khalaj"]},
    "Xələfli": {"code": "552812", "AZ": ["Xələfli"], "RU": ["Халафли"], "EN": ["Khalafli"]},
    "Xırdalan": {"code": "547711", "AZ": ["Xırdalan"], "RU": ["Хырдалан"], "EN": ["Khirdalan"]},
    "Xudat": {"code": "547527", "AZ": ["Xudat"], "RU": ["Худат"], "EN": ["Khudat"]},
    "Yalama": {
        "code": "547508", 
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
    "Yevlax": {"code": "545909", "AZ": ["Yevlax"], "RU": ["Евлах"], "EN": ["Yevlakh"]},
    "Z.Tağıyev": {"code": "547620", "AZ": ["Z.Tağıyev"], "RU": ["З.Тагиев (Насосный)", "З.Тагиев"], "EN": ["Z.Taghiyev"]},
    "Z.Tağıyev çeşidləmə": {"code": "547620", "AZ": ["Z.Tağıyev çeşidləmə"], "RU": ["З.Тагиев (сортировочная)"], "EN": ["Z.Taghiyev Sorting"]},
    "Zabrat II": {"code": "547222", "AZ": ["Zabrat II"], "RU": ["Забрат II"], "EN": ["Zabrat II"]},
    "Zaqatala": {"code": "546500", "AZ": ["Zaqatala"], "RU": ["Закаталы"], "EN": ["Zagatala"]},
    "Zazalı": {"code": "548220", "AZ": ["Zazalı"], "RU": ["Зазалы"], "EN": ["Zazali"]},
    "Zəyəm": {"code": "548412", "AZ": ["Zəyəm"], "RU": ["Заям"], "EN": ["Zayam"]},
    "Zirə": {"code": "547237", "AZ": ["Zirə"], "RU": ["Зиря"], "EN": ["Zira"]},
    "Zorat": {"code": "547456", "AZ": ["Zorat"], "RU": ["Зорат"], "EN": ["Zorat"]},
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

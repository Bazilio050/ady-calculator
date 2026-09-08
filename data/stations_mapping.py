# ------------------------------------------------------------------------------
# БЛОК 1: Справочник станций ADY (Канонические имена, ЕСР-коды и синонимы)
# ------------------------------------------------------------------------------

STATIONS_MAPPING = {
    # --- Буквы A, B, C ---
    "Abşeron": {"code": "548004", "AZ": ["Abşeron"], "RU": ["Апшерон", "Абшерон"], "EN": ["Absheron"]},
    "Ağdam": {"code": "555506", "AZ": ["Ağdam"], "RU": ["Агдам"], "EN": ["Aghdam"]},
    "Ağstafa": {"code": "557200", "AZ": ["Ağstafa"], "RU": ["Акстафа", "Агстафа"], "EN": ["Agstafa"]},
    "Alabaşlı": {"code": "556602", "AZ": ["Alabaşlı"], "RU": ["Алабашлы"], "EN": ["Alabashli"]},
    "Astara": {
        "code": "554109",
        "export_code": "554503",
        "is_border": True,
        "AZ": ["Astara"],
        "RU": ["Астара"],
        "EN": ["Astara"]
    },
    "Astara (eks.aşır)": {
        "code": "554503",
        "export_code": "554503",
        "is_border": True,
        "AZ": ["Astara (eks.aşır)", "Astara eksport"],
        "RU": ["Астара (эксп.перевалка)", "Астара экспорт", "Астара-эксп."],
        "EN": ["Astara (exp.transshipment)", "Astara export"]
    },
    "Atbulaq": {"code": "548907", "AZ": ["Atbulaq"], "RU": ["Атбулак"], "EN": ["Atbulag"]},
    "Bakı yük": {
        "code": "547105",
        "export_code": "547105",
        "is_border": False,
        "AZ": ["Bakı yük", "Bakı yuk"],
        "RU": ["Баку грузовой", "Баку тов", "Баку-товарная", "Баку-тов.", "Баку юк"],
        "EN": ["Baku cargo", "Baku freight"]
    },
    "Bakı yük terminal": {
        "code": "547603",
        "export_code": "547603",
        "is_border": False,
        "AZ": ["Bakı yük terminal", "Bakı yuk terminal", "Bakı yuk ter"],
        "RU": ["Баку грузовой терминал", "Баку терминал", "Баку-терминал", "Баку-тер.", "Баку груз терминал"],
        "EN": ["Baku cargo terminal", "Baku freight terminal"]
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
    "export_code": "558701",
    "is_border": True,
    "AZ": ["Böyük Kəsik", "BK", "Boyuk Kesik"],
    "RU": ["Беюк Кясик", "БК", "Беюк-Кясик"],
    "EN": ["Boyuk Kesik", "BK"]
},
"Böyük Kəsik (eksport)": {
    "code": "558701",
    "export_code": "558701",
    "is_border": True,
    "AZ": ["Böyük Kəsik eksport", "BK", "Boyuk Kesik eksp"],
    "RU": ["Беюк Кясик экспорт", "БК", "Беюк Кясик-эксп."],
    "EN": ["Boyuk Kesik exp", "BK"]
},
    "Çarxı": {"code": "545400", "AZ": ["Çarxı"], "RU": ["Чархи"], "EN": ["Charkhi"]},
    "Cəlilabad": {"code": "553303", "AZ": ["Cəlilabad"], "RU": ["Джалилабад"], "EN": ["Jalilabad"]},
    "Culfa": {
    "code": "550004",
    "export_code": "550108",
    "is_border": True,
    "AZ": ["Culfa"],
    "RU": ["Джульфа"],
    "EN": ["Julfa"]
},
"Culfa (eksport)": {
    "code": "550108",
    "export_code": "550108",
    "is_border": True,
    "AZ": ["Culfa eksport"],
    "RU": ["Джульфа экспорт"],
    "EN": ["Julfa exp"]
},

    # --- Буквы D, Ə, E, G, H, İ ---
    "Daşburun": {"code": "551906", "AZ": ["Daşburun"], "RU": ["Дашбурун"], "EN": ["Dashburun"]},
    "Dəllər": {"code": "556803", "AZ": ["Dəllər"], "RU": ["Далляр"], "EN": ["Dallar"]},
    "Dəlməmmədli": {"code": "556000", "AZ": ["Dəlməmmədli"], "RU": ["Дельмамедли"], "EN": ["Dalmamadli"]},
    "Dübəndi": {"code": "547904", "AZ": ["Dübəndi"], "RU": ["Дюбенди"], "EN": ["Dubendi"]},
    "Ələt": {
    "code": "548502",
    "export_code": "553002",
    "is_border": False,
    "AZ": ["Ələt", "Alat"],
    "RU": ["Алят"],
    "EN": ["Alat"]
},

"Ələt eksport-Kurik": {
    "code": "553002",
    "export_code": "553002",
    "is_border": True,
    "AZ": ["Ələt eksport-Kurik", "Ələt-Kurik", "Qurıq", "Kurik", "Ələt eksp", "Ələt-eksp."],
    "RU": ["Алят экспорт-Курык", "Алят-Курык", "Курык", "Курик", "Алят экс", "Алят експ", "Алят-эксп.", "Алят экспорт"],
    "EN": ["Alat export-Kuryk", "Kuryk", "Alat-exp."]
},

"Ələt eksport-Türk.": {
    "code": "548803",
    "export_code": "548803",
    "is_border": True,
    "AZ": ["Ələt eksport-Türk.", "Ələt-Türk", "Türkmenbaşı", "TRK"],
    "RU": ["Алят экспорт-Турк.", "Алят-Турк", "Туркменбаши", "ТРК", "Турк", "Трп", "Трк"],
    "EN": ["Alat export-Turk.", "Turkmenbashi"]
},

"Ələt eksport-Aktau": {
    "code": "549204",
    "export_code": "549204",
    "is_border": True,
    "AZ": ["Ələt eksport-Aktau", "Ələt-Aktau", "Aqtau", "Aktau"],
    "RU": ["Алят экспорт-Актау", "Алят-Актау", "Актау"],
    "EN": ["Alat export-Aktau", "Aktau"]
},
    "Bakı ticarət liman": {"code": "547302", "AZ": ["Bakı ticarət limanı"], "RU": ["Бакинский торг. порт"], "EN": ["Baku Trade Port"]},
    "Bakı ticarət limanı (eks)": {
        "code": "547406",
        "export_code": "547406",
        "is_border": False,
        "AZ": ["Bakı ticarət limanı (eks)", "Bakı liman eks", "Bakı ticarət limanı eks"],
        "RU": ["Баку торговый порт экс", "Баку торг пристань", "Баку торг эксп", "Баку торг экс", "Баку торговый пристань эксп", "Баку порт экс"],
        "EN": ["Baku trade port exp", "Baku commercial port exp"]
    },
    "Bakı ticarət limanı (aşır)": {
        "code": "547209",
        "export_code": "547209",
        "is_border": False,
        "AZ": ["Bakı ticarət limanı (aşır)", "Bakı liman aşırma", "Bakı liman asir"],
        "RU": ["Баку торговый порт перевалка", "Баку торг пристань перевалка", "Баку перевалка", "Баку порт перевалка", "Баку аширма"],
        "EN": ["Baku trade port transshipment", "Baku port transshipment"]
    },
    "Ələt yeni": {"code": "548703", "AZ": ["Ələt yeni"], "RU": ["Алят-Новый"], "EN": ["Alat-New"]},
    "Əsgəran": {"code": "557304", "AZ": ["Əsgəran"], "RU": ["Аскеран"], "EN": ["Asgaran"]},
    "Gəncə": {"code": "556208", "AZ": ["Gəncə"], "RU": ["Гянджа"], "EN": ["Ganja"]},
    "Giləzi": {"code": "546009", "AZ": ["Giləzi"], "RU": ["Гилязи"], "EN": ["Gilyazi"]},
    "Goran": {"code": "555900", "AZ": ["Goran"], "RU": ["Герань"], "EN": ["Goran"]},
    "Göylərçöl": {"code": "554402", "AZ": ["Göylərçöl"], "RU": ["Гейлярчель"], "EN": ["Goylarchol"]},
    "Gövşaban": {"code": "553801", "AZ": ["Gövşaban"], "RU": ["Гевшабан"], "EN": ["Govshaban"]},
    "Güzdək": {"code": "546600", "AZ": ["Güzdək"], "RU": ["Гюздек"], "EN": ["Guzdek"]},
    "Hacıqabul": {"code": "554202", "AZ": ["Hacıqabul"], "RU": ["Кази-Магомед", "Гаджигабул"], "EN": ["Hajigabul"]},
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
    "Mingəçevir şəhər": {
        "code": "555807",
        "export_code": "555807",
        "is_border": False,
        "AZ": ["Mingəçevir şəhər", "Mingəçevir şəh", "Mingecevir seher"],
        "RU": ["Мингечевир город", "Мингечевир гор", "Мингечаур город"],
        "EN": ["Mingachevir city", "Mingechevir city"]
    },
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
    "Qaradağ terminal": {
        "code": "549702",
        "export_code": "549702",
        "is_border": False,
        "AZ": ["Qaradağ terminal", "Qaradağ ter", "Garadag terminal"],
        "RU": ["Карадаг терминал", "Карадаг тер"],
        "EN": ["Garadagh terminal", "Garadag terminal"]
    },
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
    "Sanqaçal ter.(aşırma)": {
        "code": "548606",
        "export_code": "548606",
        "is_border": False,
        "AZ": ["Sanqaçal ter.(aşırma)", "Sanqaçal aşırma", "Sanqacal asirma", "Sanqaçal terminal"],
        "RU": ["Сангачал терминал перевалка", "Сангачал перевалка", "Сангачал аширма", "Сангачал тер"],
        "EN": ["Sangachal terminal transshipment", "Sangachal transshipment"]},
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
    "export_code": "547508",
    "is_border": True,
    "AZ": ["Yalama"],
    "RU": ["Ялама"],
    "EN": ["Yalama"]
},
"Yalama (eksport)": {
    "code": "547508",
    "export_code": "547508",
    "is_border": True,
    "AZ": ["Yalama eksport", "Yalama-eksp."],
    "RU": ["Ялама экспорт", "Ялама-эксп."],
    "EN": ["Yalama-exp."]
},
    "Yevlax": {"code": "555101", "AZ": ["Yevlax"], "RU": ["Евлах"], "EN": ["Yevlakh"]},
    "Z.Tağıyev": {
        "code": "546302",
        "export_code": "546302",
        "is_border": False,
        "AZ": ["Z.Tağıyev", "Zeynalabdin Tağıyev", "Tagiyev"],
        "RU": ["З.Тагиев", "Тагиев", "Гаджи зейналабдин Тагиев", "Г.З.Тагиев", "Посёлок Тагиева", "Насосный"],
        "EN": ["Z.Taghiyev", "Taghiyev"]
    },
    "Z.Tağıyev çeşidləmə": {
        "code": "546901",
        "export_code": "546901",
        "is_border": False,
        "AZ": ["Z.Tağıyev çeşidləmə", "Z.Tağıyev çeşid", "Tagiyev cesidleme"],
        "RU": ["З.Тагиев сортировочная", "З.Тагиев сорт", "Гаджи зейналабдин Тагиев сорт", "Гаджи зейналабдин Тагиев сортировочная", "Тагиев сорт", "Насосный сортировочная"],
        "EN": ["Z.Taghiyev sorting", "Taghiyev sorting"]
    },
    "Zabrat II": {
        "code": "557802",
        "export_code": "557802",
        "is_border": False,
        "AZ": ["Zabrat II", "Zabrat 2", "Zabrat-2"],
        "RU": ["Забрат II", "Забрат 2", "Забрат-2", "Забрат два"],
        "EN": ["Zabrat II", "Zabrat 2"]
    },
    "Zaqatala": {"code": "559600", "AZ": ["Zaqatala"], "RU": ["Закаталы"], "EN": ["Zagatala"]},
    "Zazalı": {"code": "556104", "AZ": ["Zazalı"], "RU": ["Зазалы"], "EN": ["Zazali"]},
    "Zəyəm": {"code": "556903", "AZ": ["Zəyəm"], "RU": ["Заям"], "EN": ["Zayam"]},
    "Zirə": {"code": "549308", "AZ": ["Zirə"], "RU": ["Зиря"], "EN": ["Zira"]},
    "Zorat": {"code": "549806", "AZ": ["Zorat"], "RU": ["Зорат"], "EN": ["Zorat"]},
}


# ------------------------------------------------------------------------------
# БЛОК 2: Вспомогательные поисковые функции для роутера и интерфейса
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
# БЛОК 3: Проверка пограничных статусов и получение экспортных ЕСР-кодов
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


def get_station_export_code(query_or_name: str) -> str:
    """Возвращает экспортный код станции для поиска расстояния в distances.csv"""
    canonical = get_canonical_station_name(query_or_name)
    if canonical and canonical in STATIONS_MAPPING:
        info = STATIONS_MAPPING[canonical]
        return info.get("export_code", info.get("code", ""))
    return ""

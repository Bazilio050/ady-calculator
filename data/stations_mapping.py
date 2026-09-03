# ==============================================================================
# СПРАВОЧНИК ЛОКАЛИЗАЦИИ И ФОРМАТИРОВАНИЯ СТАНЦИЙ ADY (AZ / RU / EN)
# ==============================================================================

# ------------------------------------------------------------------------------
# БЛОК 1: Полный официальный словарь станций ADY из тарифных таблиц
# ------------------------------------------------------------------------------
STATIONS_MAPPING = {
    # --- Буквы A, B, C ---
    "Abşeron": {"AZ": "Abşeron", "RU": "Апшерон", "EN": "Absheron"},
    "Ağdam": {"AZ": "Ağdam", "RU": "Агдам", "EN": "Aghdam"},
    "Ağstafa": {"AZ": "Ağstafa", "RU": "Акстафа", "EN": "Agstafa"},
    "Alabaşlı": {"AZ": "Alabaşlı", "RU": "Алабашлы", "EN": "Alabashli"},
    "Astara": {"AZ": "Astara", "RU": "Астара", "EN": "Astara"},
    "Astara (eks.aşır)": {"AZ": "Astara (eks.aşır)", "RU": "Астара (эксп.перевалка)", "EN": "Astara (exp.transshipment)"},
    "Atbulaq": {"AZ": "Atbulaq", "RU": "Атбулак", "EN": "Atbulag"},
    "Bakı yük": {"AZ": "Bakı yük", "RU": "Баку-Товарная", "EN": "Baku Freight"},
    "Bakı yük terminal": {"AZ": "Bakı yük terminalı", "RU": "Баку-Товарная (терминал)", "EN": "Baku Freight Terminal"},
    "Balakən": {"AZ": "Balakən", "RU": "Белоканы", "EN": "Balakan"},
    "Bartaz": {"AZ": "Bartaz", "RU": "Бартаз", "EN": "Bartaz"},
    "Barxudarlı": {"AZ": "Barxudarlı", "RU": "Бархударлы", "EN": "Barkhudarli"},
    "Başbaşı": {"AZ": "Başbaşı", "RU": "Башбаши", "EN": "Bashbashi"},
    "Bərdə": {"AZ": "Bərdə", "RU": "Барда", "EN": "Barda"},
    "Bərguşad": {"AZ": "Bərguşad", "RU": "Баргюшад", "EN": "Bargushad"},
    "Biləcəri": {"AZ": "Biləcəri", "RU": "Баладжары", "EN": "Bilajari"},
    "Binə": {"AZ": "Binə", "RU": "Бина", "EN": "Bina"},
    "Böyük Kəsik": {"AZ": "Böyük Kəsik-eksp.", "RU": "Беюк-Кясик-эксп.", "EN": "Boyuk Kasik-exp."},
    "Böyük Kəsik (eksport)": {"AZ": "Böyük Kəsik-eksp.", "RU": "Беюк-Кясик-эксп.", "EN": "Boyuk Kasik-exp."},
    "Çarxı": {"AZ": "Çarxı", "RU": "Чархи", "EN": "Charkhi"},
    "Cəlilabad": {"AZ": "Cəlilabad", "RU": "Джалилабад", "EN": "Jalilabad"},
    "Culfa": {"AZ": "Culfa", "RU": "Джульфа", "EN": "Julfa"},
    "Culfa (eksport)": {"AZ": "Culfa-eksp.", "RU": "Джульфа-эксп.", "EN": "Julfa-exp."},

    # --- Буквы D, Ə, E, G, H, İ ---
    "Daşburun": {"AZ": "Daşburun", "RU": "Дашбурун", "EN": "Dashburun"},
    "Dəllər": {"AZ": "Dəllər", "RU": "Далляр", "EN": "Dallar"},
    "Dəlməmmədli": {"AZ": "Dəlməmmədli", "RU": "Дельмамедли", "EN": "Dalmamadli"},
    "Dübəndi": {"AZ": "Dübəndi", "RU": "Дюбенди", "EN": "Dubendi"},
    "Ələt": {"AZ": "Ələt", "RU": "Алят", "EN": "Alat"},
    "Ələt eksport-Aktau": {"AZ": "Ələt-eksp.Aktau", "RU": "Алят-эксп.Актау", "EN": "Alat-exp.Aktau"},
    "Ələt eksport-Kurik": {"AZ": "Ələt-eksp.Kurik", "RU": "Алят-эксп.Курык", "EN": "Alat-exp.Kuryk"},
    "Ələt eksport-Türk.": {"AZ": "Ələt-eksp.Türk.", "RU": "Алят-эксп.Турк.", "EN": "Alat-exp.Turk."},
    "Bakı ticarət liman": {"AZ": "Bakı ticarət limanı", "RU": "Бакинский торг. порт", "EN": "Baku Trade Port"},
    "Bakı ticarət limanı (eks)": {"AZ": "Bakı ticarət limanı (eks)", "RU": "Бакинский торг. порт (эксп)", "EN": "Baku Trade Port (exp)"},
    "Bakı ticarət limanı (aşır)": {"AZ": "Bakı ticarət limanı (aşır)", "RU": "Бакинский торг. порт (перевалка)", "EN": "Baku Trade Port (transshipment)"},
    "Ələt yeni": {"AZ": "Ələt yeni", "RU": "Алят-Новый", "EN": "Alat-New"},
    "Əsgəran": {"AZ": "Əsgəran", "RU": "Аскеран", "EN": "Asgaran"},
    "Gəncə": {"AZ": "Gəncə", "RU": "Гянджа", "EN": "Ganja"},
    "Giləzi": {"AZ": "Giləzi", "RU": "Гилязи", "EN": "Gilyazi"},
    "Goran": {"AZ": "Goran", "RU": "Герань", "EN": "Goran"},
    "Göylərçöl": {"AZ": "Göylərçöl", "RU": "Гейлярчель", "EN": "Goylarchol"},
    "Gövşaban": {"AZ": "Gövşaban", "RU": "Гевшабан", "EN": "Govshaban"},
    "Güzdək": {"AZ": "Güzdək", "RU": "Гюздек", "EN": "Guzdek"},
    "Hacıqabul": {"AZ": "Hacıqabul", "RU": "Кази-Магомед", "EN": "Hajigabul"},
    "Həkəri": {"AZ": "Həkəri", "RU": "Акари", "EN": "Hakari"},
    "Horadiz": {"AZ": "Horadiz", "RU": "Горадиз", "EN": "Horadiz"},
    "Hövsan": {"AZ": "Hövsan", "RU": "Говсаны", "EN": "Hovsan"},
    "İmişli": {"AZ": "İmişli", "RU": "Имишли", "EN": "Imishli"},

    # --- Буквы K, L, M, N, O, P, Q ---
    "Karçevan": {"AZ": "Karçevan", "RU": "Карчевань", "EN": "Karchevan"},
    "Keşlə": {"AZ": "Keşlə", "RU": "Кишлы", "EN": "Kishli"},
    "Köçərli": {"AZ": "Köçərli", "RU": "Кочарли", "EN": "Kocharli"},
    "Kürdəmir": {"AZ": "Kürdəmir", "RU": "Кюрдамир", "EN": "Kurdamir"},
    "Kürəkçay": {"AZ": "Kürəkçay", "RU": "Кюрекчай", "EN": "Kurakchay"},
    "Ləcət": {"AZ": "Ləcət", "RU": "Ладжат", "EN": "Lajat"},
    "Ləki": {"AZ": "Ləki", "RU": "Ляки", "EN": "Laki"},
    "Lənkəran": {"AZ": "Lənkəran", "RU": "Ленкорань", "EN": "Lankaran"},
    "Liman": {"AZ": "Liman", "RU": "Лиман", "EN": "Liman"},
    "Mahmudlu": {"AZ": "Mahmudlu", "RU": "Махмудлы", "EN": "Mahmudlu"},
    "Masallı": {"AZ": "Masallı", "RU": "Масаллы", "EN": "Masalli"},
    "Maştağa": {"AZ": "Maştağa", "RU": "Маштаги", "EN": "Mashtaga"},
    "Mehri": {"AZ": "Mehri", "RU": "Мегри", "EN": "Mehri"},
    "Mincivan": {"AZ": "Mincivan", "RU": "Миндживань", "EN": "Minjivan"},
    "Mingəçevir": {"AZ": "Mingəçevir", "RU": "Мингечевир", "EN": "Mingachevir"},
    "Mingəçevir şəhər": {"AZ": "Mingəçevir şəhər", "RU": "Мингечевир-Город", "EN": "Mingachevir City"},
    "Muğan": {"AZ": "Muğan", "RU": "Мугань", "EN": "Mugan"},
    "Mürsəlli": {"AZ": "Mürsəlli", "RU": "Мурселли", "EN": "Mursalli"},
    "Müsüslü": {"AZ": "Müsüslü", "RU": "Мюсюсли", "EN": "Mususli"},
    "Naxçıvan": {"AZ": "Naxçıvan", "RU": "Нахичевань", "EN": "Nakhchivan"},
    "Neftçala": {"AZ": "Neftçala", "RU": "Нефтечала", "EN": "Neftchala"},
    "Nəvahi": {"AZ": "Nəvahi", "RU": "Наваги", "EN": "Navahi"},
    "Ordubad": {"AZ": "Ordubad", "RU": "Ордубад", "EN": "Ordubad"},
    "Pirsaat": {"AZ": "Pirsaat", "RU": "Пирсаат", "EN": "Pirsaat"},
    "Pirşağı": {"AZ": "Pirşağı", "RU": "Пиршаги", "EN": "Pirshagi"},
    "Poylu": {"AZ": "Poylu", "RU": "Пойлы", "EN": "Poylu"},
    "Puta": {"AZ": "Puta", "RU": "Пута", "EN": "Puta"},
    "Qafan": {"AZ": "Qafan", "RU": "Кафан", "EN": "Gafan"},
    "Qamışlıq": {"AZ": "Qamışlıq", "RU": "Камышлыг", "EN": "Gamishlig"},
    "Qaradağ": {"AZ": "Qaradağ", "RU": "Карадаг", "EN": "Garadagh"},
    "Qaradağ terminal": {"AZ": "Qaradağ terminalı", "RU": "Карадаг (терминал)", "EN": "Garadagh Terminal"},
    "Qasımlı": {"AZ": "Qasımlı", "RU": "Касымлы", "EN": "Gasimli"},
    "Qax": {"AZ": "Qax", "RU": "Кахи", "EN": "Gakh"},
    "Qazax": {"AZ": "Qazax", "RU": "Казах", "EN": "Gazakh"},
    "Qırıxlı": {"AZ": "Qırıxlı", "RU": "Кырыхлы", "EN": "Girikhli"},
    "Qızılburun": {"AZ": "Qızılburun", "RU": "Кызыл-Бурун", "EN": "Gizilburun"},
    "Qızılca": {"AZ": "Qızılca", "RU": "Кызылджа", "EN": "Gizilja"},
    "Qobustan": {"AZ": "Qobustan", "RU": "Гобустан", "EN": "Gobustan"},
    "Qovlar": {"AZ": "Qovlar", "RU": "Говлар", "EN": "Govlar"},
    "Quşçu körpü": {"AZ": "Quşçu körpü", "RU": "Кушчу-Керпю", "EN": "Gushchu Korpu"},

    # --- Буквы S, Ş, T, U, V, X, Y, Z ---
    "Saatlı": {"AZ": "Saatlı", "RU": "Саатлы", "EN": "Saatly"},
    "Sabir": {"AZ": "Sabir", "RU": "Сабир", "EN": "Sabir"},
    "Şabran": {"AZ": "Şabran", "RU": "Шабран (Дивичи)", "EN": "Shabran"},
    "Salahlı": {"AZ": "Salahlı", "RU": "Салахлы", "EN": "Salahli"},
    "Salyan": {"AZ": "Salyan", "RU": "Сальяны", "EN": "Salyan"},
    "Saracalar": {"AZ": "Saracalar", "RU": "Сараджалар", "EN": "Sarajalar"},
    "Şahtaxtı": {"AZ": "Şahtaxtı", "RU": "Шахтахты", "EN": "Shahtakhti"},
    "Şəki": {"AZ": "Şəki", "RU": "Шеки", "EN": "Sheki"},
    "Şəmkir": {"AZ": "Şəmkir", "RU": "Шамхор", "EN": "Shamkir"},
    "Sanqaçal": {"AZ": "Sanqaçal", "RU": "Сангачалы", "EN": "Sangachal"},
    "Sanqaçal ter.(aşırma)": {"AZ": "Sanqaçal ter.(aşırma)", "RU": "Сангачалы (перевалка)", "EN": "Sangachal Transshipment"},
    "Şərur": {"AZ": "Şərur", "RU": "Шарур (Ильичевск)", "EN": "Sharur"},
    "Şərur (eksport)": {"AZ": "Şərur-eksp.", "RU": "Шарур-эксп.", "EN": "Sharur-exp."},
    "Şirvan": {"AZ": "Şirvan", "RU": "Ширван", "EN": "Shirvan"},
    "Sitalçay": {"AZ": "Sitalçay", "RU": "Ситалчай", "EN": "Sitalchay"},
    "Siyəzən": {"AZ": "Siyəzən", "RU": "Сиязань", "EN": "Siyazan"},
    "Soltanlı": {"AZ": "Soltanlı", "RU": "Султанлы", "EN": "Soltanli"},
    "Soyuq-Bulaq": {"AZ": "Soyuq-Bulaq", "RU": "Союк-Булак", "EN": "Soyug-Bulag"},
    "Sumqayıt": {"AZ": "Sumqayıt", "RU": "Сумгаит", "EN": "Sumgayit"},
    "Suraxanı": {"AZ": "Suraxanı", "RU": "Сураханы", "EN": "Surakhani"},
    "Təzəkənd": {"AZ": "Təzəkənd", "RU": "Тазакенд", "EN": "Tazakand"},
    "Tovuz": {"AZ": "Tovuz", "RU": "Товуз", "EN": "Tovuz"},
    "Ucar": {"AZ": "Ucar", "RU": "Уджары", "EN": "Ujar"},
    "Vətəqə": {"AZ": "Vətəqə", "RU": "Ватага", "EN": "Vataga"},
    "Xaçmaz": {"AZ": "Xaçmaz", "RU": "Хачмаз", "EN": "Khachmaz"},
    "Xanabad": {"AZ": "Xanabad", "RU": "Ханабад", "EN": "Khanabad"},
    "Xankəndi": {"AZ": "Xankəndi", "RU": "Ханкенди (Степанакерт)", "EN": "Khankendi"},
    "Xələc": {"AZ": "Xələc", "RU": "Халадж", "EN": "Khalaj"},
    "Xələfli": {"AZ": "Xələfli", "RU": "Халафли", "EN": "Khalafli"},
    "Xırdalan": {"AZ": "Xırdalan", "RU": "Хырдалан", "EN": "Khirdalan"},
    "Xudat": {"AZ": "Xudat", "RU": "Худат", "EN": "Khudat"},
    "Yalama": {"AZ": "Yalama-eksp.", "RU": "Ялама-эксп.", "EN": "Yalama-exp."},
    "Yalama (eksport)": {"AZ": "Yalama-eksp.", "RU": "Ялама-эксп.", "EN": "Yalama-exp."},
    "Yevlax": {"AZ": "Yevlax", "RU": "Евлах", "EN": "Yevlakh"},
    "Z.Tağıyev": {"AZ": "Z.Tağıyev", "RU": "З.Тагиев (Насосный)", "EN": "Z.Taghiyev"},
    "Z.Tağıyev çeşidləmə": {"AZ": "Z.Tağıyev çeşidləmə", "RU": "З.Тагиев (сортировочная)", "EN": "Z.Taghiyev Sorting"},
    "Zabrat II": {"AZ": "Zabrat II", "RU": "Забрат II", "EN": "Zabrat II"},
    "Zaqatala": {"AZ": "Zaqatala", "RU": "Закаталы", "EN": "Zagatala"},
    "Zazalı": {"AZ": "Zazalı", "RU": "Зазалы", "EN": "Zazali"},
    "Zəyəm": {"AZ": "Zəyəm", "RU": "Заям", "EN": "Zayam"},
    "Zirə": {"AZ": "Zirə", "RU": "Зиря", "EN": "Zira"},
    "Zorat": {"AZ": "Zorat", "RU": "Зорат", "EN": "Zorat"},
}


# ------------------------------------------------------------------------------
# БЛОК 2: Функция перевода и мягкого поиска станций
# ------------------------------------------------------------------------------
def get_localized_station_name(station_name: str, lang: str = "AZ") -> str:
    """Возвращает переведенное название станции согласно справочнику STATIONS_MAPPING."""
    if not station_name:
        return ""

    clean_name = station_name.strip()

    # Прямое совпадение
    if clean_name in STATIONS_MAPPING:
        return STATIONS_MAPPING[clean_name].get(lang, clean_name)

    # Мягкое совпадение (без учета регистра, дефисов и точек)
    clean_cmp = clean_name.lower().replace("-", " ").replace(".", "")
    for map_key, translations in STATIONS_MAPPING.items():
        if clean_cmp == map_key.lower().replace("-", " ").replace(".", ""):
            return translations.get(lang, clean_name)

    return clean_name


# ------------------------------------------------------------------------------
# БЛОК 3: Функция форматирования вывода станций с ЕСР-кодами
# ------------------------------------------------------------------------------
def format_station_display(station_name: str, station_code: str = "", lang: str = "AZ") -> str:
    """
    Форматирует имя станции вместе с ЕСР-кодом.
    Скрывает ЕСР-код для обобщенной пограничной группы 'Ələt-eksp.'.
    """
    if not station_name:
        return ""

    localized_name = get_localized_station_name(station_name, lang=lang)

    # Исключение: для обобщенного погранперехода Алят код ЕСР скрываем
    if localized_name in ["Ələt-eksp.", "Алят-эксп.", "Alat-exp."]:
        return localized_name

    # Для остальных станций добавляем код ЕСР в скобках
    if station_code and str(station_code).strip():
        return f"{localized_name} ({str(station_code).strip()})"

    return localized_name

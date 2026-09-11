# data/translations.py

# ------------------------------------------------------------------------------
# Словарь уведомлений для правил Тарифного руководства
# ------------------------------------------------------------------------------

RULE_MESSAGES = {
    "MIN_DISTANCE_EXPORT": {
        "az": "İxrac daşınması üçün minimal tarif məsafəsi tətbiq edildi: {applied} km (faktiki: {actual} km).",
        "ru": "Применено минимальное тарифное расстояние для экспорта: {applied} км (фактическое: {actual} км).",
        "en": "Minimum tariff distance applied for export: {applied} km (actual: {actual} km)."
    },
    "MIN_DISTANCE_IMPORT": {
        "az": "İdxal daşınması üçün minimal tarif məsafəsi tətbiq edildi: {applied} km (faktiki: {actual} km).",
        "ru": "Применено минимальное тарифное расстояние для импорта: {applied} км (фактическое: {actual} км).",
        "en": "Minimum tariff distance applied for import: {applied} km (actual: {actual} km)."
    },
    "TABLE_1_ROUNDING": {
        "az": "Cədvəl 1-ə əsasən hesablama çəkisi yuvarlaqlaşdırıldı: {applied} ton (faktiki: {actual} ton).",
        "ru": "Согласно Таблице 1 расчетный вес округлен: {applied} тонн (фактический: {actual} тонн).",
        "en": "According to Table 1, billable weight rounded to: {applied} tons (actual: {actual} tons)."
    },
    "MIN_LOAD_NORM": {
        "az": "Yük üçün minimal yükləmə norması tətbiq edildi: {applied} ton (faktiki: {actual} ton).",
        "ru": "Применена минимальная норма загрузки для груза: {applied} тонн (фактическая: {actual} тонн).",
        "en": "Minimum load norm applied for cargo: {applied} tons (actual: {actual} tons)."
    },
    "MAIN_COEFF_1_50_IMPORT_EXPORT": {
        "az": "İdxal/İxrac daşımaları üzrə baza tarifinə 1.50 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.50 на импортные/экспортные перевозки к базовому тарифу.",
        "en": "A coefficient of 1.50 was applied for import/export shipments to the base rate."
    },
    "MAIN_COEFF_1_04_IMPORT_WOOD_METAL": {
        "az": "Taxta-materialları və qara metalların idxalı üzrə 1.04 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.04 на импорт лесоматериалов и черных металлов.",
        "en": "A coefficient of 1.04 was applied for the import of timber and ferrous metals."
    },
    "MAIN_COEFF_1_20_TRANSIT_ALAT": {
        "az": "Ələt - Böyük Kəsik marşrutu üzrə tranzit daşımalara 1.20 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.20 на транзитные перевозки по маршруту Алят — Беюк-Кесик.",
        "en": "A coefficient of 1.20 was applied for transit shipments on the Alat — Boyuk Kesik route."
    },
    "MAIN_COEFF_1_20_OIL_TANK": {
        "az": "Çən vaqonlarında neft və neft məhsullarının daşınmasına 1.20 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.20 на перевозку нефти и нефтепродуктов в цистернах.",
        "en": "A coefficient of 1.20 was applied for oil and oil products in tank wagons."
    },
    "MAIN_COEFF_1_20_REFRIGERATOR_TRANSIT": {
        "az": "Refrijerator daşımalarının tranziti üzrə 1.20 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.20 на транзит рефрижераторного подвижного состава.",
        "en": "A coefficient of 1.20 was applied for refrigerated transit transport."
    },
    "MAIN_COEFF_1_20_PRECIOUS_METALS": {
        "az": "Əlvan və qiymətli metalların daşınmasına 1.20 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.20 на перевозку цветных и драгоценных металлов.",
        "en": "A coefficient of 1.20 was applied for the transportation of non-ferrous and precious metals."
    },
    "MAIN_COEFF_1_015_INTERNATIONAL_LOADED": {
        "az": "Beynəlxalq yüklü daşımalar üzrə baza tariflərinə 1.015 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.015 на международные груженые перевозки к базовому тарифу.",
        "en": "A coefficient of 1.015 was applied for international loaded shipments to the base rate."
    },
    "MAIN_COEFF_0_85_PRIVATE_WAGON": {
        "az": "Xüsusi (özəl) vaqonların daşınmasına 0.85 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 0.85 на перевозки в собственных (приватных) вагонах.",
        "en": "A coefficient of 0.85 was applied for shipments in private-owned wagons."
    },
    "REF_SECTION_COEFF_1_70": {
        "az": "1 yük vaqonu + 1 dizel-generator tərkibli refrijerator seksiyasına 1.70 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.70 для рефсекции состава 1 грузовой вагон + 1 дизель-генератор.",
        "en": "A coefficient of 1.70 was applied for a reefer section with 1 cargo wagon + 1 diesel generator."
    },
    "REF_SECTION_COEFF_1_40": {
        "az": "2 yük vaqonu + 1 dizel-generator tərkibli refrijerator seksiyasına 1.40 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.40 для рефсекции состава 2 грузовых вагона + 1 дизель-генератор.",
        "en": "A coefficient of 1.40 was applied for a reefer section with 2 cargo wagons + 1 diesel generator."
    },
    "REF_SECTION_COEFF_1_10": {
        "az": "3 yük vaqonu + 1 dizel-generator tərkibli refrijerator seksiyasına 1.10 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 1.10 для рефсекции состава 3 грузовых вагона + 1 дизель-генератор.",
        "en": "A coefficient of 1.10 was applied for a reefer section with 3 cargo wagons + 1 diesel generator."
    },
    "REF_SECTION_COEFF_1_00": {
        "az": "4 yük vaqonu + 1 dizel-generator tərkibli refrijerator seksiyasına 1.00 əmsalı tətbiq edilmişdir.",
        "ru": "Применен стандартный коэффициент 1.00 для рефсекции состава 4 грузовых вагона + 1 дизель-генератор.",
        "en": "A standard coefficient of 1.00 was applied for a reefer section with 4 cargo wagons + 1 diesel generator."
    },
    "REF_SECTION_COEFF_0_85": {
        "az": "5 və daha çox yük vaqonu + 1 dizel-generator tərkibli refrijerator seksiyasına 0.85 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 0.85 для рефсекции состава 5 и более грузовых вагонов + 1 дизель-генератор.",
        "en": "A coefficient of 0.85 was applied for a reefer section with 5 or more cargo wagons + 1 diesel generator."
    },
    "REF_FRUIT_VEG_COEFF_0_60": {
        "az": "Tarif Razılaşması iştirakçısı olan ölkələrdə istehsal olunmuş meyvə-tərəvəz yüklərinə 0.60 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 0.60 на перевозку плодоовощной продукции, произведенной в странах Тарифного Соглашения.",
        "en": "A coefficient of 0.60 was applied for fruit and vegetable products originating from Tariff Agreement countries."
    },
    "REF_DIESEL_GENERATOR_AXLE_RATE": {
        "az": "Özəl refrijerator seksiyasının tərkibində gedən dizel-generator vaqonu üçün hər ox-km-ə 0.12 İsveçrə frankı tarifi tətbiq edilmişdir.",
        "ru": "Применен тариф 0.12 CHF за 1 ось-км для дизель-генераторного вагона в составе приватной рефсекции.",
        "en": "A rate of 0.12 CHF per axle-km was applied for a diesel generator wagon within a private reefer section."
    },
    "REF_EMPTY_WAGON_IN_LOADED_SECTION_AXLE_RATE": {
        "az": "Yüklü refrijerator seksiyasının tərkibində olan boş vaqon üçün hər ox-km-ə 0.10 İsveçrə frankı tarifi tətbiq edilmişdir.",
        "ru": "Применен тариф 0.10 CHF за 1 ось-км для порожнего вагона в составе груженой рефсекции.",
        "en": "A rate of 0.10 CHF per axle-km was applied for an empty wagon within a loaded reefer section."
    },
    "CAR_CARRIER_TWO_TIER_COEFF_0_80": {
        "az": "Avtomobil daşıyan ikimərtəbəli platformalarda daşınmaya 0.80 əmsalı tətbiq edilmişdir.",
        "ru": "Применен коэффициент 0.80 для перевозки автомобилей на двухъярусных платформах.",
        "en": "A coefficient of 0.80 was applied for vehicle transport on two-tier platforms."
    },

    # ------------------------------------------------------------------------------
    # БЛОК: Локализация п. 3.2.6 (Автопоезда, прицепы и автокузова на спецплатформах)
    # ------------------------------------------------------------------------------
    "ROAD_TRAIN_SPECIAL_PLATFORM_RULE_3_2_6": {
        "az": "Xüsusi təyinatlı platformalarda avtoqatarların, qoşquların və yarımqoşquların daşınması haqqı Cədvəl 5 (sütun 7 və 8) üzrə hesablanmışdır (bənd 3.2.6).",
        "ru": "Расчет провозной платы за перевозку автопоездов, прицепов и полуприцепов на спецплатформах выполнен по Таблице 5 (колонки 7 и 8, п. 3.2.6).",
        "en": "Freight charge for road trains, trailers, and semi-trailers on special platforms calculated according to Table 5 (columns 7 and 8, clause 3.2.6)."
    },

    # ------------------------------------------------------------------------------
    # БЛОК: Локализация Таблицы 7 (Контейнерные и малотоннажные отправки)
    # ------------------------------------------------------------------------------
    "TABLE_7_BASE_LOOKUP": {
        "ru": "Базовая ставка по Таблице 7 ({interval} км, колонка {column}): {base_rate_chf} CHF",
        "az": "Cədvəl 7 üzrə baza tarifi ({interval} km, sütun {column}): {base_rate_chf} CHF",
        "en": "Base rate per Table 7 ({interval} km, column {column}): {base_rate_chf} CHF",
    },
    "TABLE_7_COL_2_WAGON_5T": {
        "ru": "Повагонная отправка малой тоннажности (категория 5 тонн)",
        "az": "Kiçik tonnajlı vaqon daşıması (5 ton kateqoriyası)",
        "en": "Small-tonnage wagon shipment (5-ton category)",
    },
    "TABLE_7_COL_3_WAGON_10T": {
        "ru": "Повагонная отправка малой тоннажности (категория 10 тонн)",
        "az": "Kiçik tonnajlı vaqon daşıması (10 ton kateqoriyası)",
        "en": "Small-tonnage wagon shipment (10-ton category)",
    },
    "TABLE_7_COL_4_WAGON_15T": {
        "ru": "Повагонная отправка малой тоннажности (категория 15 тонн)",
        "az": "Kiçik tonnajlı vaqon daşıması (15 ton kateqoriyası)",
        "en": "Small-tonnage wagon shipment (15-ton category)",
    },
    "TABLE_7_COL_5_WAGON_20T": {
        "ru": "Повагонная отправка малой тоннажности (категория 20 тонн)",
        "az": "Kiçik tonnajlı vaqon daşıması (20 ton kateqoriyası)",
        "en": "Small-tonnage wagon shipment (20-ton category)",
    },
    "TABLE_7_COL_6_WAGON_25T": {
        "ru": "Повагонная отправка малой тоннажности (категория 25 тонн)",
        "az": "Kiçik tonnajlı vaqon daşıması (25 ton kateqoriyası)",
        "en": "Small-tonnage wagon shipment (25-ton category)",
    },
    "TABLE_7_COL_6_PASSENGER_POSTAL": {
        "ru": "Перевозка в пассажирском вагоне / Почтовое отправление (п. 3.1.2.5, колонка 6)",
        "az": "Sərnişin vaqonunda daşıma / Poçt göndərişi (bənd 3.1.2.5, sütun 6)",
        "en": "Carriage in passenger car / Postal shipment (clause 3.1.2.5, column 6)",
    },
    "TABLE_7_MIN_PASSENGER_POSTAL_WEIGHT_66T": {
        "ru": "Примененая минимальная расчетная масса 66 тонн для пассажирского/почтового вагона (фактическая: {actual_weight} т)",
        "az": "Sərnişin/poçt vaqonu üçün minimum 66 ton hesablama çəkisi tətbiq olunub (faktiki: {actual_weight} t)",
        "en": "Minimum billable weight of 66 tons applied for passenger/postal car (actual: {actual_weight} t)",
    },
    "TABLE_7_COL_7_CONTAINER_3T_LOADED": {
        "ru": "Среднетоннажный контейнер 3т (гружёный)",
        "az": "Orta tonnajlı konteyner 3t (yüklü)",
        "en": "Medium-tonnage container 3t (loaded)",
    },
    "TABLE_7_COL_8_CONTAINER_5T_LOADED": {
        "ru": "Среднетоннажный контейнер 5т (гружёный)",
        "az": "Orta tonnajlı konteyner 5t (yüklü)",
        "en": "Medium-tonnage container 5t (loaded)",
    },
    "TABLE_7_COL_9_CONTAINER_3T_EMPTY": {
        "ru": "Среднетоннажный контейнер 3т (порожний)",
        "az": "Orta tonnajlı konteyner 3t (boş)",
        "en": "Medium-tonnage container 3t (empty)",
    },
    "TABLE_7_COL_10_CONTAINER_5T_EMPTY": {
        "ru": "Среднетоннажный контейнер 5т (порожний)",
        "az": "Orta tonnajlı konteyner 5t (boş)",
        "en": "Medium-tonnage container 5t (empty)",
    },

    # ------------------------------------------------------------------------------
    # БЛОК: Локализация правила 3.1.2.6 (Транспортеры 4, 6, 8 осей)
    # ------------------------------------------------------------------------------
    "MIN_WEIGHT_TRANSPORTER_AXLE_NORMATIVE": {
        "ru": "Применена минимальная расчетная масса {applied_weight} тонн для {axle_count}-осного транспортера (п. 3.1.2.6, фактическая: {actual_weight} т)",
        "az": "{axle_count} oxlu transporter üçün minimum {applied_weight} ton hesablama çəkisi tətbiq olunub (bənd 3.1.2.6, faktiki: {actual_weight} t)",
        "en": "Minimum billable weight of {applied_weight} tons applied for {axle_count}-axle transporter (clause 3.1.2.6, actual: {actual_weight} t)",
    },

    "MAIN_COEFF_SPECIAL_PLATFORM_OVER_19M_1_20": {
        "az": "İnventar parka məsub, oxları arasındakı məsafə 19 metrdən artıq olan ixtisaslaşdırılmış platformalarda əndazəli yüklərin daşınmasına 1,20 əmsalı tətbiq edilib (bənd 3.1.2.7).",
        "ru": "Применен коэффициент 1.20 на перевозку габаритных грузов на специализированных платформах инвентарного парка длиной более 19 м (п. 3.1.2.7).",
        "en": "A factor of 1.20 was applied for the transportation of gauged cargo on specialized platforms of the inventory fleet over 19m long (clause 3.1.2.7)."
    },

    "MAIN_EMPTY_PRIVATE_WAGON_0_10_AXLE_KM": {
        "az": "Özəl/icarəyə götürülmüş boş vaqonların daşınması haqqı hər ox-km üçün 0,10 İsveçrə frankı tarifi ilə hesablanıb (bənd 3.2.2).",
        "ru": "Расчет провозной платы за перевозку собственных/арендованных порожних вагонов выполнен по ставке 0.10 CHF/ось-км (п. 3.2.2).",
        "en": "Transportation fee for private/leased empty wagons calculated at 0.10 CHF per axle-km (clause 3.2.2)."
    },

    # ------------------------------------------------------------------------------
    # БЛОК: Локализация п. 3.3.1 (Груженые İNV / ANV на спецплатформах, мин. 10т)
    # ------------------------------------------------------------------------------
    "INV_ANV_MIN_WEIGHT_10T_RULE_3_3_1": {
        "az": "Xüsusi təyinatlı platformalarda yüklü İNV və ANV daşınması üçün minimum 10 ton hesablama çəkisi tətbiq olunub (bənd 3.3.1, faktiki: {actual_weight} t).",
        "ru": "Применена минимальная расчетная масса 10 тонн для груженых İNV/ANV на спецплатформах (п. 3.3.1, фактическая: {actual_weight} т).",
        "en": "Minimum billable weight of 10 tons applied for loaded İNV/ANV on special platforms (clause 3.3.1, actual: {actual_weight} t)."
    },

    # ------------------------------------------------------------------------------
    # БЛОК: Локализация п. 3.3.2 (Порожние автопоезда/полуприцепы — 7т, кузова — 5т)
    # ------------------------------------------------------------------------------
    "EMPTY_ROAD_TRAIN_WEIGHT_7T_RULE_3_3_2": {
        "az": "Xüsusi təyinatlı platformalarda boş avtoqatarlar, qoşqular və yarımqoşqular üçün 7 ton hesablama çəkisi tətbiq olunub (bənd 3.3.2).",
        "ru": "Применена фиксированная расчетная масса 7 тонн для порожних автопоездов/прицепов/полуприцепов на спецплатформах (п. 3.3.2).",
        "en": "Fixed billable weight of 7 tons applied for empty road trains/trailers/semi-trailers on special platforms (clause 3.3.2)."
    },
    "EMPTY_AUTO_BODY_WEIGHT_5T_RULE_3_3_2": {
        "az": "Xüsusi təyinatlı platformalarda çıxarılan boş avtomobil kuzovları üçün 5 ton hesablama çəkisi tətbiq olunub (bənd 3.3.2).",
        "ru": "Применена фиксированная расчетная масса 5 тонн для съемных порожних автокузовов на спецплатформах (п. 3.3.2).",
        "en": "Fixed billable weight of 5 tons applied for empty detachable truck bodies on special platforms (clause 3.3.2)."
    },

    # ------------------------------------------------------------------------------
    # БЛОК: Справочные определения İNV и ANV
    # ------------------------------------------------------------------------------
    "INV_DEFINITION": {
        "az": "İNV — nəqliyyat növü dəyişdirilən zaman yükün özü boşalmadan iki və daha artıq nəqliyyat vasitəsində daşınan konteyner, çıxarılan avtomobil kuzovları və yarımqoşqular.",
        "ru": "İNV — контейнер, съемные автомобильные кузова и полуприцепы, перевозимые на двух и более транспортных средствах без выгрузки самого груза при смене вида транспорта.",
        "en": "İNV — containers, detachable truck bodies and semi-trailers transported on two or more means of transport without unloading the cargo itself when changing modes of transport."
    },
    "ANV_DEFINITION": {
        "az": "ANV — dəmir yolu nəqliyyatından əvvəl və sonra hərəkətdə olan yüklü və ya boş halda avtomobil, avtoqatar və qoşqular.",
        "ru": "ANV — груженый или порожний автомобиль, автопоезд и прицепы, находящиеся в движении до и после железнодорожного транспорта.",
        "en": "ANV — loaded or empty trucks, road trains and trailers in motion before and after rail transport."
    },

    # ------------------------------------------------------------------------------
    # БЛОК: Локализация п. 3.4.3.1 (Специализированные контейнеры / Танк-контейнеры / Рефконтейнеры)
    # ------------------------------------------------------------------------------
    "SPECIAL_CONTAINER_TANK_REF_RULE_3_4_3_1": {
        "az": "Xüsusi təyinatlı konteynerlər (tank və refkonteynerlər / şərab və meyvə şirələri) üçün cədvəl 10/8 tarifləri tətbiq olunub (bənd 3.4.3.1).",
        "ru": "Применены тарифы для специализированных контейнеров (танк-контейнеры, рефконтейнеры, вино/соки) по п. 3.4.3.1.",
        "en": "Tariffs for specialized containers (tank containers, reefer containers, wine/juices) applied under clause 3.4.3.1."
    },

    "DIESEL_GENERATOR_WAGON_RULE_3_4_3_2": {
            "az": "Xüsusi (daşıyıcıya məxsus olmayan) dizel-generator vaqonunun daşınma haqqı hər 1 ox-km üçün 0.12 İsveçrə frankı ilə hesablanmışdır (bənd 3.4.3.2).",
            "ru": "Провозная плата за приватный вагон-дизель-генератор рассчитана по ставке 0.12 CHF за 1 ось-км (п. 3.4.3.2).",
            "en": "Freight charge for private diesel-generator wagon calculated at 0.12 CHF per axle-km (clause 3.4.3.2)."
        },
        "ATTENDANTS_FEE_RULE_3_4_3_2": {
            "az": "Dizel-generator vaqonunda gedən {count} nəfər bələdçinin gediş haqqı hesablanmışdır (bənd 3.4.3.2).",
            "ru": "Начислена плата за проезд {count} проводников в вагоне-дизель-генераторе (п. 3.4.3.2).",
            "en": "Fare applied for {count} attendants in the diesel-generator wagon (clause 3.4.3.2)."
        },
        "SERVICE_CREW_FREE_RULE_3_4_3_2": {
            "az": "Xidməti briqada üçün gediş haqqı tutulmur (bənd 3.4.3.2).",
            "ru": "Плата за проезд сервисной бригады не взимается (п. 3.4.3.2).",
            "en": "No fare charged for the service crew (clause 3.4.3.2)."
        },
        "DIESEL_GENERATOR_CONTAINER_COEFF_1_35": {
        "az": "Dizel-generator konteynerləri üçün Cədvəl 8-in qiymətlərinə 1.35 əmsalı tətbiq edilmişdir (bənd 3.4.5).",
        "ru": "Применен коэффициент 1.35 к ставкам Таблицы 8 для контейнеров-дизель-генераторов (п. 3.4.5).",
        "en": "Coefficient 1.35 applied to Table 8 rates for diesel-generator containers (clause 3.4.5)."
        },

        "CONTAINER_PLATFORM_COEFF_1_40": {
        "az": "Özəl konteyner-platformalar üçün Cədvəl 8-in qiymətlərinə 1.40 əmsalı tətbiq edilmişdir (bənd 3.4.6).",
        "ru": "Применен коэффициент 1.40 к ставкам Таблицы 8 для приватных контейнеров-платформ (п. 3.4.6).",
        "en": "Coefficient 1.40 applied to Table 8 rates for private platform containers (clause 3.4.6)."
        },

        "OPEN_TOP_CONTAINER_COEFF_1_40": {
        "az": "Özəl üstüaçıq konteynerlər üçün Cədvəl 8-in qiymətlərinə 1.40 əmsalı tətbiq edilmişdir (bənd 3.4.7).",
        "ru": "Применен коэффициент 1.40 к ставкам Таблицы 8 для открытых контейнеров Open Top (п. 3.4.7).",
        "en": "Coefficient 1.40 applied to Table 8 rates for Open Top containers (clause 3.4.7)."
        }
    }

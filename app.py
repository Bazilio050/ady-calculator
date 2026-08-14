import os
import streamlit as st
from google import genai
from nlu import call_gemini_nlu, validate_nlu_input
try:
    from engine import process_full_calculation
except Exception as err:
    import traceback
    st.error(f"Ошибка в engine.py: {err}")
    st.code(traceback.format_exc())
    st.stop()

st.set_page_config(
    page_title="ADY — Tariff Calculator", 
    page_icon="🚆", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "calc_result" not in st.session_state:
    st.session_state.calc_result = None
if "nlu_res" not in st.session_state:
    st.session_state.nlu_res = None
if "missing_data" not in st.session_state:
    st.session_state.missing_data = None

st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #0e2a47 0%, #1a4a75 100%);
        padding: 6px 16px;
        border-radius: 6px;
        color: white;
        margin-top: 6px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .main-header p {
        color: #b0c4de !important;
        margin: 1px 0 0 0;
        font-size: 0.8rem;
        line-height: 1.2;
    }
    .agt-footer {
        margin-top: 40px;
        padding: 16px;
        background-color: #f8f9fa;
        border-top: 3px solid #ff5500;
        border-radius: 8px;
        text-align: center;
        color: #333333;
    }
    .agt-footer p {
        margin: 2px 0;
        font-size: 0.92rem;
    }
    .agt-slogan {
        font-size: 0.82rem;
        letter-spacing: 2px;
        color: #555555;
        text-transform: uppercase;
        margin-top: 4px !important;
        font-weight: 600;
    }

    @keyframes trainDrive {
        0% { left: -15%; }
        100% { left: 105%; }
    }
    .train-track {
        position: relative;
        width: 100%;
        height: 55px;
        background: #0e2a47;
        border-bottom: 3px dashed #ff5500;
        overflow: hidden;
        border-radius: 8px;
        margin: 15px 0 5px 0;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }
    .train-emoji {
        position: absolute;
        font-size: 28px;
        top: 6px;
        white-space: nowrap;
        animation: trainDrive 2.2s linear infinite;
    }
    .train-loader-text {
        text-align: center;
        font-weight: 600;
        font-size: 0.95rem;
        color: #ff5500;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru", 
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt ili",
        "year_select": "Fraxt ili:", 
        "lang_select": "Dil / Language:", 
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Beyuk kasik\nYük: Qara metallar (GNG 72), 35 ton\nVəziyyət: SPS örtülü vaqon",
        "calc_btn": "🚀 Tarifi hesabla", 
        "warning_empty": "Xahiş olunur, hesablaşma şərtlərini daxil edin.",
        "spinner_text": "ADY Policy {} tarifləri üzrə hesablanır...", 
        "success": "Hesablama uğurla tamamlandı! (ADY Policy {})",
        "result_title": "📋 Hesablama nəticəsi:", 
        "sec1_title": "1. Marşrut və daşıma şərtləri", 
        "sec2_title": "2. Əmsallar və valyuta məzənnəsi",
        "sec3_title": "3. Tarifin hesablanması", 
        "formula_title": "Hesablama düsturu:", 
        "rates_title": "Yekun tariflər:",
        "notes_title": "Qeydlər:", 
        "disclaimer": "Qeyd olunan tariflərə stansiya xərcləri və əlavə yığımlar daxil deyildir.",
        "col_param": "Parametr", 
        "col_val": "Qiymət / Həcm", 
        "col_rate_type": "Tarif növü", 
        "col_amount": "Məblağ",
        "lbl_route": "Marşrut", 
        "lbl_type": "Daşıma növü", 
        "lbl_dist": "Məsafə", 
        "lbl_cargo": "Yük / Vəziyyət",
        "lbl_weight": "Faktiki / Hesablaşma çəkisi", 
        "lbl_period": "Dövr", 
        "lbl_exchange": "CHF/USD", 
        "lbl_base_rate": "Baza tarifi",
        "lbl_net_rate": "Yekün ADY tarifi", 
        "lbl_express_rate": "Yekun tarif (ADY Express +2% daxil)",
        "api_warning": "⚠️ Serverdə GEMINI_API_KEY tapılmadı. Xahiş olunur, sistem tənzimləmələrini yoxlayın.", 
        "api_label": "Gemini API Key:",
        "type_import": "İdxal daşınması", 
        "type_export": "İxrac daşınması", 
        "type_transit": "Tranzit daşınması",
        "unit_ton": "USD/t", 
        "unit_wagon": "USD/vaqon", 
        "table_name": "Cədvəl", 
        "missing_title": "⚠️ Hesablama üçün aşağıdakı məlumatlar çatışmır:",
        "footer_owner": "Bu layihə **AGT Cargo** şirkətinə məxsusdur.",
        "guide_title": "💡 Daxiletmə nümunələri və dəmir yolu terminləri (Açmaq üçün basın)"
    },
    "RU": {
        "title": "Тарифный калькулятор ADY", 
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:", 
        "lang_select": "Язык / Language:", 
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Беюк Касик\nГруз: Черные металлы (ГНГ 72), 35 тонн\nСостояние: СПС крытый вагон",
        "calc_btn": "🚀 Рассчитать тариф", 
        "warning_empty": "Пожалуйста, введите условия расчета.",
        "spinner_text": "Считаем тариф согласно Тарифной политике {}...", 
        "success": "Расчет успешно выполнен! (Тарифная политика {})",
        "result_title": "📋 Результат расчета:", 
        "sec1_title": "1. Маршрут и условия перевозки", 
        "sec2_title": "2. Коэффициенты и курс валют",
        "sec3_title": "3. Расчет тарифа", 
        "formula_title": "Формула расчета:", 
        "rates_title": "Итоговые тарифы:",
        "notes_title": "Примечания:", 
        "disclaimer": "Ставки приведены без учета станционных расходов и дополнительных сборов.",
        "col_param": "Параметр", 
        "col_val": "Значение / Объем", 
        "col_rate_type": "Тип тарифа", 
        "col_amount": "Сумма",
        "lbl_route": "Маршрут", 
        "lbl_type": "Вид перевозки", 
        "lbl_dist": "Расстояние", 
        "lbl_cargo": "Груз / Состояние",
        "lbl_weight": "Фактический / Расчетный вес", 
        "lbl_period": "Период", 
        "lbl_exchange": "CHF/USD", 
        "lbl_base_rate": "Базовый тариф",
        "lbl_net_rate": "Итоговый тариф", 
        "lbl_express_rate": "Итоговый тариф (включая ADY Express +2%)",
        "api_warning": "⚠️ На сервере не найден GEMINI_API_KEY. Пожалуйста, проверьте настройки системы.", 
        "api_label": "Gemini API Key:",
        "type_import": "Импортная перевозка", 
        "type_export": "Экспортная перевозка", 
        "type_transit": "Транзитная перевозка",
        "unit_ton": "USD/т", 
        "unit_wagon": "USD/вагон", 
        "table_name": "Таблица", 
        "missing_title": "⚠️ Для точного расчета не хватает следующих данных:",
        "footer_owner": "Данный проект принадлежит компании **AGT Cargo**.",
        "guide_title": "💡 Шаблоны запросов и справочник сокращений (Нажмите для просмотра)"
    },
    "EN": {
        "title": "ADY Tariff Calculator", 
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:", 
        "lang_select": "Language:", 
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Yalama - Beyuk kasik\nCargo: Ferrous metals (NHM 72), 35 tons\nCondition: SPS covered wagon",
        "calc_btn": "🚀 Calculate Freight Rate", 
        "warning_empty": "Please enter shipment requirements.",
        "spinner_text": "Calculating rates according to Tariff Policy {}...", 
        "success": "Calculation completed successfully! (Tariff Policy {})",
        "result_title": "📋 Calculation Results:", 
        "sec1_title": "1. Route and Shipment Conditions", 
        "sec2_title": "2. Coefficients and Exchange Rate",
        "sec3_title": "3. Rate Calculation", 
        "formula_title": "Calculation Formula:", 
        "rates_title": "Final Rates:",
        "notes_title": "Notes:", 
        "disclaimer": "Rates are quoted excluding station charges and additional fees.",
        "col_param": "Parameter", 
        "col_val": "Value / Volume", 
        "col_rate_type": "Rate Type", 
        "col_amount": "Amount",
        "lbl_route": "Route", 
        "lbl_type": "Shipment Type", 
        "lbl_dist": "Distance", 
        "lbl_cargo": "Cargo / Condition",
        "lbl_weight": "Actual / Billable Weight", 
        "lbl_period": "Period", 
        "lbl_exchange": "CHF/USD", 
        "lbl_base_rate": "Base Tariff",
        "lbl_net_rate": "Final Tariff", 
        "lbl_express_rate": "Final Tariff (incl. ADY Express +2%)",
        "api_warning": "⚠️ GEMINI_API_KEY not found on server. Please check system configuration.", 
        "api_label": "Gemini API Key:",
        "type_import": "Import shipment", 
        "type_export": "Export shipment", 
        "type_transit": "Transit shipment",
        "unit_ton": "USD/t", 
        "unit_wagon": "USD/wagon", 
        "table_name": "Table", 
        "missing_title": "⚠️ Required parameters missing:",
        "footer_owner": "This project belongs to **AGT Cargo**.",
        "guide_title": "💡 Quick Templates & Railway Glossary (Click to expand)"
    }
}

logo_path = "Logo.png" if os.path.exists("Logo.png") else ("logo.png" if os.path.exists("logo.png") else None)

left_col, _ = st.columns([3, 2])

with left_col:
    if logo_path:
        st.image(logo_path, width=200)
    
    ctrl_col, _ = st.columns([1.2, 2.8])
    with ctrl_col:
        selected_lang = st.selectbox("🌐 Dil / Language:", options=["AZ", "RU", "EN"], index=0)
        t = UI_TEXT[selected_lang]
        selected_year = st.selectbox(f"⚙️ {t['year_select']}", options=["2026", "2027"], index=0)

st.markdown(f"""
    <div class="main-header">
        <h1>🚆 {t['title']}</h1>
        <p>{t['subtitle'].format(selected_year)}</p>
    </div>
""", unsafe_allow_html=True)

with st.expander(t["guide_title"]):
    if selected_lang == "AZ":
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
            "📦 Ümumi vaqonlar", "📦 Konteynerlər", "❄️ Ref / Termos", "🛢️ Çənlər", 
            "🏗️ Transportyorlar", "🚛 Xüsusi platforma", "📐 Əndazəsiz yüklər", 
            "⚙️ Öz oxları üzərində", "📦 Yığma göndərmə", "⚠️ Təhlükəli yüklər"
        ])

        with tab1:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [Çəki]t, [Vaqon növü], [SPS/MPS]`\n💡 **Nümunə:** `Yalama – Böyük Kəsik, 45t, örtülü vaqon, SPS`")
        with tab2:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [20/40]fut konteyner, [yüklü/boş], SPS`\n💡 **Nümunə:** `Yalama – Abşeron, 40-futluq konteyner, yüklü, SPS`")
        with tab3:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [5+1 / thermos], [Çəki]t, SPS`\n💡 **Nümunə:** `Yalama – Biləcəri, 0207, 5+1, 35t, SPS`")
        with tab4:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [GNG], çən vaqonu, [Çəki]t, SPS`\n💡 **Nümunə:** `Yalama – Güzdək, 2713, çən vaqonu, 60t, SPS`")
        with tab5:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [Ox sayı]-oxlu transportyor, [Çəki]t`\n💡 **Nümunə:** `Astara – Yalama, 8-oxlu transportyor, 15t`")
        with tab6:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [avtoqatar/qoşqu/scep >19m], [Çəki]t`\n💡 **Nümunə:** `Yalama – Abşeron, avtoqatar, 25t, SPS`")
        with tab7:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [Çəki]t, [Əndazəsizlik dərəcəsi]`\n💡 **Nümunə:** `Yalama – Böyük Kəsik, 35t, 3-yuxarı əndazə platforma, SPS`")
        with tab8:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [lokomotiv/kran/vaqon] öz oxları üzərində, [təmirə]`\n💡 **Nümunə:** `Yalama – Abşeron, lokomotiv 8601 öz oxları üzərində, 40t`\n📌 **Qaydalar:** Cədvəl 3/4 × 0.50 (bənd 3.7.1). Təmirə gedən МПС — 0.10 CHF/ox-km (bənd 3.7.2). Boş transportyor перегонка — ox sayına görə 0.12-0.40 CHF/ox-km (bənd 3.7.8).")
        with tab9:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], yığma göndərmə (сборный груз), [Çəki]t`\n💡 **Nümunə:** `Yalama – Abşeron, yığma göndərmə, 8t, örtülü vaqon`\n📌 **Qaydalar:** Minimum hesablaşma çəkisi norması 10 ton (изотермический vaqonda 25 ton) götürülür (bənd 3.8).")
        with tab10:
            st.markdown("📐 **Şablon:** `[Haradan] -> [Haraya], [BMT Kodu], [Çəki]t, SPS`\n💡 **Nümunə:** `Yalama – Abşeron, 35t, təhlükəli BMT 2927, SPS`")

    elif selected_lang == "RU":
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
            "📦 Универсальные", "📦 Контейнеры", "❄️ Реф / Термос", "🛢️ Цистерны", 
            "🏗️ Транспортеры", "🚛 Спецплатформы", "📐 Негабарит", 
            "⚙️ На своих осях", "📦 Сборные грузы", "⚠️ Опасные грузы"
        ])

        with tab1:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [Вес]т, [Тип вагона], [СПС/МПС]`\n💡 **Пример:** `Ялама – Беюк Кясик, 45т, крытый вагон, СПС`")
        with tab2:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [20/40]фут контейнер, [гружёный/порожний], СПС`\n💡 **Пример:** `Ялама – Апшерон, 40-футовый контейнер гружёный, СПС`")
        with tab3:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [5+1 / термос], [Вес]т, СПС`\n💡 **Пример:** `Ялама – Баладжары, 0207, 5+1, 35т, СПС`")
        with tab4:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [ГНГ], цистерна, [Вес]т, СПС`\n💡 **Пример:** `Ялама – Гюздек, 2713, цистерна, 60т, СПС`")
        with tab5:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [Осей]-осный транспортер, [Вес]т`\n💡 **Пример:** `Астара – Ялама, 8-осный транспортер, 15т`")
        with tab6:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [автопоезд/прицеп/сцеп >19м], [Вес]т`\n💡 **Пример:** `Ялама – Апшерон, автопоезд, 25т, СПС`")
        with tab7:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [Вес]т, [Степень негабаритности]`\n💡 **Пример:** `Ялама – Беюк Кясик, 35т, 3-верхняя негабаритность, платформа, СПС`")
        with tab8:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [локомотив/кран/вагон] на своих осях, [в ремонт]`\n💡 **Пример:** `Ялама – Апшерон, локомотив 8601 на своих осях, 40т`\n📌 **Правила:** Таблица 3/4 × 0.50 (п. 3.7.1). В ремонт МПС — 0.10 CHF/ось-км (п. 3.7.2). Перегонка порожних транспортеров — 0.12-0.40 CHF/ось-км по осям (п. 3.7.8).")
        with tab9:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], сборный груз, [Вес]т`\n💡 **Пример:** `Ялама – Апшерон, сборный груз, 8т, крытый вагон`\n📌 **Правила:** Минимальный расчётный вес 10 тонн (в изотермическом 25 тонн) (п. 3.8).")
        with tab10:
            st.markdown("📐 **Шаблон:** `[Откуда] -> [Куда], [Код ООН/BMT], [Вес]т, СПС`\n💡 **Пример:** `Ялама – Апшерон, 35т, опасный BMT 2927, СПС`")

    else:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
            "📦 Universal", "📦 Containers", "❄️ Ref / Thermos", "🛢️ Tank wagons", 
            "🏗️ Transporters", "🚛 Special platform", "📐 Oversize", 
            "⚙️ Own axles", "📦 Consolidated", "⚠️ Dangerous"
        ])

        with tab1:
            st.markdown("📐 **Template:** `[From] -> [To], [Weight]t, [Wagon type], [SPS/MPS]`\n💡 **Example:** `Yalama – Beyuk Kasik, 45t, covered wagon, SPS`")
        with tab2:
            st.markdown("📐 **Template:** `[From] -> [To], [20/40]ft container, [loaded/empty], SPS`\n💡 **Example:** `Yalama – Absheron, 40ft container, loaded, SPS`")
        with tab3:
            st.markdown("📐 **Template:** `[From] -> [To], [5+1 / thermos], [Weight]t, SPS`\n💡 **Example:** `Yalama – Bilajari, 0207, 5+1, 35t, SPS`")
        with tab4:
            st.markdown("📐 **Template:** `[From] -> [To], [NHM], tank wagon, [Weight]t, SPS`\n💡 **Example:** `Yalama – Guzdek, 2713, tank wagon, 60t, SPS`")
        with tab5:
            st.markdown("📐 **Template:** `[From] -> [To], [Axles]-axle transporter, [Weight]t`\n💡 **Example:** `Astara – Yalama, 8-axle transporter, 15t`")
        with tab6:
            st.markdown("📐 **Template:** `[From] -> [To], [road train/trailer/scep >19m], [Weight]t`\n💡 **Example:** `Yalama – Absheron, road train, 25t, SPS`")
        with tab7:
            st.markdown("📐 **Template:** `[From] -> [To], [Weight]t, [Oversize degree]`\n💡 **Example:** `Yalama – Beyuk Kasik, 35t, 3rd upper oversize platform, SPS`")
        with tab8:
            st.markdown("📐 **Template:** `[From] -> [To], [locomotive/crane/wagon] on own axles`\n💡 **Example:** `Yalama – Absheron, locomotive 8601 on own axles, 40t`\n📌 **Rules:** Table 3/4 × 0.50 (clause 3.7.1). Repair MPS — 0.10 CHF/axle-km (clause 3.7.2). Empty transporter repositioning — 0.12-0.40 CHF/axle-km (clause 3.7.8).")
        with tab9:
            st.markdown("📐 **Template:** `[From] -> [To], consolidated cargo, [Weight]t`\n💡 **Example:** `Yalama – Absheron, consolidated cargo, 8t, covered wagon`\n📌 **Rules:** Minimum billable weight norm 10 tons (25 tons in isothermal wagon) (clause 3.8).")
        with tab10:
            st.markdown("📐 **Template:** `[From] -> [To], [UN Code], [Weight]t, SPS`\n💡 **Example:** `Yalama – Absheron, 35t, dangerous UN 2927, SPS`")

user_input = st.text_area(t["input_header"], height=120, placeholder=t["input_placeholder"])

user_api_key = os.environ.get("GEMINI_API_KEY", "")
if not user_api_key and "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]

if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
        st.session_state.calc_result = None
    elif not user_api_key.strip():
        st.error(t["api_warning"])
        st.session_state.calc_result = None
    else:
        loader_placeholder = st.empty()
        loader_placeholder.markdown(f"""
            <div class="train-track">
                <div class="train-emoji">🚂🚃🚃🚃💨</div>
            </div>
            <div class="train-loader-text">
                ⏳ {t['spinner_text'].format(selected_year)}
            </div>
        """, unsafe_allow_html=True)

        try:
            client = genai.Client(api_key=user_api_key.strip())
            nlu_res = call_gemini_nlu(client, user_input, selected_lang)
            
            gng_val = str(nlu_res.get("gng_code") or nlu_res.get("cargo_gng_code") or "").strip()
            cargo_val = str(nlu_res.get("gng_name") or nlu_res.get("cargo_name") or "").strip()

            is_default_or_empty = (
                not gng_val or gng_val in ["00000000", "0000", "0"] or
                not cargo_val or "Aşırılan" in cargo_val or "Ümumi" in cargo_val
            )

            if is_default_or_empty:
                nlu_res["gng_code"] = "00000000"
                nlu_res["cargo_gng_code"] = "00000000"
                
                cargo_defaults = {
                    "AZ": "Aşırılan yük",
                    "RU": "Общий / Генеральный груз",
                    "EN": "General cargo"
                }
                localized_cargo_name = cargo_defaults.get(selected_lang, "Aşırılan yük")
                
                nlu_res["cargo_name"] = localized_cargo_name
                nlu_res["gng_name"] = localized_cargo_name
            
            missing = validate_nlu_input(nlu_res, selected_lang)
            loader_placeholder.empty()

            if missing:
                st.session_state.missing_data = missing
                st.session_state.calc_result = None
            else:
                st.session_state.missing_data = None
                st.session_state.calc_result = process_full_calculation(nlu_res, user_input, selected_lang, selected_year, t)
                st.session_state.nlu_res = nlu_res

        except Exception as e:
            loader_placeholder.empty()
            st.error(f"Error: {str(e)}")
            st.session_state.calc_result = None

if st.session_state.missing_data:
    st.warning(t["missing_title"])
    for m in st.session_state.missing_data:
        st.markdown(f"* {m}")

elif st.session_state.calc_result:
    data = st.session_state.calc_result
    st.success(t["success"].format(selected_year))
    
    with st.expander("🔍 Gemini NLU JSON (Для проверки распознавания)"):
        st.json(st.session_state.nlu_res)

    p1, p2, p3 = data["part1"], data["part2"], data["part3"]
    
    st.markdown(f"#### 📍 {t['sec1_title']}")
    st.markdown(
        f"| {t['col_param']} | {t['col_val']} |\n"
        f"| :--- | :--- |\n"
        f"| **{t['lbl_route']}** | {p1['route']} |\n"
        f"| **{t['lbl_type']}** | {p1['shipment_type']} |\n"
        f"| **{t['lbl_dist']}** | {p1['distance']} |\n"
        f"| **{t['lbl_cargo']}** | {p1['cargo_and_wagon']} |\n"
        f"| **{t['lbl_weight']}** | {p1['weight_info']} |\n"
        f"| **{t['lbl_period']}** | {p1['period']} |"
    )

    st.markdown(f"#### ⚙️ {t['sec2_title']}")
    t2_rows = [
        f"| **{t['lbl_exchange']}** | {p2['exchange_rate']} |", 
        f"| **{t['lbl_base_rate']}** | {p2['base_tariff']} |"
    ]
    for coeff in p2.get("coefficients", []):
        t2_rows.append(f"| **{coeff['name']}** | {coeff['value']} |")
    st.markdown(f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n" + "\n".join(t2_rows))

    st.markdown(f"#### 📐 {t['sec3_title']}")
    st.code(p3["formula"], language="text")
    st.markdown(
        f"| {t['col_rate_type']} | {t['col_amount']} |\n"
        f"| :--- | :--- |\n"
        f"| **{t['lbl_net_rate']}** | **{p3['net_ady_rate']}** |\n"
        f"| **{t['lbl_express_rate']}** | **{p3['express_rate']}** |"
    )

    if p3.get("notes"):
        st.markdown(f"**{t['notes_title']}**")
        for idx, note in enumerate(p3["notes"], start=1):
            st.markdown(f"{idx}. *{note}*")

st.markdown(f"""
    <div class="agt-footer">
        <p>{t['footer_owner']}</p>
        <p class="agt-slogan">BE GLOBAL CONNECTED</p>
    </div>
""", unsafe_allow_html=True)

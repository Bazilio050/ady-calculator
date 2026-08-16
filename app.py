import os
import streamlit as st
from google import genai
from nlu import call_gemini_nlu, call_gemini_audio_nlu, validate_nlu_input

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

# Инициализация состояния
if "calc_result" not in st.session_state:
    st.session_state.calc_result = None
if "nlu_res" not in st.session_state:
    st.session_state.nlu_res = None
if "missing_data" not in st.session_state:
    st.session_state.missing_data = None
if "pending_transcript" not in st.session_state:
    st.session_state.pending_transcript = None
if "preview_nlu" not in st.session_state:
    st.session_state.preview_nlu = None
if "last_processed_audio_hash" not in st.session_state:
    st.session_state.last_processed_audio_hash = None

# Безопасное обновление текста ввода ДО отрисовки st.text_area
if st.session_state.pending_transcript:
    st.session_state.main_input_area = st.session_state.pending_transcript
    st.session_state.pending_transcript = None

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
        transform: scaleX(-1);
    }
    .train-loader-text {
        text-align: center;
        font-weight: 600;
        font-size: 0.95rem;
        color: #ff5500;
        margin-bottom: 15px;
    }

    /* Разделитель «ИЛИ» между текстом и голосом */
    .or-divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 18px 0;
        color: #888;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .or-divider::before, .or-divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #444;
    }
    .or-divider:not(:empty)::before {
        margin-right: .5em;
    }
    .or-divider:not(:empty)::after {
        margin-left: .5em;
    }

    div[data-testid="stAudioInput"] {
        border: 2px solid #ff5500 !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        background-color: rgba(255, 85, 0, 0.04) !important;
        margin: 12px 0 !important;
        box-shadow: 0 4px 12px rgba(255, 85, 0, 0.08) !important;
    }
    div[data-testid="stAudioInput"] button {
        width: 64px !important;
        height: 64px !important;
        border-radius: 50% !important;
        background-color: #ff5500 !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(255, 85, 0, 0.3) !important;
        transition: transform 0.15s ease, background-color 0.15s ease !important;
    }
    div[data-testid="stAudioInput"] button:active {
        transform: scale(0.92) !important;
        background-color: #e04b00 !important;
    }
    .audio-limit-note {
        font-size: 0.85rem;
        color: #ff5500;
        font-weight: 600;
        margin-top: -4px;
        margin-bottom: 10px;
    }

    .preview-card {
        background-color: #f0f4f8;
        border-left: 5px solid #0e2a47;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .preview-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #0e2a47;
        margin-bottom: 8px;
    }
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-route { background-color: #e3f2fd; color: #0d47a1; }
    .badge-gng-ok { background-color: #e8f5e9; color: #1b5e20; }
    .badge-gng-warn { background-color: #ffebee; color: #b71c1c; border: 1px solid #ef5350; }
    .badge-weight { background-color: #fff3e0; color: #e65100; }
    .badge-wagon { background-color: #f3e5f5; color: #4a148c; }
    </style>
""", unsafe_allow_html=True)

UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru", 
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt ili",
        "year_select": "Fraxt ili:", 
        "lang_select": "Dil / Language:", 
        "input_header": "Mətn ilə daxil etmə:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Beyuk kasik\nYük: Qara metallar (GNG 72), 35 ton\nVəziyyət: SPS örtülü vaqon",
        "or_divider": "VƏ YA SƏS İLƏ DAXİL EDİN",
        "voice_input_header": "🎙️ Səs ilə daxil etmə:",
        "audio_label": "Yazı üçün mikrofona basın",
        "audio_limit_error": "🛑 Səs yazısı çox uzundur (30 saniyədən çoxdur)! Lütfən, sorğunu daha qısa şəkildə yenidən yazın.",
        "stt_loading": "⏳ Səs yazısı tanınır...",
        "preview_title": "🔍 Səs yazısından oxunan parametrlər (Yoxlayın):",
        "wagon_default": "Vaqon",
        "clarify_needed": "Dəqiqləşdirilməli",
        "json_expander": "🔍 Gemini NLU JSON (Tanınmanın yoxlanılması üçün)",
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
        "lbl_guard_express_rate": "Mühafizə haqqı (ADY Express +2% daxil)",
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
        "guide_title": "💡 Daxiletmə nümunələri və dəmir yolu terminləri (Açmaq üçün basın)",
        "audio_note": "⏱️ Maksimum 30 saniyə. Danışdıqdan sonra dayandırın — mətn avtomatik daxil ediləcək."
    },
    "RU": {
        "title": "Тарифный калькулятор ADY", 
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:", 
        "lang_select": "Язык / Language:", 
        "input_header": "Ввод текстом:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Беюк Касик\nГруз: Черные металлы (ГНГ 72), 35 тонн\nСостояние: СПС крытый вагон",
        "or_divider": "ИЛИ НАДИКТУЙТЕ ГОЛОСОМ",
        "voice_input_header": "🎙️ Голосовой ввод:",
        "audio_label": "Нажмите на микрофон для записи",
        "audio_limit_error": "🛑 Запись превышает 30 секунд! Пожалуйста, повторите кратко.",
        "stt_loading": "⏳ Распознавание аудиозаписи...",
        "preview_title": "🔍 Параметры из голосового ввода (Проверьте):",
        "wagon_default": "Вагон",
        "clarify_needed": "Уточнить",
        "json_expander": "🔍 Gemini NLU JSON (Для проверки распознавания)",
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
        "lbl_guard_express_rate": "Сбор за охрану (включая ADY Express +2%)",
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
        "guide_title": "💡 Шаблоны запросов и справочник сокращений (Нажмите для просмотра)",
        "audio_note": "⏱️ Максимум 30 секунд. Нажмите стоп — текст автоматически подставится в поле."
    },
    "EN": {
        "title": "ADY Tariff Calculator", 
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:", 
        "lang_select": "Language:", 
        "input_header": "Text input:",
        "input_placeholder": "Example:\nRoute: Yalama - Beyuk kasik\nCargo: Ferrous metals (NHM 72), 35 tons\nCondition: SPS covered wagon",
        "or_divider": "OR RECORD VOICE",
        "voice_input_header": "🎙️ Voice input:",
        "audio_label": "Click microphone to record",
        "audio_limit_error": "🛑 Recording exceeds 30 seconds! Please re-record briefly.",
        "stt_loading": "⏳ Transcribing audio...",
        "preview_title": "🔍 Parameters extracted from voice (Check):",
        "wagon_default": "Wagon",
        "clarify_needed": "To be specified",
        "json_expander": "🔍 Gemini NLU JSON (For recognition check)",
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
        "lbl_guard_express_rate": "Guard fee (incl. ADY Express +2%)",
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
        "guide_title": "💡 Quick Templates & Railway Glossary (Click to expand)",
        "audio_note": "⏱️ Maximum 30 seconds. Stop recording to automatically populate the input field."
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
            "📦 Ümumi vaqonlar", "📦 Konteynerlər", "❄️ Ref / Termos", "🛢️ Çənlər", 
            "🏗️ Transportyorlar", "🚛 Xüsusi platforma", "📐 Əndazəsiz yüklər", 
            "⚙️ Öz oxları üzərində", "📦 Yığma göndərmə", "⚠️ Təhlükəli yüklər",
            "🧑‍✈️ Bələdçilər / Tepluşka"
        ])

        with tab1:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [GNG], [Çəki]t, [Vaqon növü], [SPS/MPS]`  
            💡 **Nümunə:** `Yalama – Böyük Kəsik, 4407, 45t, örtülü vaqon, SPS`  
            ⚙️ **Açar sözlər:** `örtülü`, `yarımvaqon`, `platforma`, `4407`, `SPS`, `MPS`, `boş`  
            📌 **Qayda:** Ümumi təyinatlı vaqonlar üçün İdxal/İxracda Cədvəl 3, Tranzitdə Cədvəl 4 tətbiq olunur (bənd 3.1).
            """)
        with tab2:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [20/40]fut konteyner, [yüklü/boş], SPS`  
            💡 **Nümunə:** `Yalama – Abşeron, 40-futluq konteyner, yüklü, SPS`  
            ⚙️ **Açar sözlər:** `20ft`, `40ft`, `konteyner`, `tank_container`, `ref_container`, `boş`  
            📌 **Qayda:** Unversal konteynerlər Cədvəl 8, xüsusi/tank/ref konteynerlər Cədvəl 10 üzrə hesablanır.
            """)
        with tab3:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [5+1 / thermos], [Çəki]t, SPS`  
            💡 **Nümunə:** `Yalama – Biləcəri, 0207, 5+1, 35t, SPS`  
            ⚙️ **Açar sözlər:** `ref`, `5+1`, `thermos`, `termos`, `izoterm`, `SPS`  
            📌 **Qayda:** İzotermik və soyuduculu hərəkət tərkibləri Cədvəl 5 üzrə hesablanır (bənd 3.1.2.1).
            """)
        with tab4:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [GNG], çən vaqonu, [Çəki]t, SPS`  
            💡 **Nümunə:** `Yalama – Güzdək, 2713, çən vaqonu, 60t, SPS`  
            ⚙️ **Açar sözlər:** `çən`, `cistern`, `2713`, `3404`, `27071`, `SPS`, `MPS`  
            📌 **Qayda:** Maye növlü yüklər Cədvəl 6 üzrə hesablanır. GNG 2707/2902 üçün özəl çənlərə 0.70 güzəşti tətbiq edilir (bənd 3.2.5).
            """)
        with tab5:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [Ox sayı]-oxlu transportyor, [Çəki]t`  
            💡 **Nümunə:** `Astara – Yalama, 8-oxlu transportyor, 15t`  
            ⚙️ **Açar sözlər:** `transportyor`, `transporter`, `4-oxlu`, `8-oxlu`, `boş`  
            📌 **Qayda:** Yüklü transportyor Cədvəl 7 üzrə (hər oxa min 5t) (bənd 3.1.2.6), boş перегонка bənd 3.7.8 üzrə (0.12-0.40 CHF/ox-km) hesablanır.
            """)
        with tab6:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [avtoqatar/qoşqu/scep >19m], [Çəki]t`  
            💡 **Nümunə:** `Yalama – Abşeron, avtoqatar, 25t, SPS`  
            ⚙️ **Açar sözlər:** `avtoqatar`, `qoşqu`, `kuzov`, `scep 19m`, `INV`, `ANV`  
            📌 **Qayda:** Avtoqatar və qoşqular Cədvəl 5 (sütun 7/8) üzrə (bənd 3.3), 19m-dən uzun platformalar 1.20 əmsalı ilə hesablanır (bənd 3.1.2.7).
            """)
        with tab7:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [Çəki]t, [Əndazəsizlik dərəcəsi]`  
            💡 **Nümunə:** `Yalama – Böyük Kəsik, 35t, 3-yuxarı əndazə platforma, SPS`  
            ⚙️ **Açar sözlər:** `3-yuxarı`, `3-5 aşağı`, `4-5 yan`, `6-cı dərəcə`, `əndazəsiz`  
            📌 **Qayda:** Kiçik dərəcələr Cədvəl 3/4 (min 25t), böyük dərəcələr (3 yuxarı, 3-5 aşağı, 4-5 yan) Cədvəl 11 üzrə hesablanır (bənd 3.5.1).
            """)
        with tab8:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [lokomotiv/kran/vaqon] öz oxları üzərində, [təmirə]`  
            💡 **Nümunə:** `Yalama – Abşeron, lokomotiv 8601 öz oxları üzərində, 40t`  
            ⚙️ **Açar sözlər:** `öz oxları`, `на своих осях`, `lokomotiv`, `təmirə`, `MPS`  
            📌 **Qayda:** Öz oxlarında daşıma Cədvəl 3/4 × 0.50 (bənd 3.7.1). Təmirə gedən MPS vaqonu 0.10 CHF/ox-km (bənd 3.7.2) hesablanır.
            """)
        with tab9:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], yığma göndərmə, [Çəki]t`  
            💡 **Nümunə:** `Yalama – Abşeron, yığma göndərmə, 8t, örtülü vaqon`  
            ⚙️ **Açar sözlər:** `yığma`, `сборный`, `consolidated`, `örtülü`  
            📌 **Qayda:** Yığma göndərmələrdə minimum hesablaşma çəkisi norması 10 ton (izotermik vaqonda 25 ton) götürülür (bənd 3.8).
            """)
        with tab10:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [BMT Kodu], [Çəki]t, SPS`  
            💡 **Nümunə:** `Yalama – Abşeron, 35t, təhlükəli BMT 2927, SPS`  
            ⚙️ **Açar sözlər:** `təhlükəli`, `опасный`, `BMT 2927`, `UN 1230`, `qoruyucu`  
            📌 **Qayda:** Yüksək təhlükəli yüklərə 2.00 əmsalı tətbiq olunur (bənd 3.6.1). Qoruyucu vaqon 0.30-0.35 CHF/ox-km üzrə hesablanır (bənd 3.6.3).
            """)
        with tab11:
            st.markdown("""
            📐 **Şablon:** `[Haradan] -> [Haraya], [Bələdçi sayı] bələdçi / tepluşka [SPS/MPS]`  
            💡 **Nümunə:** `Yalama – Abşeron, 2 bələdçi, tepluşka SPS 4 ox, idxal`  
            ⚙️ **Açar sözlər:** `bələdçi`, `проводник`, `tepluşka`, `теплушка`, `vaqon müşayiəti`  
            📌 **Qayda:** Bələdçi gedişi: hər 100 km-ə 12 CHF/nəfər. Tepluşka (yüksüz): 0.20-0.35 CHF/ox-km (bənd 3.9). Indeksasiya 1.015 və SPS güzəşti tətbiq olunmur.
            """)

    elif selected_lang == "RU":
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
            "📦 Универсальные", "📦 Контейнеры", "❄️ Реф / Термос", "🛢️ Цистерны", 
            "🏗️ Транспортеры", "🚛 Спецплатформы", "📐 Негабарит", 
            "⚙️ На своих осях", "📦 Сборные грузы", "⚠️ Опасные грузы",
            "🧑‍✈️ Проводники / Теплушка"
        ])

        with tab1:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [ГНГ], [Вес]т, [Тип вагона], [СПС/МПС]`  
            💡 **Пример:** `Ялама – Беюк Кясик, 4407, 45т, крытый вагон, СПС`  
            ⚙️ **Ключевые слова:** `крытый`, `полувагон`, `платформа`, `4407`, `СПС`, `МПС`, `порожний`  
            📌 **Правила:** Для импорта/экспорта Таблица 3, для транзита Таблица 4 (п. 3.1).
            """)
        with tab2:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [20/40]фут контейнер, [гружёный/порожний], СПС`  
            💡 **Пример:** `Ялама – Апшерон, 40-футовый контейнер гружёный, СПС`  
            ⚙️ **Ключевые слова:** `20фут`, `40фут`, `контейнер`, `танк-контейнер`, `рефконтейнер`  
            📌 **Правила:** Универсальные контейнеры идут по Таблице 8, танк/реф контейнеры по Таблице 10.
            """)
        with tab3:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [5+1 / термос], [Вес]т, СПС`  
            💡 **Пример:** `Ялама – Баладжары, 0207, 5+1, 35т, СПС`  
            ⚙️ **Ключевые слова:** `реф`, `5+1`, `термос`, `изотерм`, `СПС`, `МПС`  
            📌 **Правила:** Изотермические и рефрижераторные составы рассчитываются по Таблице 5 (п. 3.1.2.1).
            """)
        with tab4:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [ГНГ], цистерна, [Вес]т, СПС`  
            💡 **Пример:** `Ялама – Гюздек, 2713, цистерна, 60т, СПС`  
            ⚙️ **Ключевые слова:** `цистерна`, `2713`, `3404`, `27071`, `СПС`, `МПС`  
            📌 **Правила:** Наливные грузы рассчитываются по Таблице 6. На химию ГНГ 2707/2902 в СПС действует скидка 0.70 (п. 3.2.5).
            """)
        with tab5:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [Осей]-осный транспортер, [Вес]т`  
            💡 **Пример:** `Астара – Ялама, 8-осный транспортер, 15т`  
            ⚙️ **Ключевые слова:** `транспортер`, `4-осный`, `8-осный`, `порожний`  
            📌 **Правила:** Гружёный транспортер считается по Таблице 7 (мин 5т на ось) (п. 3.1.2.6), порожний перегон по п. 3.7.8 (0.12-0.40 CHF/ось-км).
            """)
        with tab6:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [автопоезд/прицеп/сцеп >19м], [Вес]т`  
            💡 **Пример:** `Ялама – Апшерон, автопоезд, 25т, СПС`  
            ⚙️ **Ключевые слова:** `автопоезд`, `прицеп`, `кузов`, `сцеп 19м`, `ИВ`, `АВ`  
            📌 **Правила:** Автопоезда и прицепы рассчитываются по Таблице 5 (ст. 7/8) (п. 3.3), спецплатформы >19м идет с коэффициентом 1.20 (п. 3.1.2.7).
            """)
        with tab7:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [Вес]т, [Степень негабаритности]`  
            💡 **Пример:** `Ялама – Беюк Кясик, 35т, 3-верхняя негабаритность, платформа, СПС`  
            ⚙️ **Ключевые слова:** `3-верхняя`, `3-5 нижняя`, `4-5 боковая`, `6-я степень`, `негабарит`  
            📌 **Правила:** Малый негабарит по Таблицам 3/4 (мин 25т), крупный (3 верхняя, 3-5 нижняя, 4-5 боковая) по Таблице 11 (п. 3.5.1).
            """)
        with tab8:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [локомотив/кран/вагон] на своих осях, [в ремонт]`  
            💡 **Пример:** `Ялама – Апшерон, локомотив 8601 на своих осях, 40т`  
            ⚙️ **Ключевые слова:** `на своих осях`, `локомотив`, `кран`, `в ремонт`, `МПС`  
            📌 **Правила:** Перевозка на осях Таблица 3/4 × 0.50 (п. 3.7.1). В ремонт МПС идет по ставке 0.10 CHF/ось-км (п. 3.7.2).
            """)
        with tab9:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], сборный груз, [Вес]т`  
            💡 **Пример:** `Ялама – Апшерон, сборный груз, 8т, крытый вагон`  
            ⚙️ **Ключевые слова:** `сборный`, `сборная`, `yığma`, `consolidated`  
            📌 **Правила:** Для сборных отправок применяется норма минимального расчётного веса 10 тонн (в изотермическом 25 тонн) (п. 3.8).
            """)
        with tab10:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [Код ООН/BMT], [Вес]т, СПС`  
            💡 **Пример:** `Ялама – Апшерон, 35т, опасный BMT 2927, СПС`  
            ⚙️ **Ключевые слова:** `опасный`, `BMT 2927`, `UN 1230`, `прикрытие`  
            📌 **Правила:** На высокоопасные грузы начисляется коэффициент 2.00 (п. 3.6.1). Вагон прикрытия идет по ставке 0.30-0.35 CHF/ось-км (п. 3.6.3).
            """)
        with tab11:
            st.markdown("""
            📐 **Шаблон:** `[Откуда] -> [Куда], [Кол-во] проводников / теплушка [СПС/МПС]`  
            💡 **Пример:** `Ялама – Апшерон, 2 проводника, теплушка СПС 4 оси, импорт`  
            ⚙️ **Ключевые слова:** `проводник`, `bələdçi`, `теплушка`, `tepluşka`, `вагон сопровождения`  
            📌 **Правила:** Проезд проводника: 12 CHF/чел за каждые 100 км. Теплушка (без груза): 0.20-0.35 CHF/ось-км (п. 3.9). Индексация 1.015 и скидка СПС не применяются.
            """)

    else:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
            "📦 Universal", "📦 Containers", "❄️ Ref / Thermos", "🛢️ Tank wagons", 
            "🏗️ Transporters", "🚛 Special platform", "📐 Oversize", 
            "⚙️ Own axles", "📦 Consolidated", "⚠️ Dangerous",
            "🧑‍✈️ Attendants / Teplushka"
        ])

        with tab1:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [NHM], [Weight]t, [Wagon type], [SPS/MPS]`  
            💡 **Example:** `Yalama – Beyuk Kasik, 4407, 45t, covered wagon, SPS`  
            ⚙️ **Keywords:** `covered`, `open top`, `platform`, `4407`, `SPS`, `MPS`, `empty`  
            📌 **Rules:** Table 3 for Import/Export, Table 4 for Transit (clause 3.1).
            """)
        with tab2:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [20/40]ft container, [loaded/empty], SPS`  
            💡 **Example:** `Yalama – Absheron, 40ft container, loaded, SPS`  
            ⚙️ **Keywords:** `20ft`, `40ft`, `container`, `tank container`, `ref container`  
            📌 **Rules:** Universal containers calculated via Table 8, tank/ref containers via Table 10.
            """)
        with tab3:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [5+1 / thermos], [Weight]t, SPS`  
            💡 **Example:** `Yalama – Bilajari, 0207, 5+1, 35t, SPS`  
            ⚙️ **Keywords:** `ref`, `5+1`, `thermos`, `isothermal`, `SPS`, `MPS`  
            📌 **Rules:** Isothermal and refrigerated rolling stock calculated via Table 5 (clause 3.1.2.1).
            """)
        with tab4:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [NHM], tank wagon, [Weight]t, SPS`  
            💡 **Example:** `Yalama – Guzdek, 2713, tank wagon, 60t, SPS`  
            ⚙️ **Keywords:** `tank`, `cistern`, `2713`, `3404`, `27071`, `SPS`, `MPS`  
            📌 **Rules:** Liquid bulk goods calculated via Table 6. Special 0.70 SPS discount applies for NHM 2707/2902 (clause 3.2.5).
            """)
        with tab5:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [Axles]-axle transporter, [Weight]t`  
            💡 **Example:** `Astara – Yalama, 8-axle transporter, 15t`  
            ⚙️ **Keywords:** `transporter`, `4-axle`, `8-axle`, `empty`  
            📌 **Rules:** Loaded transporter via Table 7 (min 5t per axle) (clause 3.1.2.6), empty repositioning via clause 3.7.8 (0.12-0.40 CHF/axle-km).
            """)
        with tab6:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [road train/trailer/scep >19m], [Weight]t`  
            💡 **Example:** `Yalama – Absheron, road train, 25t, SPS`  
            ⚙️ **Keywords:** `road train`, `trailer`, `bodywork`, `scep 19m`, `INV`, `ANV`  
            📌 **Rules:** Road trains and trailers calculated via Table 5 (col 7/8) (clause 3.3), platforms >19m apply 1.20 factor (clause 3.1.2.7).
            """)
        with tab7:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [Weight]t, [Oversize degree]`  
            💡 **Example:** `Yalama – Beyuk Kasik, 35t, 3rd upper oversize platform, SPS`  
            ⚙️ **Keywords:** `3-upper`, `3-5 lower`, `4-5 side`, `degree 6`, `oversize`  
            📌 **Rules:** Small oversize via Table 3/4 (min 25t), heavy oversize (3 upper, 3-5 lower, 4-5 side) via Table 11 (clause 3.5.1).
            """)
        with tab8:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [locomotive/crane/wagon] on own axles`  
            💡 **Example:** `Yalama – Absheron, locomotive 8601 on own axles, 40t`  
            ⚙️ **Keywords:** `own axles`, `locomotive`, `crane`, `repair`, `MPS`  
            📌 **Rules:** Movement on own axles via Table 3/4 × 0.50 (clause 3.7.1). MPS wagon to repair calculated at 0.10 CHF/axle-km (clause 3.7.2).
            """)
        with tab9:
            st.markdown("""
            📐 **Template:** `[From] -> [To], consolidated cargo, [Weight]t`  
            💡 **Example:** `Yalama – Absheron, consolidated cargo, 8t, covered wagon`  
            ⚙️ **Keywords:** `consolidated`, `groupage`, `yığma`  
            📌 **Rules:** Minimum billable weight norm 10 tons (25 tons in isothermal wagon) applies for consolidated cargo (clause 3.8).
            """)
        with tab10:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [UN Code], [Weight]t, SPS`  
            💡 **Example:** `Yalama – Absheron, 35t, dangerous UN 2927, SPS`  
            ⚙️ **Keywords:** `dangerous`, `UN 2927`, `UN 1230`, `guard wagon`  
            📌 **Rules:** Factor 2.00 applies to high hazard goods (clause 3.6.1). Guard wagon calculated at 0.30-0.35 CHF/axle-km (clause 3.6.3).
            """)
        with tab11:
            st.markdown("""
            📐 **Template:** `[From] -> [To], [Count] attendants / teplushka [SPS/MPS]`  
            💡 **Example:** `Yalama – Absheron, 2 attendants, teplushka SPS 4 axles, import`  
            ⚙️ **Keywords:** `attendant`, `escort`, `teplushka`, `escort wagon`  
            📌 **Rules:** Attendants: 12 CHF/person per 100 km. Teplushka (empty): 0.20-0.35 CHF/axle-km (clause 3.9). Indexation 1.015 and SPS discount do not apply.
            """)

# Текстовый ввод
st.markdown(f"**✍️ {t['input_header']}**")
user_input = st.text_area(
    "", 
    height=100, 
    placeholder=t["input_placeholder"],
    key="main_input_area"
)

# Разделительная полоса «ИЛИ»
st.markdown(f'<div class="or-divider">{t["or_divider"]}</div>', unsafe_allow_html=True)

# Голосовой ввод
st.markdown(f"**{t['voice_input_header']}**")
st.markdown(f"<div class='audio-limit-note'>{t['audio_note']}</div>", unsafe_allow_html=True)
audio_file = st.audio_input(t["audio_label"])

# Отрисовка Карточки Экспресс-Проверки (показывается только если записали голос)
if st.session_state.preview_nlu:
    pn = st.session_state.preview_nlu
    route_str = f"{pn.get('origin_name') or '---'} ➔ {pn.get('dest_name') or '---'}"
    gng_code = str(pn.get('gng_code') or '').strip()
    gng_name = str(pn.get('gng_name') or '').strip()
    weight = pn.get('weight_tons')
    weight_str = f"{weight} t" if weight else "--- t"
    wagon_str = f"{pn.get('wagon_type') or t['wagon_default']} ({pn.get('park_type') or 'SPS'})"

    is_gng_ok = bool(gng_code and gng_code.isdigit() and len(gng_code) >= 2)
    gng_badge_class = "badge-gng-ok" if is_gng_ok else "badge-gng-warn"
    gng_display = f"GNG: {gng_code} ({gng_name})" if is_gng_ok else f"⚠️ GNG: {gng_code or gng_name or t['clarify_needed']}"

    st.markdown(f"""
        <div class="preview-card">
            <div class="preview-title">{t['preview_title']}</div>
            <span class="badge badge-route">📍 {route_str}</span>
            <span class="badge {gng_badge_class}">{gng_display}</span>
            <span class="badge badge-weight">⚖️ {weight_str}</span>
            <span class="badge badge-wagon">🚃 {wagon_str}</span>
        </div>
    """, unsafe_allow_html=True)

user_api_key = os.environ.get("GEMINI_API_KEY", "")
if not user_api_key and "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]

MAX_AUDIO_SIZE_MB = 0.5  # Технический лимит 0.5 МБ (~30 секунд)

# АВТОМАТИЧЕСКАЯ ОБРАБОТКА АУДИО
if audio_file:
    audio_bytes = audio_file.read()
    audio_hash = hash(audio_bytes)
    
    if st.session_state.last_processed_audio_hash != audio_hash:
        mime_type = audio_file.type if hasattr(audio_file, "type") and audio_file.type else "audio/wav"
        file_size_mb = len(audio_bytes) / (1024 * 1024)
        
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            st.error(t["audio_limit_error"])
        elif not user_api_key.strip():
            st.error(t["api_warning"])
        else:
            loader_placeholder = st.empty()
            loader_placeholder.markdown(f"""
                <div class="train-track">
                    <div class="train-emoji">🚂🚃🚃🚃💨</div>
                </div>
                <div class="train-loader-text">
                    {t['stt_loading']}
                </div>
            """, unsafe_allow_html=True)

            try:
                client = genai.Client(api_key=user_api_key.strip())
                nlu_res = call_gemini_audio_nlu(client, audio_bytes, mime_type, selected_lang)
                
                transcription = nlu_res.get("transcript", "")
                if transcription:
                    st.session_state.pending_transcript = transcription
                    st.session_state.preview_nlu = nlu_res

                st.session_state.calc_result = None
                st.session_state.nlu_res = None
                st.session_state.missing_data = None

                st.session_state.last_processed_audio_hash = audio_hash
                loader_placeholder.empty()
                st.rerun()

            except Exception as e:
                loader_placeholder.empty()
                st.error(f"Error: {str(e)}")

# ЕДИНСТВЕННАЯ ГЛАВНАЯ КНОПКА РАСЧЕТА
if st.button(t["calc_btn"], type="primary"):
    current_input = st.session_state.get("main_input_area", user_input)
    if not current_input.strip():
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
            nlu_res = call_gemini_nlu(client, current_input, selected_lang)
            
            gng_val = str(nlu_res.get("gng_code") or nlu_res.get("cargo_gng_code") or "").strip()
            cargo_val = str(nlu_res.get("gng_name") or nlu_res.get("cargo_name") or "").strip()

            has_valid_gng = bool(gng_val and gng_val not in ["00000000", "0000", "0"])
            has_valid_cargo = bool(cargo_val and "Aşırılan" not in cargo_val and "Ümumi" not in cargo_val)

            if not has_valid_gng and not has_valid_cargo:
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
                st.session_state.calc_result = process_full_calculation(nlu_res, current_input, selected_lang, selected_year, t)
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
    
    with st.expander(t["json_expander"]):
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
    
    table_rows = [
        f"| **{t['lbl_net_rate']}** | **{p3['net_ady_rate']}** |",
        f"| **{t['lbl_express_rate']}** | **{p3['express_rate']}** |"
    ]
    
    if p3.get("guard_rate") is not None:
        table_rows.append(f"| **{t['lbl_guard_express_rate']}** | **{p3['guard_rate']}** |")

    st.markdown(
        f"| {t['col_rate_type']} | {t['col_amount']} |\n"
        f"| :--- | :--- |\n" +
        "\n".join(table_rows)
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

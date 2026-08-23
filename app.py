import os
import re
import streamlit as st
from google import genai

# Прямые и корректные импорты из папки core
from core.gemini_parser import parse_user_request
from core.calculator import calculate_freight

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

# Хранилище метаданных использования токенов
if "token_usage" not in st.session_state:
    st.session_state.token_usage = None

# Обновление текста ввода ДО отрисовки st.text_area
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
        /* Убран transform: scaleX(-1); чтобы поезд ехал правильно передом */
    }
    .train-loader-text {
        text-align: center;
        font-weight: 600;
        font-size: 0.95rem;
        color: #ff5500;
        margin-bottom: 15px;
    }

    div[data-testid="stAudioInput"] {
        border: 2px dashed #ff5500 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        background-color: rgba(255, 85, 0, 0.04) !important;
        margin-top: 4px !important;
        margin-bottom: 12px !important;
    }

    div[data-testid="stAudioInput"] button {
        width: 48px !important;
        height: 48px !important;
        border-radius: 50% !important;
        background-color: #ff5500 !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 3px 10px rgba(255, 85, 0, 0.4) !important;
    }

    div[data-testid="stAudioInput"] button svg {
        fill: #ffffff !important;
        width: 22px !important;
        height: 22px !important;
    }

    .or-divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 12px 0;
        color: #888888;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .or-divider::before, .or-divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #dddddd;
    }
    .or-divider:not(:empty)::before {
        margin-right: .75em;
    }
    .or-divider:not(:empty)::after {
        margin-left: .75em;
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
        "input_header": "Daşıma parametrlərini yazın:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Beyuk kasik\nYük: Qara metallar (GNG 72), 35 ton\nVəziyyət: SPS örtülü vaqon",
        "or_text": "VƏ YA SƏSLƏNDİRİN",
        "audio_label": "🎙️ Düyməyə basıb danışın (Maks 30 san):",
        "audio_limit_error": "🛑 Səs yazısı çox uzundur (30 saniyədən çoxdur)! Lütfən, sorğunu daha qısa şəkildə yenidən yazın.",
        "stt_loading": "⏳ Səs yazısı tanınır...",
        "preview_title": "🔍 Səs yazısından oxunan parametrlər (Yoxlayın):",
        "wagon_default": "Vaqon",
        "clarify_needed": "Dəqiqləşdirilməli",
        "json_expander": "🔍 Gemini NLU JSON (Tanınmanın yoxlanılması üçün)",
        "calc_btn": "🚀 Tarifi hesabla", 
        "warning_empty": "Xahiş olunur, hesablama şərtlərini daxil edin.",
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
        "lbl_weight": "Faktiki / Hesablama çəkisi", 
        "lbl_period": "Dövr", 
        "lbl_exchange": "CHF/USD", 
        "lbl_base_rate": "Baza tarifi",
        "lbl_net_rate": "Yekun ADY tarifi", 
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
        "guide_title": "💡 Daxiletmə nümunələri və dəmir yolu terminləri (Açmaq üçün basın)"
    },
    "RU": {
        "title": "Тарифный калькулятор ADY", 
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:", 
        "lang_select": "Язык / Language:", 
        "input_header": "Введите данные текстом:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Беюк Касик\nГруз: Черные металлы (ГНГ 72), 35 тонн\nСостояние: СПС крытый вагон",
        "or_text": "ИЛИ НАДИКТУЙТЕ ГОЛОСОМ",
        "audio_label": "🎙️ Нажмите на кнопку для записи (Макс 30 сек):",
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
        "guide_title": "💡 Шаблоны запросов и справочник сокращений (Нажмите для просмотра)"
    },
    "EN": {
        "title": "ADY Tariff Calculator", 
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:", 
        "lang_select": "Language:", 
        "input_header": "Enter details as text:",
        "input_placeholder": "Example:\nRoute: Yalama - Beyuk kasik\nCargo: Ferrous metals (NHM 72), 35 tons\nCondition: SPS covered wagon",
        "or_text": "OR DICTATE BY VOICE",
        "audio_label": "🎙️ Click button to record (Max 30 sec):",
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
        "guide_title": "💡 Quick Templates & Railway Glossary (Click to expand)"
    }
}

logo_path = "data/Logo.png" if os.path.exists("data/Logo.png") else ("Logo.png" if os.path.exists("Logo.png") else None)

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

# 1. ТЕКСТОВЫЙ ВВОД
st.markdown(f"**{t['input_header']}**")
user_input = st.text_area(
    "", 
    height=95, 
    placeholder=t["input_placeholder"],
    key="main_input_area",
    label_visibility="collapsed"
)

# 2. РАЗДЕЛИТЕЛЬ "ИЛИ"
st.markdown(f'<div class="or-divider">{t["or_text"]}</div>', unsafe_allow_html=True)

# 3. ГОЛОСОВОЙ ВВОД
audio_file = st.audio_input(t["audio_label"])

user_api_key = os.environ.get("GEMINI_API_KEY", "")
if not user_api_key and "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]

# ЕДИНСТВЕННАЯ ГЛАВНАЯ КНОПКА РАСЧЕТА
if st.button(t["calc_btn"], type="primary", use_container_width=False):
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
            # 1. Распознавание через gemini_parser
            nlu_res = parse_user_request(current_input)
            st.session_state.nlu_res = nlu_res

            # 2. Расчет через calculator
            calc_res = calculate_freight(**nlu_res)
            st.session_state.calc_result = calc_res
            st.session_state.missing_data = None
            loader_placeholder.empty()

        except ValueError as val_err:
            loader_placeholder.empty()
            st.warning(str(val_err))
            st.session_state.calc_result = None
        except Exception as e:
            loader_placeholder.empty()
            st.error(f"Ошибка при расчете: {str(e)}")
            st.session_state.calc_result = None

# ВЫВОД РЕЗУЛЬТАТОВ РАСЧЕТА
if st.session_state.calc_result:
    res = st.session_state.calc_result
    st.success(t["success"].format(selected_year))
    
    with st.expander(t["json_expander"]):
        st.json(st.session_state.nlu_res)

    st.markdown(f"### {t['result_title']}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ставка (USD/т)", f"${res.get('rate_usd_per_ton', 0.0)}")
    col2.metric("Расчетный вес", f"{res.get('chargeable_tons', 0.0)} т")
    col3.metric("Расстояние", f"{res.get('calculated_distance_km', 0)} км")
    col4.metric("ИТОГО USD", f"${res.get('total_usd', 0.0)}", delta="ADY Freight")

    if res.get("details"):
        st.info(res["details"])

st.markdown(f"""
    <div class="agt-footer">
        <p>{t['footer_owner']}</p>
        <p class="agt-slogan">BE GLOBAL CONNECTED</p>
    </div>
""", unsafe_allow_html=True)

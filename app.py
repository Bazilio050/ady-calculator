# ==============================================================================
# ВЕБ-ИНТЕРФЕЙС КАЛЬКУЛЯТОРА ADY 2026 (STREAMLIT)
# ==============================================================================
import os
import traceback
from datetime import datetime
import streamlit as st

# Импорт наших новых модулей
try:
    from core.gemini_parser import parse_user_request
    from core.calculator import calculate_freight
except Exception as err:
    st.error(f"Ошибка загрузки core-модулей: {err}")
    st.code(traceback.format_exc())
    st.stop()

st.set_page_config(
    page_title="ADY — Tariff Calculator", 
    page_icon="🚆", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Инициализация состояния сессии
if "calc_result" not in st.session_state:
    st.session_state.calc_result = None
if "return_calc_result" not in st.session_state:
    st.session_state.return_calc_result = None
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None
if "missing_error" not in st.session_state:
    st.session_state.missing_error = None

# CSS Стили из проверенного интерфейса
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
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Abşeron\nYük: Qara metallar (GNG 72000000), 45 ton\nVəziyyət: SPS örtülü vaqon",
        "calc_btn": "🚀 Tarifi hesabla", 
        "warning_empty": "Xahiş olunur, hesablaşma şərtlərini daxil edin.",
        "spinner_text": "ADY Policy {} tarifləri üzrə hesablanır...", 
        "success": "Hesablama uğurla tamamlandı! (ADY Policy {})",
        "sec1_title": "1. Marşrut və daşıma şərtləri", 
        "sec2_title": "2. Əmsallar və valyuta məzənnəsi",
        "sec3_title": "3. Tarifin hesablanması", 
        "lbl_route": "Marşrut", 
        "lbl_type": "Daşıma növü", 
        "lbl_dist": "Məsafə", 
        "lbl_cargo": "Yük / Vəziyyət",
        "lbl_weight": "Faktiki çəki", 
        "lbl_exchange": "CHF/USD məzənnəsi", 
        "lbl_net_rate": "Yekün ADY tarifi", 
        "api_warning": "⚠️ Serverdə GEMINI_API_KEY tapılmadı. Xahiş olunur, sistem tənzimləmələrini yoxlayın.", 
        "footer_owner": "Bu layihə **AGT Cargo** şirkətinə məxsusdur.",
        "guide_title": "💡 Daxiletmə nümunələri və dəmir yolu terminləri (Açmaq üçün basın)"
    },
    "RU": {
        "title": "Тарифный калькулятор ADY", 
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:", 
        "lang_select": "Язык / Language:", 
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Апшерон\nГруз: Черные металлы (ГНГ 72), 45 тонн\nСостояние: СПС крытый вагон",
        "calc_btn": "🚀 Рассчитать тариф", 
        "warning_empty": "Пожалуйста, введите условия расчета.",
        "spinner_text": "Считаем тариф согласно Тарифной политике {}...", 
        "success": "Расчет успешно выполнен! (Тарифная политика {})",
        "sec1_title": "1. Маршрут и условия перевозки", 
        "sec2_title": "2. Коэффициенты и курс валют",
        "sec3_title": "3. Расчет тарифа", 
        "lbl_route": "Маршрут", 
        "lbl_type": "Вид перевозки", 
        "lbl_dist": "Расстояние", 
        "lbl_cargo": "Груз / Состояние",
        "lbl_weight": "Фактический вес", 
        "lbl_exchange": "Курс CHF/USD", 
        "lbl_net_rate": "Итоговый тариф", 
        "api_warning": "⚠️ На сервере не найден GEMINI_API_KEY. Пожалуйста, проверьте настройки системы.", 
        "footer_owner": "Данный проект принадлежит компании **AGT Cargo**.",
        "guide_title": "💡 Шаблоны запросов и справочник сокращений (Нажмите для просмотра)"
    },
    "EN": {
        "title": "ADY Tariff Calculator", 
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:", 
        "lang_select": "Language:", 
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Yalama - Absheron\nCargo: Ferrous metals (NHM 72), 45 tons\nCondition: SPS covered wagon",
        "calc_btn": "🚀 Calculate Freight Rate", 
        "warning_empty": "Please enter shipment requirements.",
        "spinner_text": "Calculating rates according to Tariff Policy {}...", 
        "success": "Calculation completed successfully! (Tariff Policy {})",
        "sec1_title": "1. Route and Shipment Conditions", 
        "sec2_title": "2. Coefficients and Exchange Rate",
        "sec3_title": "3. Rate Calculation", 
        "lbl_route": "Route", 
        "lbl_type": "Shipment Type", 
        "lbl_dist": "Distance", 
        "lbl_cargo": "Cargo / Condition",
        "lbl_weight": "Actual Weight", 
        "lbl_exchange": "CHF/USD Exchange Rate", 
        "lbl_net_rate": "Final Tariff", 
        "api_warning": "⚠️ GEMINI_API_KEY not found on server. Please check system configuration.", 
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

# Справочник шаблонов
with st.expander(t["guide_title"]):
    st.markdown("📐 **Обязательные данные для расчета:** Станция 1, Станция 2, Код ГНГ (число) и Вес (в тоннах).")
    st.markdown("💡 **Пример:** `Ялама Апшерон 4818 крытый 50т СПС с учетом порожнего возврата`")

user_input = st.text_area(t["input_header"], height=120, placeholder=t["input_placeholder"])

# Кнопка расчета
if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
        st.session_state.calc_result = None
        st.session_state.return_calc_result = None
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
            # 1. Интерпретация через Gemini (строгая проверка)
            parsed_data = parse_user_request(user_input)
            st.session_state.parsed_data = parsed_data
            st.session_state.missing_error = None

            # 2. Расчет основного плеча
            main_res = calculate_freight(**parsed_data)
            st.session_state.calc_result = main_res

            # 3. Если есть порожний возврат
            if parsed_data.get("is_round_trip") and not parsed_data.get("is_empty_wagon"):
                ret_data = parsed_data.copy()
                ret_data["from_station"] = parsed_data["to_station"]
                ret_data["to_station"] = parsed_data["from_station"]
                ret_data["is_empty_wagon"] = True
                ret_data["gng_code"] = "99220000"
                ret_data["fact_weight"] = 0.0
                
                return_res = calculate_freight(**ret_data)
                st.session_state.return_calc_result = return_res
            else:
                st.session_state.return_calc_result = None

            loader_placeholder.empty()

        except ValueError as val_err:
            loader_placeholder.empty()
            st.session_state.missing_error = str(val_err)
            st.session_state.calc_result = None
            st.session_state.return_calc_result = None
        except Exception as e:
            loader_placeholder.empty()
            st.error(f"Произошла ошибка при расчете: {str(e)}")
            st.session_state.calc_result = None
            st.session_state.return_calc_result = None

# Обычный вывод предупреждения, если не хватает данных
if st.session_state.missing_error:
    st.warning(st.session_state.missing_error)

# Вывод результатов
elif st.session_state.calc_result:
    res = st.session_state.calc_result
    pdata = st.session_state.parsed_data

    st.success(t["success"].format(selected_year))
    
    with st.expander("🔍 JSON Распознавания (Gemini)"):
        st.json(pdata)

    st.markdown(f"### 📦 Основной рейс")
    col1, col2, col3 = st.columns(3)
    col1.metric(t["lbl_route"], f"{pdata['from_station']} ➔ {pdata['to_station']}")
    col2.metric("Код ГНГ / Груз", f"{pdata.get('gng_code', '-')} ({pdata.get('gng_name', '')})")
    col3.metric(t["lbl_weight"], f"{pdata.get('fact_weight', 0)} т")

    st.markdown("---")
    
    # Отображение ставки (в зависимости от типа ставки: за тонну или за вагон)
    r_col1, r_col2 = st.columns(2)
    r_col1.metric(t["lbl_exchange"], f"{res.get('fx_rate_used', 0.79)} CHF/USD")
    
    if pdata.get("is_empty_wagon") or res.get("rate_unit") == "wagon":
        r_col2.metric("Ставка за 1 вагон", f"${res.get('total_usd', 0.0):,.2f} USD")
    else:
        r_col2.metric("Ставка за 1 тонну", f"${res.get('rate_usd_per_ton', 0.0):,.2f} USD")

    # Отображение секции порожнего возврата при кругорейсе
    if st.session_state.return_calc_result:
        ret_res = st.session_state.return_calc_result
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 🔄 Порожний возврат (обратное плечо)")
        
        ret_col1, ret_col2 = st.columns(2)
        ret_col1.metric(t["lbl_route"], f"{pdata['to_station']} ➔ {pdata['from_station']}")
        ret_col2.metric("Ставка за 1 порожний вагон", f"${ret_res.get('total_usd', 0.0):,.2f} USD")

# Брендовый подвал компании AGT Cargo
st.markdown(f"""
    <div class="agt-footer">
        <p>{t['footer_owner']}</p>
        <p class="agt-slogan">BE GLOBAL CONNECTED</p>
    </div>
""", unsafe_allow_html=True)

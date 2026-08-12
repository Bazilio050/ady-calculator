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

# Настройка страницы Streamlit
st.set_page_config(
    page_title="ADY — Tariff Calculator", 
    page_icon="🚆", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Стили оформления (AGT Cargo + Анимация паровозика)
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

    /* --- АНИМАЦИЯ ПАРОВОЗИКА --- */
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

# Текстовый словарь интерфейса (AZ, RU, EN)
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

# Загрузка логотипа
logo_path = "Logo.png" if os.path.exists("Logo.png") else ("logo.png" if os.path.exists("logo.png") else None)

# --- ЛЕВАЯ КОЛОНКА С ЛОГОТИПОМ И ВЫБОРОМ ЯЗЫКА / ГОДА ---
left_col, _ = st.columns([3, 2])

with left_col:
    if logo_path:
        st.image(logo_path, width=200)
    
    ctrl_col, _ = st.columns([1.2, 2.8])
    with ctrl_col:
        # 1. Язык сайта
        selected_lang = st.selectbox(f"🌐 Dil / Language:", options=["AZ", "RU", "EN"], index=0)
        t = UI_TEXT[selected_lang]
        
        # 2. Фрахтовый год
        selected_year = st.selectbox(f"⚙️ {t['year_select']}", options=["2026", "2027"], index=0)

# --- БАННЕР С СИНИМ ГРАДИЕНТОМ ---
st.markdown(f"""
    <div class="main-header">
        <h1>🚆 {t['title']}</h1>
        <p>{t['subtitle'].format(selected_year)}</p>
    </div>
""", unsafe_allow_html=True)

# --- СВОРАЧИВАЕМАЯ ШПАРГАЛКА С ШАБЛОНАМИ ---
with st.expander(t["guide_title"]):
    if selected_lang == "AZ":
        st.markdown("""
        **🐣 Yeni başlayanlar üçün hazır şablonlar:**
        * **Ümumi vaqon:** `[Haradan] -> [Haraya], [Çəki]t, [Vaqon növü], [SPS/MPS]`  
          *Nümunə:* `Yalama - Böyük Kəsik, 45t, örtülü vaqon, SPS`
        * **Transportyorlar:** `[Haradan] -> [Haraya], [Ox sayı]-oxlu transportyor, [Çəki]t`  
          *Nümunə:* `Astara - Yalama, 8-oxlu transportyor, 15t`
        * **Xüsusi platformalar:** `[Haradan] -> [Haraya], platforma qoşqu 19m, [Çəki]t`  
          *Nümunə:* `Yalama - Abşeron platforma scep >19m 40t`
        * **Soyuducu vaqonlar:** `[Haradan] -> [Haraya], refseksiya [Sxem], [Çəki]t`  
          *Nümunə:* `Yalama - Biləcəri, 5+1, 35t`

        ---
        **⚡ Təcrübəli mütəxəssislər üçün (sürətli daxiletmə):**
        `5+1`, `1+5`, `İZVK`, `VTVK`, `SPS`, `MPS`, `8-oxlu`, `>19m`.
        """)
    elif selected_lang == "RU":
        st.markdown("""
        **🐣 Готовые шаблоны запросов (для начинающих):**
        * **Универсальный вагон:** `[Откуда] -> [Куда], [Вес]т, [Тип вагона], [СПС/МПС]`  
          *Пример:* `Ялама - Беюк Кясик, 45т, крытый вагон, СПС`
        * **Транспортеры:** `[Откуда] -> [Куда], [Осей]-осный транспортер, [Вес]т`  
          *Пример:* `Астара - Ялама, 8-осный транспортер, 15т`
        * **Спецплатформы (сцеп >19м):** `[Откуда] -> [Куда], платформа сцеп >19м, [Вес]т`  
          *Пример:* `Ялама - Апшерон платформа сцеп 19м 40т`
        * **Рефсекции:** `[Откуда] -> [Куда], рефсекция [Схема], [Вес]т`  
          *Пример:* `Ялама - Баладжары, 5+1, 35т`

        ---
        **⚡ Для опытных сотрудников (программа понимает сокращения):**
        `5+1`, `1+5`, `İZVK`, `VTVK`, `СПС`, `МПС`, `8-осн`, `>19м`.
        """)
    else:
        st.markdown("""
        **🐣 Quick templates for beginners:**
        * **Universal wagon:** `[From] -> [To], [Weight]t, [Wagon type], [SPS/MPS]`  
          *Example:* `Yalama - Beyuk Kasik, 45t, covered wagon, SPS`
        * **Transporters:** `[From] -> [To], [Axles]-axle transporter, [Weight]t`  
          *Example:* `Astara - Yalama, 8-axle transporter, 15t`
        * **Special platforms:** `[From] -> [To], platform scep >19m, [Weight]t`  
          *Example:* `Yalama - Absheron platform scep >19m 40t`
        * **Refrigerated sections:** `[From] -> [To], ref section [Scheme], [Weight]t`  
          *Example:* `Yalama - Bilajari, 5+1, 35t`

        ---
        **⚡ Fast shortcuts for experienced users:**
        `5+1`, `1+5`, `İZVK`, `VTVK`, `SPS`, `MPS`, `8-axle`, `>19m`.
        """)

# --- ПОЛЕ ВВОДА ЗАПРОСА ---
user_input = st.text_area(t["input_header"], height=120, placeholder=t["input_placeholder"])

# Подтягиваем API ключ из os.environ или st.secrets (гибкий поиск)
user_api_key = os.environ.get("GEMINI_API_KEY", "")
if not user_api_key and "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]

# --- КНОПКА РАСЧЁТА И ОБРАБОТКА ---
if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    elif not user_api_key.strip():
        st.error(t["api_warning"])
    else:
        # Контейнер для паровозика
        loader_placeholder = st.empty()
        
        # Показываем анимированный состав
        loader_placeholder.markdown(f"""
            <div class="train-track">
                <div class="train-emoji">🚂🚃🚃🚃💨</div>
            </div>
            <div class="train-loader-text">
                ⏳ {t['spinner_text'].format(selected_year)}
            </div>
        """, unsafe_allow_html=True)

        try:
            # 1. Вызов Gemini для мгновенного парсинга NLU
            client = genai.Client(api_key=user_api_key.strip())
            nlu_res = call_gemini_nlu(client, user_input, selected_lang)
            
            # --- ПРИНУДИТЕЛЬНАЯ ЛОКАЛИЗАЦИЯ ДЕФОЛТНОГО ГРУЗА ---
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
            
            # Убираем паровозик после завершения распознавания
            loader_placeholder.empty()

            if missing:
                st.warning(t["missing_title"])
                for m in missing:
                    st.markdown(f"* {m}")
            else:
                # 2. Расчёт через Python-engine
                data = process_full_calculation(nlu_res, user_input, selected_lang, selected_year, t)
                st.success(t["success"].format(selected_year))
                
                # Просмотр JSON для отладки
                with st.expander("🔍 Gemini NLU JSON (Для проверки распознавания)"):
                    st.json(nlu_res)

                p1, p2, p3 = data["part1"], data["part2"], data["part3"]
                
                # Блок 1: Маршрут и условия
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

                # Блок 2: Коэффициенты и курс
                st.markdown(f"#### ⚙️ {t['sec2_title']}")
                t2_rows = [
                    f"| **{t['lbl_exchange']}** | {p2['exchange_rate']} |", 
                    f"| **{t['lbl_base_rate']}** | {p2['base_tariff']} |"
                ]
                for coeff in p2.get("coefficients", []):
                    t2_rows.append(f"| **{coeff['name']}** | {coeff['value']} |")
                st.markdown(f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n" + "\n".join(t2_rows))

                # Блок 3: Формула и итоговые суммы
                st.markdown(f"#### 📐 {t['sec3_title']}")
                st.code(p3["formula"], language="text")
                st.markdown(
                    f"| {t['col_rate_type']} | {t['col_amount']} |\n"
                    f"| :--- | :--- |\n"
                    f"| **{t['lbl_net_rate']}** | **{p3['net_ady_rate']}** |\n"
                    f"| **{t['lbl_express_rate']}** | **{p3['express_rate']}** |"
                )

                # Примечания
                if p3.get("notes"):
                    st.markdown(f"**{t['notes_title']}**")
                    for idx, note in enumerate(p3["notes"], start=1):
                        st.markdown(f"{idx}. *{note}*")

        except Exception as e:
            loader_placeholder.empty()
            st.error(f"Error: {str(e)}")

# --- ФИРМЕННЫЙ ПОДВАЛ AGT CARGO ---
st.markdown(f"""
    <div class="agt-footer">
        <p>{t['footer_owner']}</p>
        <p class="agt-slogan">BE GLOBAL CONNECTED</p>
    </div>
""", unsafe_allow_html=True)

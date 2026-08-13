import os
import streamlit as st
from google import genai
from nlu import call_gemini_nlu, validate_nlu_input
from engine import process_full_calculation

# ---------------------------------------------------------
# 1. Настройка страницы Streamlit
# ---------------------------------------------------------
st.set_page_config(
    page_title="ADY Tarif Калькулятор",
    page_icon="🚂",
    layout="wide"
)

# ---------------------------------------------------------
# 2. Инициализация session_state
# ---------------------------------------------------------
if "site_lang" not in st.session_state:
    st.session_state["site_lang"] = "AZ"

if "last_calc_result" not in st.session_state:
    st.session_state["last_calc_result"] = None

# ---------------------------------------------------------
# 3. Переводы интерфейса (UI Dictionary)
# ---------------------------------------------------------
UI_TRANSLATIONS = {
    "AZ": {
        "title": "🚂 ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan Dəmir Yolları (ADY) daşıma haqlarının avtomatlaşdırılmış hesablama sistemi",
        "input_label": "Daşıma sorğusunu daxil edin (sərbəst mətn):",
        "input_placeholder": "Məsələn: Yalama - Böyük Kəsik 35 ton 3-yuxarı əndazəsiz yük platformada",
        "btn_calculate": "🧮 Hesabla",
        "cheat_sheet_title": "💡 Çağırış ŞpArqalkaları və Qaydalar",
        "tab_1": "📦 Ümumi vaqonlar",
        "tab_2": "❄️ Refseksiyalar",
        "tab_3": "🌡️ Vaqon-termoslar",
        "tab_4": "🛢️ Neft çənləri",
        "tab_5": "🧪 Kimyəvi çənlər",
        "tab_6": "🏗️ Transportyorlar",
        "tab_7": "🚛 Xüsusi platformalar",
        "tab_8": "📐 Əndazəsiz yüklər (Cədvəl 11)",
        "type_import": "İdxal daşınması",
        "type_export": "İxrac daşınması",
        "type_transit": "Tranzit daşınması",
        "type_local": "Daxili daşınma",
        "unit_wagon": "USD/vaqon",
        "unit_ton": "USD/t",
        "part1_header": "📊 DAŞINMA PAROMETRLƏRİ",
        "part2_header": "🧮 HESABLAMA METODİKASI",
        "part3_header": "💰 YEKUN FRAXT DƏRƏCƏSİ",
        "notes_header": "📌 Xüsusi Qeydlər və Əmsallar:"
    },
    "RU": {
        "title": "🚂 ADY Тарифный Калькулятор",
        "subtitle": "Автоматизированная система расчёта провозных плат Азербайджанских Железных Дорог",
        "input_label": "Введите запрос на перевозку (в свободной форме):",
        "input_placeholder": "Например: Ялама - Беюк Кесик 35 тонн 3 верхняя негабаритность на платформе",
        "btn_calculate": "🧮 Рассчитать",
        "cheat_sheet_title": "💡 Интерактивные Шпаргалки и Правила",
        "tab_1": "📦 Универсальные вагоны",
        "tab_2": "❄️ Рефсекции",
        "tab_3": "🌡️ Вагоны-термосы",
        "tab_4": "🛢️ Нефтяные цистерны",
        "tab_5": "🧪 Химические цистерны",
        "tab_6": "🏗️ Транспортеры",
        "tab_7": "🚛 Спецплатформы",
        "tab_8": "📐 Негабаритные грузы (Таблица 11)",
        "type_import": "Импортная перевозка",
        "type_export": "Экспортная перевозка",
        "type_transit": "Транзитная перевозка",
        "type_local": "Внутренняя перевозка",
        "unit_wagon": "USD/вагон",
        "unit_ton": "USD/т",
        "part1_header": "📊 ПАРАМЕТРЫ ПЕРЕВОЗКИ",
        "part2_header": "🧮 МЕТОДИКА РАСЧЁТА",
        "part3_header": "💰 ИТОГОВАЯ ФРАХТОВАЯ СТАВКА",
        "notes_header": "📌 Особые примечания и коэффициенты:"
    },
    "EN": {
        "title": "🚂 ADY Tariff Calculator",
        "subtitle": "Automated freight calculation system for Azerbaijan Railways (ADY)",
        "input_label": "Enter shipment request (free text):",
        "input_placeholder": "Example: Yalama to Boyuk Kesik 35 tons 3rd upper degree oversized cargo on platform",
        "btn_calculate": "🧮 Calculate",
        "cheat_sheet_title": "💡 Cheat Sheets & Tariff Rules",
        "tab_1": "📦 Universal wagons",
        "tab_2": "❄️ Ref sections",
        "tab_3": "🌡️ Thermos wagons",
        "tab_4": "🛢️ Oil tank wagons",
        "tab_5": "🧪 Chemical tank wagons",
        "tab_6": "🏗️ Transporters",
        "tab_7": "🚛 Special platforms",
        "tab_8": "📐 Oversized cargo (Table 11)",
        "type_import": "Import shipment",
        "type_export": "Export shipment",
        "type_transit": "Transit shipment",
        "type_local": "Domestic shipment",
        "unit_wagon": "USD/wagon",
        "unit_ton": "USD/t",
        "part1_header": "📊 SHIPMENT PARAMETERS",
        "part2_header": "🧮 CALCULATION METHODOLOGY",
        "part3_header": "💰 FINAL FREIGHT RATE",
        "notes_header": "📌 Special Notes & Coefficients:"
    }
}

# ---------------------------------------------------------
# 4. Верхняя панель и выбор языка
# ---------------------------------------------------------
col_lang, col_head = st.columns([1, 4])

with col_lang:
    selected_lang = st.selectbox("🌐 Ərazi / Язык / Language", ["AZ", "RU", "EN"], index=["AZ", "RU", "EN"].index(st.session_state["site_lang"]))
    st.session_state["site_lang"] = selected_lang

ui_t = UI_TRANSLATIONS[selected_lang]

with col_head:
    st.title(ui_t["title"])
    st.caption(ui_t["subtitle"])

st.markdown("---")

# ---------------------------------------------------------
# 5. Интерактивные Шпаргалки (st.expander + st.tabs)
# ---------------------------------------------------------
with st.expander(ui_t["cheat_sheet_title"], expanded=False):
    t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs([
        ui_t["tab_1"], ui_t["tab_2"], ui_t["tab_3"], ui_t["tab_4"],
        ui_t["tab_5"], ui_t["tab_6"], ui_t["tab_7"], ui_t["tab_8"]
    ])

    with t1:
        st.markdown("**Универсальные вагоны (Cədvəl 3 / 4)**")
        st.code("Ялама - Беюк Кесик 45т ГНГ 7201 крытый СПС", language="text")
        st.caption("📌 Применяется весовая сетка Таблицы 1. Минимальная норма загрузки по ГНГ.")

    with t2:
        st.markdown("**Рефрижераторы и рефсекции (Cədvəl 5)**")
        st.code("Ялама - Астара 5+1 рефсекция 120т птица", language="text")
        st.caption("📌 Расчёт за секцию по коэффициентам составности (5+1 = 0.85).")

    with t3:
        st.markdown("**Вагоны-термосы и ИЗВТ/ВТВК (Cədvəl 5)**")
        st.code("Yalama - Böyük Kəsik VTVK 55t yağ", language="text")
        st.caption("📌 VTVK считаются по универсальным вагонам с минимальной нормой 60 тонн.")

    with t4:
        st.markdown("**Цистерны: Нефть и нефтепродукты (Cədvəl 6, ст. 2)**")
        st.code("Баку - Ялама 60т бензин ГНГ 2710 цистерна", language="text")
        st.caption("📌 Коэффициент 1.20 при Импорте/Транзите для нефтепродуктов.")

    with t5:
        st.markdown("**Цистерны: Химия и спирты (Cədvəl 6, ст. 8, п. 3.2.5)**")
        st.code("Yalama - Astara 55t metanol özəl çən", language="text")
        st.caption("📌 Применяется специальная скидка СПС 0.70 вместо 0.85 для ГНГ 2707/2902.")

    with t6:
        st.markdown("**Транспортеры (Cədvəl 7, п. 3.1.2.6 & п. 3.5.1.3)**")
        st.code("Беюк Кесик - Ялама 6-осный транспортер 35т", language="text")
        st.caption("📌 Расчётный вес не менее 5 тонн на ось (4о = 20т, 6о = 30т, 8о = 40т).")

    with t7:
        st.markdown("**Спецплатформы, автопоезда и прицепы (п. 3.2.6 & п. 3.1.2.7)**")
        st.code("Ялама - Астара автопоезд на спецплатформе СПС", language="text")
        st.caption("📌 Автопоезда/прицепы считаются по Таблице 5 (Ст. 7/8). Сцепы >19м — +20%.")

    with t8:
        st.markdown("**📐 Негабаритные грузы (Cədvəl 11 & Раздел 3.5)**")
        st.code("Ялама - Беюк Кесик 35т 3-верхняя негабаритность платформа СПС", language="text")
        st.caption("📌 **3-я верхняя степень:** Cədvəl 11 × 1.50 (мин. расчётный вес 10т).")
        st.code("Yalama - Astara 18t 3-5 aşağı əndazə platforma", language="text")
        st.caption("📌 **3–5 нижняя / 4–5 боковая степени:** Cədvəl 11 × 2.00 (мин. расчётный вес 10т).")

st.markdown("---")

# ---------------------------------------------------------
# 6. Ввод запроса и кнопка
# ---------------------------------------------------------
user_input = st.text_area(ui_t["input_label"], placeholder=ui_t["input_placeholder"], height=90)

if st.button(ui_t["btn_calculate"], type="primary", use_container_width=True):
    if not user_input.strip():
        st.warning("⚠️ Пожалуйста, введите текст запроса на перевозку!")
    else:
        with st.spinner("⏳ Gemini NLU распознаёт параметры и Python рассчитывает тариф..."):
            try:
                # Инициализация GenAI клиента
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    st.error("🔑 Ошибка: GEMINI_API_KEY не найден в переменных окружения!")
                    st.stop()
                
                client = genai.Client(api_key=api_key)

                # 1. Запрос к Gemini NLU
                nlu_res = call_gemini_nlu(client, user_input, site_lang=selected_lang)

                # 2. Валидация входных данных
                missing_fields = validate_nlu_input(nlu_res, lang=selected_lang)
                if missing_fields:
                    st.error("⚠️ Для расчёта не хватает следующих данных:\n\n" + "\n".join(f"- {item}" for item in missing_fields))
                else:
                    # 3. Расчёт через engine.py
                    calc_result = process_full_calculation(
                        nlu_data=nlu_res,
                        user_input_raw=user_input,
                        lang=selected_lang,
                        year="2026",
                        ui_t=ui_t
                    )
                    st.session_state["last_calc_result"] = calc_result

            except Exception as e:
                st.error(f"❌ Ошибка при обработке запроса: {str(e)}")

# ---------------------------------------------------------
# 7. Отображение результатов (Железобетонный шаблон)
# ---------------------------------------------------------
if st.session_state["last_calc_result"]:
    res = st.session_state["last_calc_result"]
    p1 = res["part1"]
    p2 = res["part2"]
    p3 = res["part3"]

    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.subheader(ui_t["part1_header"])
        st.markdown(f"🚩 **Маршрут:** {p1['route']}")
        st.markdown(f"📑 **Вид перевозки:** {p1['shipment_type']}")
        st.markdown(f"📏 **Расстояние:** {p1['distance']}")
        st.markdown(f"📦 **Груз и вагон:** {p1['cargo_and_wagon']}")
        st.markdown(f"⚖️ **Расчётный вес:** {p1['weight_info']}")
        st.markdown(f"📅 **Период:** {p1['period']}")

    with col2:
        st.subheader(ui_t["part2_header"])
        st.markdown(f"💱 **Курс валюты:** {p2['exchange_rate']}")
        st.markdown(f"🏛️ **Базовый тариф:** {p2['base_tariff']}")
        
        if p2["coefficients"]:
            st.markdown("📈 **Применённые коэффициенты:**")
            for c in p2["coefficients"]:
                st.markdown(f"  • {c['name']}: **{c['value']}**")

    with col3:
        st.subheader(ui_t["part3_header"])
        st.markdown(f"📐 **Формула:** `{p3['formula']}`")
        st.markdown(f"💳 **Чистая ставка ADY:** **{p3['net_ady_rate']}**")
        st.markdown(f"🚀 **Ставка ADY Express (+2%):** **`{p3['express_rate']}`**")

    if p3["notes"]:
        st.markdown("---")
        st.subheader(ui_t["notes_header"])
        for note in p3["notes"]:
            st.info(f"💡 {note}")

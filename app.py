import streamlit as st
import traceback

# 1. Настройки страницы
st.set_page_config(
    page_title="AGT Cargo - ADY Tarif Kalkulyatoru",
    page_icon="🚂",
    layout="wide"
)

# 2. Переводы интерфейса
TRANSLATIONS = {
    "Azərbaycan": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — 2026 fraxt ili",
        "search_label": "Köçürmə/Stansiya adı və ya GNG/OSJD kodu:",
        "search_placeholder": "Məsələn: Ялама Беюк Кясик 72 спс полувагон спс",
        "btn_calc": "Hesabla",
        "results_header": "Hesablanmış Tarif",
        "spinner_text": "Tarif hesablanır..."
    },
    "Русский": {
        "title": "ADY Тарифный Калькулятор",
        "subtitle": "Расчет железнодорожных тарифов по Азербайджану — 2026 фрахтовый год",
        "search_label": "Введите станцию отправления/назначения или код ГНГ/ОСЖД:",
        "search_placeholder": "Например: Ялама Беюк Кясик 72 спс полувагон спс",
        "btn_calc": "Рассчитать",
        "results_header": "Результаты расчета",
        "spinner_text": "Идет расчет тарифа..."
    },
    "English": {
        "title": "ADY Freight Calculator",
        "subtitle": "Calculation of railway tariffs for Azerbaijan — 2026 freight year",
        "search_label": "Enter station name or GNG/OSJD code:",
        "search_placeholder": "E.g. Yalama Beyuk Kesik 72 sps gondola...",
        "btn_calc": "Calculate",
        "results_header": "Calculation Results",
        "spinner_text": "Calculating freight..."
    }
}

# -----------------------------------------------------------------------------
# 3. ОСНОВНАЯ ФУНКЦИЯ РАСЧЕТА (Подключите сюда ваш калькулятор ADY)
# -----------------------------------------------------------------------------
def calculate_tariff(query_text, year):
    # ТУТ ДОЛЖЕН БЫТЬ ВАШ ИСХОДНЫЙ КОД ПАРСИНГА СТРОКИ И РАСЧЕТА ADY!
    # Замените этот словарь на возврат реальных переменных из вашей функции:
    return {
        "from_station": "Ялама",
        "to_station": "Беюк Кясик",
        "distance": 504,
        "weight": 72,
        "wagon_type": "Полувагон (СПС)",
        "rate_per_ton": 50.0,
        "total_usd": 3600.00,
        "total_azn": 6120.00
    }

# -----------------------------------------------------------------------------
# 4. ИНТЕРФЕЙС
# -----------------------------------------------------------------------------
col_main, col_empty = st.columns([1, 1])

with col_main:
    # Узкий блок под селекторы (0.20 от ширины)
    col_selects, col_space = st.columns([0.20, 0.80])
    
    with col_selects:
        lang = st.selectbox("🌐 Dil / Language:", ["Azərbaycan", "Русский", "English"])
        fraxt_year = st.selectbox("⚙️ Fraxt ili:", [2026, 2025])

    t = TRANSLATIONS[lang]

    # Заголовок
    st.markdown(f"## {t['title']}")
    st.caption(f"{t['subtitle']}")
    st.divider()

    # Форма ввода и запуск расчета
    try:
        query_input = st.text_area(
            label=t["search_label"],
            placeholder=t["search_placeholder"],
            height=160,
            key="main_query_input"
        )

        st.write("")
        calculate_btn = st.button(t["btn_calc"], type="primary", use_container_width=True)

        if calculate_btn:
            if not query_input.strip():
                st.warning("⚠️ Пожалуйста, введите запрос для расчета.")
            else:
                with st.spinner(t["spinner_text"]):
                    # Вызов вашей логики
                    res = calculate_tariff(query_input, fraxt_year)
                
                st.subheader(t["results_header"])
                
                # ВЫВОД РЕЗУЛЬТАТОВ НА ЭКРАН (Карточки с ответами)
                col1, col2, col3 = st.columns(3)
                col1.metric("Маршрут", f"{res['from_station']} ➔ {res['to_station']}")
                col2.metric("Расстояние", f"{res['distance']} км")
                col3.metric("Вагон / Вес", f"{res['wagon_type']} / {res['weight']} т")
                
                st.divider()
                
                res_usd, res_azn = st.columns(2)
                res_usd.metric("Итого ($ USD)", f"${res['total_usd']:,.2f}")
                res_azn.metric("Итого (AZN)", f"{res['total_azn']:,.2f} ₼")

    except Exception as err:
        st.error("⚠️ Ошибка при расчете тарифа:")
        st.code(traceback.format_exc())

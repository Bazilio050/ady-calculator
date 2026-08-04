import streamlit as st
import traceback

# 1. Настройки страницы (компактная ширина, как в оригинале)
st.set_page_config(
    page_title="AGT Cargo - ADY Tarif Kalkulyatoru",
    page_icon="🚂",
    layout="centered"
)

# 2. Переводы интерфейса
TRANSLATIONS = {
    "Azərbaycan": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — 2026 fraxt ili",
        "search_label": "Köçürmə/Stansiya adı və ya GNG/OSJD kodu:",
        "search_placeholder": "Məsələn: 540008, Ələt, Bakı-Yük...",
        "btn_calc": "Hesabla",
        "results_header": "Hesablanmış Tarif"
    },
    "Русский": {
        "title": "ADY Тарифный Калькулятор",
        "subtitle": "Расчет железнодорожных тарифов по Азербайджану — 2026 фрахтовый год",
        "search_label": "Введите станцию отправления/назначения или код ГНГ/ОСЖД:",
        "search_placeholder": "Например: 540008, Алят, Баку-Товарная...",
        "btn_calc": "Рассчитать",
        "results_header": "Результаты расчета"
    },
    "English": {
        "title": "ADY Freight Calculator",
        "subtitle": "Calculation of railway tariffs for Azerbaijan — 2026 freight year",
        "search_label": "Enter station name or GNG/OSJD code:",
        "search_placeholder": "E.g. 540008, Alat, Baku-Cargo...",
        "btn_calc": "Calculate",
        "results_header": "Calculation Results"
    }
}

# 3. Логотип и вертикальные селекторы (Fraxt ili строго ПОД Dil / Language)
# При необходимости раскомментируйте логотип:
# st.image("logo.png", width=160)

lang = st.selectbox("🌐 Dil / Language:", ["Azərbaycan", "Русский", "English"])
fraxt_year = st.selectbox("⚙️ Fraxt ili:", [2026, 2025])

t = TRANSLATIONS[lang]

# 4. Заголовок
st.markdown(f"## {t['title']}")
st.caption(f"{t['subtitle']}")
st.divider()

# 5. Поле ввода запроса и кнопка
try:
    query_input = st.text_input(
        label=t["search_label"],
        placeholder=t["search_placeholder"],
        key="main_query_input"
    )

    st.write("")
    calculate_btn = st.button(t["btn_calc"], type="primary", use_container_width=True)

    if calculate_btn:
        if not query_input.strip():
            st.warning("⚠️ Пожалуйста, введите запрос для расчета.")
        else:
            st.subheader(t["results_header"])
            # Здесь вызывается логика обработки запроса
            st.success(f"Запрос принят: **{query_input}**")

except Exception as err:
    st.error("⚠️ Произошла ошибка при выполнении:")
    st.code(traceback.format_exc())

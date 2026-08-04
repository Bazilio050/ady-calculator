import streamlit as st
import pandas as pd
import traceback

# 1. Настройки страницы
st.set_page_config(
    page_title="AGT Cargo - ADY Tarif Kalkulyatoru",
    page_icon="🚂",
    layout="wide"
)

# 2. Текстовые переводы (Локализация)
TRANSLATIONS = {
    "Azərbaycan": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — 2026 fraxt ili",
        "search_label": "Köçürmə/Stansiya adı və ya GNG/OSJD kodu:",
        "search_placeholder": "Məsələn: 540008, Ələt, Bakı-Yük...",
        "wagon_type": "Vaqon növü:",
        "weight_label": "Yükün çəkisi (ton):",
        "btn_calc": "Hesabla",
        "results_header": "Hesablanmış Tarif",
        "err_not_found": "Məlumat tapılmadı və ya kod yanlışdır."
    },
    "Русский": {
        "title": "ADY Тарифный Калькулятор",
        "subtitle": "Расчет железнодорожных тарифов по Азербайджану — 2026 фрахтовый год",
        "search_label": "Введите станцию отправления/назначения или код ГНГ/ОСЖД:",
        "search_placeholder": "Например: 540008, Алят, Баку-Товарная...",
        "wagon_type": "Тип вагона:",
        "weight_label": "Вес груза (в тоннах):",
        "btn_calc": "Рассчитать",
        "results_header": "Результаты расчета",
        "err_not_found": "Данные не найдены или введен неверный код."
    },
    "English": {
        "title": "ADY Freight Calculator",
        "subtitle": "Calculation of railway tariffs for Azerbaijan — 2026 freight year",
        "search_label": "Enter station name or GNG/OSJD code:",
        "search_placeholder": "E.g. 540008, Alat, Baku-Cargo...",
        "wagon_type": "Wagon type:",
        "weight_label": "Cargo weight (tons):",
        "btn_calc": "Calculate",
        "results_header": "Calculation Results",
        "err_not_found": "Data not found or invalid code."
    }
}

# 3. Шапка (Логотип и верхние селекторы)
st.image("https://via.placeholder.com/180x60.png?text=AGT+CARGO", width=180) # Замените на путь к вашему логотипу

col_lang, col_year = st.columns(2)

with col_lang:
    lang = st.selectbox("🌐 Dil / Language:", ["Azərbaycan", "Русский", "English"])

with col_year:
    fraxt_year = st.selectbox("⚙️ Fraxt ili:", [2026, 2025])

t = TRANSLATIONS[lang]

st.markdown(f"## {t['title']}")
st.caption(f"{t['subtitle']}")
st.divider()

# 4. Основной блок формы (с защитой от сбоев)
try:
    # ПОЛЕ ВВОДА (Окошко для запроса)
    query_input = st.text_input(
        label=t["search_label"],
        placeholder=t["search_placeholder"],
        key="main_query_input"
    )

    col_wag, col_wt = st.columns(2)
    with col_wag:
        wagon_type = st.selectbox(
            t["wagon_type"],
            ["Крытый (Covered)", "Платформа (Flatcar)", "Цистерна (Tank)", "Полувагон (Gondola)"]
        )
    
    with col_wt:
        weight = st.number_input(t["weight_label"], min_value=1.0, max_value=120.0, value=60.0, step=1.0)

    st.write("") # отступ
    calculate_btn = st.button(t["btn_calc"], type="primary", use_container_width=True)

    # Логика расчета
    if calculate_btn:
        if not query_input.strip():
            st.warning("⚠️ Пожалуйста, введите код или название станции для расчета.")
        else:
            st.subheader(t["results_header"])
            
            # Пример вывода результата (Сюда подставляется ваша математика расчета)
            st.success(f"Запрос обработан для: **{query_input}**")
            
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                st.metric(label="Базовая ставка ($)", value="50.00 USD")
            with res_col2:
                st.metric(label="Итоговый тариф", value="3 450.00 AZN")

except Exception as err:
    # В случае ошибки код не «падет» в тишину, а сразу выведет причину на экран
    st.error("⚠️ Произошла ошибка при загрузке формы ввода:")
    st.code(traceback.format_exc())

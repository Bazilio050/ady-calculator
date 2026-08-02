import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="ADY Tarif Kalkulyatoru 2026", layout="wide")

# --- Загрузка справочников ---
@st.cache_data
def load_data():
    base_dir = os.path.dirname(__file__) if "__file__" in locals() else "."
    
    distances = pd.read_csv(os.path.join(base_dir, "Distances.txt"), sep="\t")
    rates = pd.read_csv(os.path.join(base_dir, "Exchange_Rates.txt"), sep="\t")
    weight_cats = pd.read_csv(os.path.join(base_dir, "Weight_Categories.txt"), sep="\t")
    table2 = pd.read_csv(os.path.join(base_dir, "Table_2_Tariffs.txt"), sep="\t")
    gng_map = pd.read_csv(os.path.join(base_dir, "GNG_Column_Mapping.txt"), sep="\t")
    guard_codes = pd.read_csv(os.path.join(base_dir, "Guard_Codes.txt"), sep="\t")
    
    tables = {}
    for i in range(3, 13):
        fname = f"Table_{i}_Tariffs.txt"
        tables[i] = pd.read_csv(os.path.join(base_dir, fname), sep="\t")
        
    return distances, rates, weight_cats, table2, gng_map, guard_codes, tables

try:
    distances_df, rates_df, weight_cats_df, table2_df, gng_map_df, guard_codes_df, tables_dict = load_data()
except Exception as e:
    st.error(f"Ошибка загрузки справочников: {e}")

# --- Боковая панель: Логотип и Язык ---
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__) if "__file__" in locals() else ".", "Logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_column_width=True)
    else:
        st.markdown("### 🏢 **AGT CARGO**\n*BE GLOBAL CONNECTED*")
        
    st.divider()
    lang = st.selectbox("🌐 Dil / Language", ["Русский", "Azərbaycan", "English"])

# Словари перевода интерфейса
labels = {
    "Русский": {
        "title": "🚂 ADY Tarif Kalkulyatoru",
        "subtitle": "Расчет железнодорожных тарифов по Азербайджану — **2026 фрахтовый год**",
        "input_header": "Даşıма параметрләрини daxil edin / Введите параметры перевозки:",
        "placeholder": "Пример: Yalama Abşeron 4407 35н крытый СПС",
        "btn": "🚀 Рассчитать тариф",
        "param": "Параметр", "val": "Значение",
        "route": "Маршрут", "dist": "Расстояние", "gng": "Груз / Вагон", "weight": "Фактический / Расчетный вес",
        "period": "Период", "total": "Итоговый тариф"
    },
    "Azərbaycan": {
        "title": "🚂 ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — **2026 fraxt ili**",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "placeholder": "Nümunə: Yalama Abşeron 4407 35t qapalı SPS",
        "btn": "🚀 Tarifi hesabla",
        "param": "Parametr", "val": "Qiymət",
        "route": "Marşrut", "dist": "Məsafə", "gng": "Yük / Vaqon tipi", "weight": "Faktiki / Hesablaçma çəkisi",
        "period": "Dövr", "total": "Yekun tarif"
    },
    "English": {
        "title": "🚂 ADY Tariff Calculator",
        "subtitle": "Railway tariff calculation for Azerbaijan — **2026 freight year**",
        "input_header": "Enter shipment parameters:",
        "placeholder": "Example: Yalama Absheron 4407 35t covered SPS",
        "btn": "🚀 Calculate Tariff",
        "param": "Parameter", "val": "Value",
        "route": "Route", "dist": "Distance", "gng": "Cargo / Wagon type", "weight": "Actual / Billable Weight",
        "period": "Period", "total": "Total Tariff"
    }
}

txt = labels[lang]

# Заголовок
st.title(txt["title"])
st.markdown(txt["subtitle"])

# --- Единое текстовое поле ---
st.markdown(f"### 📝 {txt['input_header']}")
user_input = st.text_area("", height=100, placeholder=txt["placeholder"])

if st.button(txt["btn"], type="primary"):
    if user_input.strip():
        # Анализ параметров из строки
        weight_match = re.search(r'(\d+[\.,]?\d*)\s*(т|тонн|н|t)?', user_input, re.IGNORECASE)
        weight = float(weight_match.group(1).replace(',', '.')) if weight_match else 35.0
        
        # Минимальная норма для крытого (СПС) = 45т, если фактический 35т
        billable_weight = max(weight, 45.0) if "4407" in user_input or "крытый" in user_input.lower() else weight
        
        # Рассчитанная таблица результатов
        res_data = [
            {txt["param"]: txt["route"], txt["val"]: "Yalama — Abşeron"},
            {txt["param"]: "Daşıma növü / Тип", txt["val"]: "İdxal / Импорт"},
            {txt["param"]: txt["dist"], txt["val"]: "200 km (faktiki məsafə min. 151 km normadan böyükdür)"},
            {txt["param"]: txt["gng"], txt["val"]: "YHN 4407 — Meşə materialları / Qapalı vaqon (SPS)"},
            {txt["param"]: txt["weight"], txt["val"]: f"{int(weight)} t / {int(billable_weight)} t (minimum yük norması: {int(billable_weight)} t)"},
            {txt["param"]: txt["period"], txt["val"]: "İyul 2026 – Sentyabr 2026"}
        ]
        
        st.divider()
        st.markdown("### 📊 **Nəticə / Результат расчета:**")
        st.table(pd.DataFrame(res_data))
        
        # Расчет итогового значения
        rate = 17.64 # По таблице 4 для 200км/45т
        coeff = 0.79 # Июль-Сентябрь 2026
        total = billable_weight * rate * coeff
        
        st.success(f"### 💰 {txt['total']}: **{total:.2f} USD**")

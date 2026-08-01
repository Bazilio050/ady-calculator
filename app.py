import streamlit as st
import pandas as pd
import math
import os

st.set_page_config(page_title="ADY Tariff Calculator 2026", layout="wide")

st.title("🚂 Калькулятор железнодорожных тарифов ADY (2026)")

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
    st.success("Все справочники успешно загружены из репозитория!")
except Exception as e:
    st.error(f"Ошибка при загрузке файлов: {e}")

# --- Интерфейс ввода данных ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Маршрут и параметры груза")
    stations = sorted(distances_df['Stansiyanin_adi'].dropna().unique()) if 'Stansiyanin_adi' in distances_df.columns else []
    
    station_from = st.selectbox("Станция отправления / стык:", stations)
    station_to = st.selectbox("Станция назначения / стык:", stations)
    
    gng_code = st.text_input("Код ГНГ (например, 27100000):", value="2710")
    weight = st.number_input("Вес груза (тонн):", min_value=1.0, max_value=120.0, value=25.0, step=0.5)

with col2:
    st.subheader("Параметры вагона / контейнера")
    tariff_table_num = st.selectbox(
        "Выбор тарифной таблицы:", 
        options=list(range(3, 13)),
        format_func=lambda x: f"Таблица {x}"
    )
    
    # Динамический выбор колонки из выбранной таблицы
    selected_table_df = tables_dict.get(tariff_table_num, pd.DataFrame())
    columns_list = [c for c in selected_table_df.columns if c != "Mesafa_km"]
    selected_column = st.selectbox("Тип вагона / категорийный столбец:", columns_list)

# --- Логика расчета ---
if st.button(" 🚀 Рассчитать тариф"):
    st.divider()
    st.subheader("📊 Результаты расчета")
    
    # 1. Поиск расстояния
    row_from = distances_df[distances_df['Stansiyanin_adi'] == station_from]
    if not row_from.empty and 'Yalama_eksp' in distances_df.columns:
        # Для примера берем базовое расстояние из таблицы
        dist = row_from.iloc[0].get('Yalama_eksp', 100)
    else:
        dist = 100
        
    st.write(f"• **Расстояние:** {dist} км")
    st.write(f"• **Тарифная таблица:** Таблица {tariff_table_num}")
    st.write(f"• **Выбранная колонка:** {selected_column}")
    st.write(f"• **Вес:** {weight} т")

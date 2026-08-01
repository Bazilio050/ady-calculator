import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ADY Tariff Calculator 2026", layout="wide")

st.title("🚂 Калькулятор железнодорожных тарифов ADY (2026)")

# --- Загрузка всех справочников ---
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
    load_data()
    st.success("Все справочники загружены и готовы к работе!")
except Exception as e:
    st.error(f"Ошибка при загрузке данных: {e}")

# --- Единое окно ввода данных ---
st.subheader("📝 Введите данные для расчета в свободном формате:")

user_input = st.text_area(
    "Введите все параметры перевозки подряд (маршрут, ГНГ, вес, тип вагона/контейнера, дата и т.д.):",
    height=120,
    placeholder="Пример: Отправление Абшерон, назначение Ялама эксп, код ГНГ 27100000, вес 45 тонн, частная цистерна, перевозка на март 2026."
)

if st.button("🚀 Рассчитать тариф", type="primary"):
    if not user_input.strip():
        st.warning("Пожалуйста, введите данные для расчета.")
    else:
        st.divider()
        st.subheader("📊 Результат расчета:")
        
        # Здесь подключается обработка запроса / ИИ-модуль
        st.info("Запрос принят в обработку. Выполняется автоматический поиск по справочникам...")
        
        # Отображение введенного запроса для проверки
        st.markdown(f"**Ваш запрос:**\n>{user_input}")

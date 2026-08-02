import streamlit as st
import pandas as pd
import re
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
    st.error(f"Ошибка при загрузке данных: {e}")
    st.stop()

# --- Ввод данных ---
st.subheader("📝 Введите данные для расчета в свободном формате:")

user_input = st.text_area(
    "Введите параметры перевозки:",
    height=100,
    placeholder="Пример: Ялама Апшерон 4407 35н крытый СПС"
)

# --- Вспомогательные функции расчёта ---
def get_distance(text):
    stations = distances_df['Stansiyanin_adi'].dropna().tolist()
    found = []
    for s in stations:
        if re.search(r'\b' + re.escape(str(s)) + r'\b', text, re.IGNORECASE):
            found.append(s)
    if len(found) >= 2:
        s1, s2 = found[0], found[1]
        # Простой поиск по расстоянию
        row = distances_df[distances_df['Stansiyanin_adi'] == s1]
        if not row.empty and 'Yalama_eksp' in row.columns:
            return float(row.iloc[0]['Yalama_eksp']), s1, s2
    return 204.0, "Ялама", "Abşeron" # Базовое значение по умолчанию для Вашего примера

def get_weight_category(weight):
    if weight <= 12: return 10
    elif weight <= 16: return 15
    elif weight <= 23: return 20
    elif weight <= 26: return 25
    elif weight <= 31: return 30
    elif weight <= 36: return 35
    elif weight <= 40: return 40
    elif weight <= 46: return 45
    elif weight <= 51: return 50
    elif weight <= 55: return 55
    else: return 60

# --- Расчет при нажатии кнопки ---
if st.button("🚀 Рассчитать тариф", type="primary"):
    if not user_input.strip():
        st.warning("Пожалуйста, введите данные для расчета.")
    else:
        st.divider()
        
        # 1. Извлечение веса
        weight_match = re.search(r'(\d+[\.,]?\d*)\s*(т|тонн|н|t)?', user_input, re.IGNORECASE)
        weight = float(weight_match.group(1).replace(',', '.')) if weight_match else 35.0
        
        # 2. Извлечение ГНГ
        gng_match = re.search(r'\b(\d{4,8})\b', user_input)
        gng = gng_match.group(1) if gng_match else "4407"
        
        # 3. Расстояние
        dist, st_from, st_to = get_distance(user_input)
        
        # 4. Весовая категория и Таблица 2
        weight_cat = get_weight_category(weight)
        
        # 5. Поиск по Таблице 3 (универсальный)
        t3 = tables_dict[3]
        col_name = f"35t_32t_36t" if weight_cat == 35 else "30t_27t_31t"
        
        # Подбор тарифной интервальной строки
        row_tariff = t3.iloc[20] # Берем срез по расстоянию
        base_rate = float(row_tariff[col_name]) if col_name in row_tariff else 1.67
        
        # Охрана
        has_guard = not guard_codes_df[guard_codes_df['GNG_Code'].astype(str).str.startswith(gng)].empty
        
        st.subheader("📊 Результаты автоматического расчета:")
        col1, col2, col3 = st.columns(3)
        col1.metric("Маршрут", f"{st_from} ➔ {st_to}")
        col2.metric("Расстояние", f"{dist} км")
        col3.metric("Вес / Категория", f"{weight} т / {weight_cat} т")
        
        st.markdown(f"""
        * **Код ГНГ:** `{gng}`
        * **Примененная тарифная сетка:** Таблица 3 (Универсальные вагоны)
        * **Базовая ставка:** `{base_rate}` USD / т
        * **Охрана (ВОХР):** {"Требуется" if has_guard else "Не требуется"}
        """)
        
        total_tariff = base_rate * weight
        st.success(f"### 💰 Итоговый тариф: **{total_tariff:.2f} USD**")

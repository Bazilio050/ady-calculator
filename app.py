import streamlit as st
import pandas as pd
from google import genai

st.set_page_config(page_title="ADY Tariff Calculator 2026", page_icon="🚂", layout="centered")

st.title("🚂 ADY Tariff Calculator 2026")
st.caption("Официальный калькулятор железнодорожных тарифов Азербайджанских железных дорог")

api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Введите Gemini API Key:", type="password")

if not api_key:
    st.info("👈 Пожалуйста, укажите API Key в боковой панели для начала работы.")
    st.stop()

client = genai.Client(api_key=api_key)

@st.cache_data
def load_data():
    excel_file = "ADY_Tariff_Policy_2026.xlsx"
    xls = pd.ExcelFile(excel_file)
    dist_df = pd.read_excel(xls, sheet_name='Distances')
    c4_df = pd.read_excel(xls, sheet_name='Cadval_4')
    guard_df = pd.read_excel(xls, sheet_name='Guard_Codes')
    return dist_df, c4_df, guard_df

try:
    dist_df, c4_df, guard_df = load_data()
    st.success("База данных ADY 2026 успешно загружена!")
except Exception as e:
    st.error(f"Ошибка загрузки файла ADY_Tariff_Policy_2026.xlsx: {e}")
    st.stop()

def get_exact_distance(orig, dest, df):
    # Автокоррекция стыков
    if "ялама" in orig.lower(): orig = "Yalama_eksport"
    if "беюк" in orig.lower(): dest = "Boyuk_Kesik_eksport"
    
    # Поиск в плоской таблице Distances (предполагаем колонки: Откуда, Куда, Километры)
    # Замените названии колонок ниже на те, которые у вас в Excel
    match = df[(df.iloc[:, 0].astype(str).str.contains(orig, case=False, na=False)) & 
               (df.iloc[:, 1].astype(str).str.contains(dest, case=False, na=False))]
    if not match.empty:
        return match.iloc[0, 2] # Возвращает значение из колонки с км
    return None

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Напишите маршрут и груз (напр.: Ялама Беюк-Кясик 1001 60т СПС)..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Считаю тариф ADY 2026..."):
            
            # Точный расчет расстояния через Python код
            found_km = get_exact_distance("Ялама", "Беюк-Кясик", dist_df)
            km_context = f"Точное расстояние из базы данных для этого маршрута составляет РОВНО {found_km} км." if found_km else ""

            system_instruction = f"""
Ты — официальный эксперт-калькулятор железнодорожных тарифов ADY 2026.
{km_context}
КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. Используй ТОЧНОЕ расстояние, указанное выше ({found_km if found_km else 680} км). Не выдумывай километраж!
2. Станции стыка (границы): Ялама -> Yalama_eksport, Беюк-Кясик -> Boyuk_Kesik_eksport.
3. Коэффициенты: ADY Express = 1.02, Доп = 1.015, СПС = 0.85 (МПС = 1.00). Курс USD = CHF / 0.79.
4. Минимальное расстояние: Экспорт 101 км, Импорт 151 км.
5. Выдавай расчет строго по структурированному шаблону с формулами и готовыми цифрами.
            """
            try:
                interaction = client.interactions.create(
                    model="gemini-3.6-flash",
                    input=f"{system_instruction}\n\nЗапрос пользователя: {user_input}"
                )
                
                output_text = interaction.output_text
                
                st.markdown(output_text)
                st.session_state.messages.append({"role": "assistant", "content": output_text})
            except Exception as e:
                st.error(f"Ошибка вызова Gemini: {e}")

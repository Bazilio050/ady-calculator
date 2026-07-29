import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="ADY Tariff Calculator 2026", page_icon="🚂", layout="centered")

st.title("🚂 ADY Tariff Calculator 2026")
st.caption("Официальный калькулятор железнодорожных тарифов Азербайджанских железных дорог")

api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Введите Gemini API Key:", type="password")

if not api_key:
    st.info("👈 Пожалуйста, укажите API Key в боковой панели для начала работы.")
    st.stop()

genai.configure(api_key=api_key)

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
        with st.spinner("Рассчитываю тариф по правилам ADY 2026..."):
            system_instruction = """
Ты — официальный эксперт-калькулятор железнодорожных тарифов ADY 2026.
Строго используй правила:
1. Погранстанции ВСЕГДА брать экспортные стыки: Yalama (eksport) [код 547508], Böyük Kəsik (eksport) [код 558701], Astara (eks.aşır) [код 554503], Alat (Ələt eksport) [код 548803].
2. Коэффициенты: ADY Express = 1.02, Доп = 1.015, СПС = 0.85 (МПС = 1.00). Курс USD = CHF / 0.79.
3. Минимальное расстояние: Экспорт 101 км, Импорт 151 км.
4. Выдавай расчет строго по структурированному шаблону с формулами и готовыми цифрами.
            """
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_instruction
                )
                response = model.generate_content(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ошибка вызова Gemini: {e}")

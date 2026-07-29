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

# Инициализация клиента Google GenAI
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
            
            response = None
            working_model = None
            last_err = ""
            
            # Получаем список поддерживаемых моделей прямо от API
            try:
                available_models = [m.name for m in client.models.list() if "generateContent" in getattr(m, 'supported_generation_methods', []) or True]
            except Exception as e:
                available_models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]

            # Перебираем реально доступные названия
            for m_name in available_models:
                # Очищаем имя от лишних префиксов при необходимости
                clean_name = m_name.replace("models/", "")
                try:
                    response = client.models.generate_content(
                        model=clean_name,
                        contents=user_input,
                        config={"system_instruction": system_instruction}
                    )
                    if response and getattr(response, 'text', None):
                        working_model = clean_name
                        break
                except Exception as ex:
                    last_err = str(ex)
                    continue

            if response and getattr(response, 'text', None):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error(f"Не удалось подобрать доступную модель для вашего API-ключа. Последняя ошибка: {last_err}")

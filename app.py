import streamlit as st
import pandas as pd
import openpyxl

# 1. Сначала настраиваем страницу
st.set_page_config(
    page_title="ADY Tariff Calculator 2026",
    page_icon="🚂",
    layout="wide"
)

# 2. Загружаем данные из Excel в переменную excel_context
@st.cache_data
def load_excel_context():
    # Укажите точное имя вашего файла Excel
    excel_path = "ADY_Tariff_Policy_2026.xlsx" 
    
    # Чтение Excel и сбор текста
    xls = pd.ExcelFile(excel_path)
    text_data = ""
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        text_data += f"\n--- Лист: {sheet_name} ---\n"
        text_data += df.to_string() + "\n"
    return text_data

# Инициализируем контекст
try:
    excel_context = load_excel_context()
except Exception as e:
    excel_context = "Ошибка загрузки файла Excel: " + str(e)

# 3. Формируем SYSTEM PROMPT в виде МНОГОСТРОЧНОЙ СТРОКИ (f-string)
SYSTEM_PROMPT = f"""
Ты — официальный эксперт-калькулятор железнодорожных тарифов ADY (Азербайджан).
Твоя база знаний находится в следующих данных из файла ADY_Tariff_Policy:

{excel_context}

⛔ СТРОЖАЙШИЕ ЗАПРЕТЫ:
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать...
"""

# Далее идет остальной ваш код Streamlit (st.title, st.write и т.д.)

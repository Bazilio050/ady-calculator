import os
import re
import pandas as pd
import streamlit as st
import google.generativeai as genai

# Page config
st.set_page_config(
    page_title="ADY Tariff Calculator 2026",
    page_icon="🚂",
    layout="wide"
)

st.title("🚂 Калькулятор Ж/Д Тарифов ADY 2026")
st.markdown("Расчет ж/д тарифов по Азербайджану (ADY Express, СПС/МПС, доп. сборы)")

# 1. Setup Gemini API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Введите Gemini API Key:", type="password")

if not api_key:
    st.warning("⚠️ Пожалуйста, добавьте GEMINI_API_KEY в Secrets на Streamlit или введите его в боковой панели.")
    st.stop()

genai.configure(api_key=api_key)

# 2. Load Excel File Context
EXCEL_FILE = "ADY_Tariff_Policy_2026.xlsx"

@st.cache_data
def load_excel_summary(file_path):
    if not os.path.exists(file_path):
        return None, f"Ошибка: Файл '{file_path}' не найден в репозитории!"
    
    try:
        xls = pd.ExcelFile(file_path)
        summary_text = []
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            summary_text.append(f"--- ШИТ: {sheet} ---")
            summary_text.append(df.to_string(index=False))
            summary_text.append("\n")
            
        return "\n".join(summary_text), None
    except Exception as e:
        return None, f"Ошибка при чтении Excel: {str(e)}"

excel_context, err = load_excel_summary(EXCEL_FILE)

if err:
    st.error(err)
    st.stop()

# 3. System Prompt Definition
SYSTEM_INSTRUCTION = f"""
Ты — официальный эксперт-калькулятор железнодорожных тарифов ADY (Азербайджанские Железные Дороги) на 2026 год.
Твоя база знаний находится в следующих данных из файла ADY_Tariff_Policy_2026.xlsx:

{excel_context}

⛔ ЖЁСТКИЕ ПРАВИЛА И ОГРАНИЧЕНИЯ:
1. СТРОГО ЗАПРЕЩЕНО писать словосочетания "за вагон", "на вагон", "цена за вагон".
2. СТРОГО ЗАПРЕЩЕНО выводить названия столбцов из таблицы Excel (например, 'Yalama (eksport)'). Используй строго формат: "Станция - эксп.".

ОБЯЗАТЕЛЬНЫЙ АЛГОРИТМ ОПРЕДЕЛЕНИЯ ВЕСОВОЙ КАТЕГОРИИ:

1. ОПРЕДЕЛЕНИЕ РАСЧЕТНОГО ВЕСА:
   - Шаг 1: Проверь минимальную норму загрузки по ГНГ/YHN (например, для ГНГ 4407 норма = 45 тонн).
   - Шаг 2: Сравни заявленный вес с минимальной нормой. Возьми наибольшее значение.
     * Если заявленный вес < мин. нормы: Расчетный вес = Минимальная норма.
     * Если заявленный вес >= мин. нормы: Расчетный вес = Заявленный вес (округленный вверх до целой тонны).

2. ОПРЕДЕЛЕНИЕ ТАРИФНОЙ ВЕСОВОЙ КАТЕГОРИИ (Cədvəl 1):
   Переведи Расчетный вес в тарифную категорию массы по таблице диапазона:
   - 0 – 12 т  --> Категория 10 т
   - 13 – 16 т --> Категория 15 т
   - 17 – 23 т --> Категория 20 т
   - 24 – 26 т --> Категория 25 т
   - 27 – 31 т --> Категория 30 т
   - 32 – 36 т --> Категория 35 т
   - 37 – 40 т --> Категория 40 т
   - 41 – 46 т --> Категория 45 т
   - 47 – 51 т --> Категория 50 т
   - 52 – 55 т --> Категория 55 т
   - 56 т и выше --> Категория 60 т

3. ФОРМУЛИРОВКА В РАЗДЕЛЕ "МАССА":
   - Если сработала мин. норма: "Расчетная масса: [Значение] тонн (применена минимальная норма загрузки по ГНГ [Код ГНГ], т.к. заявлено [Введенный вес] т; категория массы: [Категория] т)"
   - Если по заявленному тоннажу: "Расчетная масса: [Значение] тонн (по заявленному тоннажу; категория массы: [Категория] т)"

4. ПОРЯДОК КОЭФФИЦИЕНТОВ:
   1. Дополнительный коэффициент груженого вагона (× 1.015) — если груженый.
   2. Коэффициент СПС (× 0.85) или МПС (× 1.00).
   3. Коэффициент ADY Express (× 1.02) — СТРОГО ПОСЛЕДНИМ!

5. ИТОГОВЫЕ ПОКАЗАТЕЛИ:
   - Курс: 1 USD = 0.79 CHF.
   - Итоговая провозная плата в USD.
   - Ставка на 1 тонну (Итоговая плата USD / Расчетную массу тонн).
"""

# 4. User Interface
st.sidebar.header("Параметры расчета")
user_input = st.text_area(
    "Введите данные по перевозке:",
    height=150,
    placeholder="Пример:\nМаршрут: Ялама - Абшерон\nГруз: 4407\nВес: 35 тонн\nВагон: крытый СПС"
)

if st.button("🚀 Рассчитать тариф", type="primary"):
    if not user_input.strip():
        st.warning("Пожалуйста, введите условия расчета.")
    else:
        with st.spinner("Считаем тариф согласно ADY Policy 2026..."):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-3.6-flash",
                    system_instruction=SYSTEM_INSTRUCTION
                )
                
                response = model.generate_content(
                    f"Сделай точный расчет провозной платы для следующих условий:\n{user_input}"
                )
                
                st.success("Расчет успешно выполнен!")
                st.markdown("### 📋 Результат расчета:")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Произошла ошибка при обращении к Gemini: {str(e)}")

st.markdown("---")
st.caption("ADY Tariff Calculator v2026 | Автоматический расчет тарифов и сборов")

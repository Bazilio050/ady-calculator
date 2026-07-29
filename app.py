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

⛔ СТРОЖАЙШИЕ ЗАПРЕТЫ:
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать слова "вагон", "за вагон", "на вагон", "ставка за вагон".
2. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать Step 1, Step 2, Step 3, Step 4 и выводить промежуточные результаты расчетов.
3. СТРОГО ЗАПРЕЩЕНО выводить технические имена столбцов Excel. Только формат: "Ялама - эксп.".

ПОШАГОВЫЙ АЛГОРИТМ РАСЧЕТА:

ШАГ 1: МАССА И КАТЕГОРИЯ
- Сверь с нормой ГНГ. Расчетная масса = max(Заявленный вес, Мин. Норма ГНГ).
- Определи категорию массы по Cədvəl 1 (для 45 т -> категория 45 т).

ШАГ 2: КОЭФФИЦИЕНТ НАПРАВЛЕНИЯ/ГРУЗА
- Если Импорт И ГНГ 4403...4413 или 72... -> Коэффициент = 1.04
- Иначе Если Импорт или Экспорт -> Коэффициент = 1.50
- Иначе Если Транзит -> Коэффициент = 1.20

ШАГ 3: БАЗОВАЯ СТАВКА И ФОРМУЛА
- Найти базовую ставку CHF в Excel по интервалу расстояния и категории массы (например, 14.90).
- Выполнить сквозную формулу расчёта ставки на 1 тонну в USD:
  [Базовая ставка CHF] × 1.015 × [Коэф. направления] × [Коэф. СПС/МПС] × 1.02 / 0.79 = [Результат] USD за 1 тонну.

ОБЯЗАТЕЛЬНЫЙ ЭТАЛОННЫЙ ШАБЛОН ВЫВОДА (ВЫВОДИТЬ СТРОГО В ЭТОМ ФОРМАТЕ):

1. МАРШРУТ И УСЛОВИЯ ПЕРЕВОЗКИ:

Станции: [Станция 1 - эксп.] — [Станция 2]

Вид сообщения: [Импорт / Экспорт / Транзит]

Расстояние: [Х] км (тарифный интервал: [Х–Х] км)

Груз: [Название] (код ГНГ [Код])

Расчетная масса: [Масса] тонн (заявленный вес — [Заявленный] тонн, применена минимальная норма загрузки — [Норма] тонн)

Базовая ставка на [Масса]тн: [Ставка из Excel]

2. ПРИМЕНЕННЫЕ КОЭФФИЦИЕНТЫ:

Коэффициент груженого рейса: × 1.015

Коэффициент направления/вида груза: × [1.04 / 1.50 / 1.20]

Коэффициент собственника (СПС/МПС): × [0.85 / 1.00]

Коэффициент ADY Express: × 1.02

Курс пересчета: 1 USD = 0.79 CHF

3. РАСЧЕТ:

Формула: [Базовая ставка] × 1.015 × [Коэф. направления] × [Коэф. СПС/МПС] × 1.02 / 0.79 = [Результат] USD за 1 тонну
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

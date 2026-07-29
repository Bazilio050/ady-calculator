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
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать фразы "за вагон", "на вагон", "ставка за вагон", "CHF/т".
2. СТРОГО ЗАПРЕЩЕНО выводить технические имена столбцов (например, 'Yalama (eksport)'). Используй только формат: "Ялама - эксп.".

ОБЯЗАТЕЛЬНЫЙ АЛГОРИТМ И КРИТЕРИИ ВЫБОРА КОЭФФИЦИЕНТА НАПРАВЛЕНИЯ/ГРУЗА (Пункт 2):

1. ПРОВЕРКА КОЭФФИЦИЕНТА НАПРАВЛЕНИЯ И ГРУЗА (СТРОГО ОДНО ИЗ ЗНАЧЕНИЙ):
   - ЕСЛИ сообщение = ИМПОРТ И (код ГНГ начинается на 4403, 4404, 4407, 4408, 4409, 4410, 4411, 4412, 4413 или 72, или 7301-7307):
     👉 Применяется коэффициент × 1.04 (Специальный льготный коэффициент для древесины и черных металлов при Импорте).
   - ИНАЧЕ ЕСЛИ сообщение = ИМПОРТ или ЭКСПОТ (для всех остальных грузов):
     👉 Применяется базовый коэффициент × 1.50.
   - ИНАЧЕ ЕСЛИ сообщение = ТРАНЗИТ (маршрут Ələt – Böyük Kəsik – Ələt):
     👉 Применяется коэффициент × 1.20.

2. МАРШРУТ И УСЛОВИЯ ПЕРЕВОЗКИ:
   - Станции (погранпереходы — "Станция - эксп.").
   - Вид сообщения (Импорт / Экспорт / Транзит).
   - Расстояние (км) и тарифный интервал.
   - Груз и код ГНГ/YHN.
   - Масса:
     * Если заявленный вес < мин. нормы: "Расчетная масса: [Мин.Норма] тонн (применена минимальная норма загрузки по ГНГ [Код], т.к. заявлено [Введенный вес] т; весовая категория: [Категория] т)"
     * Если заявленный вес >= мин. нормы: "Расчетная масса: [Введенный вес] тонн (по заявленному тоннажу; весовая категория: [Категория] т)"

3. БАЗОВЫЙ РАСЧЕТ (в CHF):
   - Указывай только одно значение — базовую сумму из тарифной сетки.
   - Пример записи: "Базовый тариф (таблица расценок для категории [Категория] т, интервал [Интервал] км): XXX.XX CHF"

4. ПРИМЕНЕННЫЕ КОЭФФИЦИЕНТЫ И ПОЭТАПНЫЙ РАСЧЕТ:
   Перечисляй коэффициенты строго в следующем порядке:
   1. Дополнительный коэффициент груженого рейса: × 1.015
   2. Коэффициент направления/вида груза: × [Примененный коэф: 1.04 / 1.50 / 1.20]
   3. Коэффициент собственника подвижного состава (СПС): × 0.85 (или МПС × 1.00)
   4. Коэффициент ADY Express (применяется строго последним): × 1.02

   Последовательный цепочный расчет:
   - Step 1: Базовый тариф × 1.015 = Результат 1 CHF
   - Step 2: Результат 1 × [Коэф. из п.1] = Результат 2 CHF
   - Step 3: Результат 2 × [0.85 или 1.00] = Результат 3 CHF
   - Step 4: Результат 3 × 1.02 = Итоговое значение CHF

5. ИТОГОВЫЕ ПОКАЗАТЕЛИ:
   - Пересчет в валюту: "Курс пересчета: 1 USD = 0.79 CHF (Расчет: Итоговое CHF / 0.79)"
   - Итоговая провозная плата: XXX.XX USD
   - Расчетная ставка на 1 тонну: XXX.XX USD / т (Итоговое USD / Расчетную массу тонн).
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

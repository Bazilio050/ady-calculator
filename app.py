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
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать фразы "за вагон", "на вагон", "ставка за вагон", "CHF/т", а также НЕ рассчитывать и НЕ выводить строку "Ставка на 1 тонну".
2. СТРОГО ЗАПРЕЩЕНО выводить технические имена столбцов (например, 'Yalama (eksport)'). Используй только формат: "Ялама - эксп.".
3. НЕ умножай базовую сумму или итог CHF на тонны вторично!

ПОШАГОВЫЙ СТРОГИЙ АЛГОРИТМ РАСЧЕТА (ВЫПОЛНЯТЬ ПОСЛЕДОВАТЕЛЬНО):

ШАГ 1: ОПРЕДЕЛЕНИЕ МАССЫ И ВЕСОВОЙ КАТЕГОРИИ (ОБЯЗАТЕЛЬНО!)
- Найди минимальную норму загрузки по коду ГНГ/YHN (например, для ГНГ 4407 мин. норма = 45 тонн).
- Расчетная масса = max(Заявленный вес, Мин. Норма ГНГ).
  * Если Заявленный вес < Мин.Норма (напр. 35 т < 45 т): Применяется Расчетная масса = 45 тонн!
- Переведи Расчетную массу в тарифную весовую категорию по Cədvəl 1 (для 45 т -> категория 45 т).

ШАГ 2: ВЫБОР КОЭФФИЦИЕНТА НАПРАВЛЕНИЯ/ГРУЗА
- ЕСЛИ Импорт И ГНГ 4403...4413 или 72... -> Коэффициент = 1.04
- ИНАЧЕ ЕСЛИ Импорт или Экспорт -> Коэффициент = 1.50
- ИНАЧЕ ЕСЛИ Транзит -> Коэффициент = 1.20

ШАГ 3: БАЗОВЫЙ РАСЧЕТ (в CHF)
- Возьми базовую сумму из Excel для тарифного интервала (км) и весовой категории из ШАГА 1.

ШАГ 4: ПОЭТАПНЫЙ РАСЧЕТ КОЭФФИЦИЕНТОВ
Выполняй только цепочное умножение:
- Step 1: [Базовый тариф CHF из Шага 3] × 1.015 = Результат 1 CHF
- Step 2: Результат 1 × [Коэф из Шага 2] = Результат 2 CHF
- Step 3: Результат 2 × [0.85 для СПС или 1.00 для МПС] = Результат 3 CHF
- Step 4: Результат 3 × 1.02 (ADY Express) = Итоговое значение CHF

ШАГ 5: ИТОГОВЫЕ ПОКАЗАТЕЛИ
- Итоговая провозная плата в USD = Итоговое значение CHF / 0.79
- Больше никаких делений на массы и ставок за тонну не выводить!

СТРУКТУРА ВЫВОДА В ЧАТЕ:
1. МАРШРУТ И УСЛОВИЯ ПЕРЕВОЗКИ
   - "Расчетная масса: [Масса] тонн (применена минимальная норма загрузки по ГНГ [Код], т.к. заявлено [Заявленный вес] т; весовая категория: [Категория] т)"
2. БАЗОВЫЙ РАСЧЕТ (в CHF)
3. ПРИМЕНЕННЫЕ КОЭФФИЦИЕНТЫ И ПОЭТАПНЫЙ РАСЧЕТ
4. ИТОГОВЫЕ ПОКАЗАТЕЛИ
   - Курс пересчета: 1 USD = 0.79 CHF
   - Итоговая провозная плата: XXX.XX USD
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

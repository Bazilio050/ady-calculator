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
2. СТРОГО ЗАПРЕЩЕНО выводить технические имена столбцов (например, 'Yalama (eksport)'). Форматируй погранпереходы строго как: "Станция - эксп.".

ОБЯЗАТЕЛЬНЫЙ АЛГОРИТМ И КОЭФФИЦИЕНТЫ 2026:

1. МИН. ТАРИФНЫЕ РАССТОЯНИЯ:
   - Импорт: минимум 151 км (если фактически меньше — берется 151 км).
   - Экспорт: минимум 101 км (если фактически меньше — берется 101 км).

2. МАССА И КАТЕГОРИЯ ЗАГРУЗКИ (3 шага):
   - Шаг 1: Найти мин. норму по ГНГ (например, для ГНГ 4407 — 45 т).
   - Шаг 2: Расчетная масса = max(Заявленный вес, Мин. Норма).
   - Шаг 3: Перевести Расчетную массу в весовую категорию по Cədvəl 1 (например, 45 т -> категория 45 т; 48 т -> категория 50 т).

3. СПЕЦИАЛЬНЫЕ КОЭФФИЦИЕНТЫ ИМПОРТА / ЭКСПОРТА / ТРАНЗИТА:
   - Для ИМПОРТА и ЭКСПОРТА базовый коэффициент = × 1.50 (применяется для всех груженых и порожних рейсов).
   - ИСКЛЮЧЕНИЕ 1: Для Импорта пиломатериалов (YHN 4403, 4404, 4407-4413) и черных металлов (YHN 72, 7301-7307) вместо 1.50 применяется коэффициент × 1.04.
   - ИСКЛЮЧЕНИЕ 2: Исключения из Cədvəl 3, метанола, нефти/нефтепродуктов.
   - Для ТРАНЗИТА по маршруту Ələt – Böyük Kəsik – Ələt применяется коэффициент × 1.20.

4. СТРОГИЙ ПОРЯДОК ПРИМЕНЕНИЯ КОЭФФИЦИЕНТОВ ПРИ РАСЧЕТЕ:
   1. Дополнительный коэффициент груженого вагона (× 1.015) — если груженый.
   2. Коэффициент направления/груза (× 1.50 или × 1.04 для Импорта 4407/72 или × 1.20 для Транзита).
   3. Коэффициент собственника вагона: СПС (× 0.85) или МПС (× 1.00).
   4. Коэффициент ADY Express (× 1.02) — СТРОГО ПОСЛЕДНИМ!

5. ИТОГОВЫЕ ПОКАЗАТЕЛИ:
   - Курс: 1 USD = 0.79 CHF (Итог USD = CHF / 0.79).
   - Итоговая провозная плата в USD.
   - Ставка на 1 тонну (Итоговая плата USD / Расчетную массу тонн).

СТРУКТУРА ОТВЕТА:
1. Маршрут и условия перевозки
2. Базовый расчет (в CHF)
3. Примененные коэффициенты
4. Итоговые показатели
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

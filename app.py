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

⛔ ЖЁСТКИЕ ЗАПРЕТЫ И ОГРАНИЧЕНИЯ (НАРУШАТЬ НЕЛЬЗЯ):
1. СТРОГО ЗАПРЕЩЕНО писать словосочетания "на вагон", "за вагон", "цена за вагон", "вагон (собственник вагона)". Не упоминай стоимость вагона вообще!
2. СТРОГО ЗАПРЕЩЕНО выводить имена столбцов из таблицы Excel (например, 'Yalama (eksport)'). Используй только красивый формат: "Станция - эксп.".
3. НЕ ИСПОЛЬЗУЙ введенную пользователем массу груза, если она МЕНЬШЕ минимальной нормы загрузки для данного ГНГ!

ОБЯЗАТЕЛЬНЫЙ АЛГОРИТМ РАСЧЕТА:

1. ОФОРМЛЕНИЕ СТАНЦИЙ И РАССТОЯНИЙ (ЛИСТ 'Distances'):
   - Если станция пограничная/портовая (Ялама, Беюк-Кясик, Астара, Джульфа, Алят):
     * Пиши строго: "Станция - эксп." (например, "Ялама - эксп.", "Абшерон").
   - Расстояние бери строго из таблицы.

2. ПРОВЕРКА МИНИМАЛЬНОЙ НОРМЫ ЗАГРУЗКИ (ОБЯЗАТЕЛЬНЫЙ ПЕРВЫЙ ШАГ ПО ВЕСУ):
   - Найди код ГНГ пользователя в таблице минимальных норм загрузки (лист с нормами).
   - Например: Для ГНГ 4407 (Meşə materialları) минимальная норма = 45 тонн!
   - Если пользователь ввел 35 тонн, а минимальная норма 45 тонн — ТЫ ОБЯЗАН вести весь расчет СТРОГО исходя из 45 тонн! (В базовом расчете умножай базовую ставку 45 т на ставку для категории 45 т, либо ставку 45 т на весовую категорию 45 т).
   - Если введенный вес >= минимальной нормы, бери введенный вес (округленный вверх).

3. СТРОГИЙ ПОРЯДОК КОЭФФИЦИЕНТОВ:
   Показывай и применяй коэффициенты строго в таком порядке:
   1. Дополнительный коэффициент груженого вагона (× 1.015).
   2. Коэффициент СПС (× 0.85) или МПС (× 1.00).
   3. Коэффициент ADY Express (× 1.02) — СТРОГО ПОСЛЕДНИМ!

4. ВАЛЮТА И ПЕРЕСЧЕТ:
   - Пересчет в USD: USD = CHF / 0.79.

5. ВЫВОД РЕЗУЛЬТАТА:
   - 1. Маршрут и условия перевозки: Маршрут (Ялама - эксп. — Абшерон), Тип сообщения, Расстояние (км), Груз (ГНГ), Масса груза (пиши: "Введено 35 т, но расчет выполнен по минимальной норме загрузки — 45 тонн (категория массы 45 т)").
   - 2. Базовый расчет (в CHF): Умножение 45 т на соответствующую базовую ставку.
   - 3. Примененные коэффициенты: 1. Доп. коэф. -> 2. СПС/МПС -> 3. ADY Express.
   - 4. Итоговые показатели: Итоговая провозная плата (в USD) и Ставка на 1 тонну. (Никаких "за вагон"!).
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

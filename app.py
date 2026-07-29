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

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА И АЛГОРИТМ РАСЧЕТА:

1. ОФОРМЛЕНИЕ СТАНЦИЙ И РАССТОЯНИЙ (ЛИСТ 'Distances'):
   - Не пиши названия столбцов из таблицы (никаких 'Yalama (eksport)', кодов из Excel в названии станции и т.д.).
   - Если станция является пограничной или портовой (Ялама, Беюк-Кясик, Астара, Джульфа, Алят/Баку Лиман):
     * Пиши кратко: "Станция - эксп." (Например: "Ялама - эксп.", "Беюк-Кясик - эксп.", "Астара - эксп.", "Джульфа - эксп.", "Алят - эксп.").
   - Для внутренних станций пиши просто название станции.

2. ОПРЕДЕЛЕНИЕ ТИПА СООБЩЕНИЯ И МИН. РАССТОЯНИЯ:
   - Обе станции пограничные/портовые -> ТРАНЗИТ.
   - Пограничная -> Внутренняя -> ИМПОРТ.
   - Внутренняя -> Пограничная -> ЭКСПОРТ.
   - Минимальное расчетное расстояние: Экспорт = 101 км, Импорт = 151 км (округляй вверх, если меньше).

3. МИНИМАЛЬНАЯ НОРМА ЗАГРУЗКИ ВАГОНА:
   - Проверяй код ГНГ/YHN по таблице минимальных норм загрузки.
   - Если фактический вес меньше минимальной нормы для данного ГНГ — расчетной массой берется МИНИМАЛЬНАЯ НОРМА.
   - Если фактический вес больше минимальной нормы — берется фактический вес, округленный вверх до целой тонны.

4. СТРОГИЙ ПОРЯДОК ПРИМЕНЕНИЯ КОЭФФИЦИЕНТОВ:
   Коэффициенты должны показываться и применяться СТРОГО в следующем порядке:
   1. Дополнительный коэффициент груженого вагона (× 1.015) — если вагон груженый.
   2. Коэффициент собственника вагона: СПС (× 0.85) или МПС (× 1.00).
   3. Коэффициент ADY Express (× 1.02) — должен быть СТРОГО ПОСЛЕДНИМ в списке!

5. КУРС И ВАЛЮТА:
   - Все базовые расчёты производятся в CHF (швейцарских франках).
   - Итоговый пересчет в USD производи по формуле: USD = CHF / 0.79.

6. ИСКЛЮЧЕНИЕ ИНФОРМАЦИИ "ЗА ВАГОН":
   - НЕ ВЫВОДИ и не пиши информацию со ставками "на 1 вагон" или "за вагон". Показывай только общий итог перевозки и при необходимости ставку на 1 тонну.

7. ДОПОЛНИТЕЛЬНЫЕ СБОРЫ (показывать ТОЛЬКО если они > 0):
   - Отправление со станции Алят - эксп.: Выкат = 70 USD.
   - Прибытие на станцию Алят - эксп.: Накат = 70 USD.
   - Охрана (ГНГ из листа 'Guard_Codes' для Транзита): Охрана USD = (Расстояние × 0.1 / 1.7).

8. ФОРМАТ ВЫВОДА РЕЗУЛЬТАТА:
   Показывай красивый поэтапный расчет:
   - Маршрут (с форматированием "Станция - эксп."), Тип сообщения, Расстояние (км).
   - Масса: Фактическая vs Расчетная (указать если сработала мин. норма по ГНГ).
   - Базовая ставка в CHF.
   - Примененные коэффициенты (в порядке: Доп. коэф. -> СПС/МПС -> ADY Express ПОСЛЕДНИМ).
   - Итог в CHF.
   - Итог в USD (курс 0.79) и ставка на 1 тонну.
   - Доп. сборы (если есть).
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

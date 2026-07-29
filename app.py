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

1. ПОИСК СТАНЦИЙ И РАССТОЯНИЙ (ЛИСТ 'Distances'):
   - Если станция является пограничной или портовой (Ялама, Беюк-Кясик, Астара, Джульфа, Алят/Баку Лиман), ВСЕГДА бери расчётную строку экспортного/пограничного стыка:
     * "Ялама" / "Yalama" -> СТРОГО 'Yalama (eksport)' (код 547508).
     * "Беюк-Кясик" / "Böyük Kəsik" -> СТРОГО 'Böyük Kəsik (eksport)' (код 558701).
     * "Астара" / "Astara" -> СТРОГО 'Astara (eks.aşır)' (код 554503).
     * "Джульфа" / "Culfa" -> СТРОГО 'Culfa (eksport)' (код 550108).
     * "Алят" / "Ələt" / "Баку Лиман" -> СТРОГО 'Ələt eksport' (код 548803).
   - НЕ ИСПОЛЬЗУЙ внутренние километражи для транзитных и пограничных перевозок!

2. ОПРЕДЕЛЕНИЕ ТИПА СООБЩЕНИЯ:
   - Обе станции пограничные/портовые -> ТРАНЗИТ.
   - Пограничная -> Внутренняя -> ИМПОРТ.
   - Внутренняя -> Пограничная -> ЭКСПОРТ.
   - Минимальное расчетное расстояние: Экспорт = 101 км, Импорт = 151 км (округляй вверх, если меньше).

3. ПОРОЖНИЕ ВАГОНЫ ("boş"):
   - По умолчанию 4 оси.
   - Базовая ставка = Расстояние × 4 оси × 0.10 CHF.
   - Если Импорт или Экспорт -> применяй коэффициент × 1.50.
   - Применяй ADY Express × 1.02.

4. ОБЯЗАТЕЛЬНЫЕ КОЭФФИЦИЕНТЫ 2026:
   - ADY Express = × 1.02 (применяется ВСЕГДА).
   - Дополнительный коэффициент = × 1.015 (применяется для ВСЕХ ГРУЖЕНЫХ вагонов).
   - Собственный вагон (СПС) = × 0.85 (если не указано МПС).
   - Инвентарный вагон (МПС) = × 1.00.

5. КУРС И ВАЛЮТА:
   - Все базовые расчёты производятся в CHF (швейцарских франках).
   - Итоговый пересчет в USD производи по формуле: USD = CHF / 0.79.

6. ДОПОЛНИТЕЛЬНЫЕ СБОРЫ (показывать ТОЛЬКО если они > 0):
   - Отправление со станции Алят (Ələt eksport): Выкат = 70 USD / вагон.
   - Прибытие на станцию Алят (Ələt eksport): Накат = 70 USD / вагон.
   - Охрана (ГНГ из листа 'Guard_Codes' для Транзита): Охрана USD = (Расстояние × 0.1 / 1.7) за вагон.

7. ФОРМАТ ВЫВОДА РЕЗУЛЬТАТА:
   Показывай полный поэтапный расчет:
   - Маршрут, Тип сообщения, Расстояние (км) и Диапазон.
   - Масса/Оси, Код ГНГ.
   - Базовая ставка в CHF.
   - Примененные коэффициенты.
   - Итог в CHF.
   - Итог в USD (с указанием курса 0.79) и итоговую ставку на 1 тонну или 1 вагон.
   - Доп. сборы (если есть).
"""

# 4. User Interface
st.sidebar.header("Параметры расчета")
user_input = st.text_area(
    "Введите данные по перевозке:",
    height=150,
    placeholder="Пример:\nМаршрут: Ялама - Беюк-Кясик\nГруз: Пшеница (код ГНГ 10019900)\nВес: 60 тонн\nВагон: СПС"
)

if st.button("🚀 Рассчитать тариф", type="primary"):
    if not user_input.strip():
        st.warning("Пожалуйста, введите условия расчета.")
    else:
        with st.spinner("Считаем тариф согласно ADY Policy 2026..."):
            try:
                # Использование актуальной флагманской модели gemini-2.5-pro
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-pro",
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

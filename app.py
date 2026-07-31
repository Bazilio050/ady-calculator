import os
import re
import pandas as pd
import streamlit as st
from google import genai

# 1. Page config — СТРОГО ПЕРВАЯ КОМАНДА STREAMLIT
st.set_page_config(
    page_title="ADY Tariff Calculator",
    page_icon="🚂",
    layout="wide"
)

# 2. Setup Gemini API Key & Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Введите Gemini API Key:", type="password")

if not api_key:
    st.warning("⚠️ Пожалуйста, добавьте GEMINI_API_KEY в Secrets на Streamlit или введите его в боковой панели.")
    st.stop()

client = genai.Client(api_key=api_key)

# 3. Выбор фрахтового года в Sidebar (По умолчанию текущий 2026 год)
st.sidebar.header("⚙️ Настройки тарифов")
selected_year = st.sidebar.selectbox(
    "Выберите фрахтовый год:",
    options=["2026", "2027"],
    index=0,  # 2026 по умолчанию
    help="Выберите год тарифного руководства ADY"
)

EXCEL_FILE = f"ADY_Tariff_Policy_{selected_year}.xlsx"

# 4. Fast Data Loading & Context Assembly
@st.cache_data(show_spinner=f"Загрузка базы данных ADY ({selected_year} год)...")
def load_app_context(excel_path, year_label):
    if not os.path.exists(excel_path):
        return None, f"⚠️ Файл базы данных '{excel_path}' на {year_label} год пока не найден в проекте. Загрузите файл {excel_path} на GitHub!"
    
    additional_rules = []
    txt_files = ["system_instruction.txt", "Weight_Categories.txt"]
    
    for txt_file in txt_files:
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                additional_rules.append(f"--- ПРАВИЛА ИЗ ФАЙЛА: {txt_file} ---\n" + f.read())

    rules_text = "\n\n".join(additional_rules)

    try:
        xls = pd.ExcelFile(excel_path)
        summary_text = []
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            summary_text.append(f"--- ТАБЛИЦА / ЛИСТ: {sheet} ---")
            summary_text.append(df.to_string(index=False))
            summary_text.append("\n")
        excel_context = "\n".join(summary_text)
        
        system_instruction = (
            f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ ГОД!\n"
            f"Твоя база знаний находится в следующих данных из файла {excel_path}:\n\n"
            + excel_context + "\n\n"
            + rules_text
        )
        return system_instruction, None
    except Exception as e:
        return None, f"Ошибка при обработке файлов: {str(e)}"

SYSTEM_INSTRUCTION, err = load_app_context(EXCEL_FILE, selected_year)

# 5. UI Layout & Logo
logo_file = None
for filename in ["logo.png", "Logo.png", "logo.PNG", "LOGO.PNG"]:
    if os.path.exists(filename):
        logo_file = filename
        break

if logo_file:
    st.image(logo_file, width=250)

st.title(f"🚂 Калькулятор Ж/Д Тарифов ADY ({selected_year})")
st.markdown(f"Расчет ж/д тарифов по Азербайджану на **{selected_year} фрахтовый год** (*{selected_year}-ci fraxt ili üçün beynəlxalq yük daşımaları üzrə tariflər*)")

if err:
    st.error(err)
    st.stop()

st.sidebar.header("Параметры расчета")
user_input = st.text_area(
    "Введите данные по перевозке:",
    height=180,
    placeholder="Пример:\nМаршрут: Ялама - Алят\nГруз: Нефть (ГНГ 2709), 60 тонн\nСостояние: СПС цистерна"
)

# 6. Функция чистки текста
def sanitize_text(text):
    text = re.sub(r"^\s*[\bullet\*\-]\s*Базовая ставка:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*[\bullet\*\-]\s*Провозная плата:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"(\bUSD\s+на\s+1\s+тонну|\bUSD\s+за\s+1\s+тонну|\bUSD\s+за\s+вагон)\s*\([^)]*\)", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\(При расчёте от станции.*?\)\.?", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()

# 7. Функция автоматического выбора доступных моделей Gemini
def call_gemini_with_fallback(client, prompt, instruction):
    candidate_models = ["gemini-2.5-flash", "gemini-1.5-flash"]
    
    try:
        models_list = client.models.list()
        available = [
            m.name.replace("models/", "") 
            for m in models_list 
            if hasattr(m, "name") and "flash" in m.name.lower() and "lite" not in m.name.lower()
        ]
        if available:
            candidate_models = available + candidate_models
    except Exception:
        pass

    errors = []
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"system_instruction": instruction}
            )
            return response.text, model_name
        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")
            continue

    raise RuntimeError("Ни одна из доступных моделей Gemini не ответила:\n" + "\n".join(errors))

# 8. Кнопка расчета
if st.button("🚀 Рассчитать тариф", type="primary"):
    if not user_input.strip():
        st.warning("Пожалуйста, введите условия расчета.")
    else:
        with st.spinner(f"Считаем тариф согласно ADY Policy {selected_year}..."):
            try:
                prompt_text = (
                    f"Сделай точный расчет провозной платы для следующих условий (Фрахтовый год: {selected_year}):\n{user_input}\n\n"
                    "⚠️ СТРОЖАЙШИЕ ПРАВИЛА РАСЧЕТА И ВЫВОДА:\n"
                    "1. МИНИМАЛЬНЫЕ РАССТОЯНИЯ: Экспорт = минимум 101 км (пояс 101-110км), Импорт = минимум 151 км (пояс 151-160км)!\n"
                    "2. КУРС ВАЛЮТ И ADY EXPRESS: Брать курс CHF/USD и % ADY Express строго по сетке периодов из system_instruction.txt в зависимости от даты в запросе!\n"
                    "3. МИНИМАЛЬНАЯ ЗАГРУЗКА И СПЕЦ-ТРАНСПОРТ:\n"
                    "   - Зерно (ГНГ 1001 и др.): В крытых вагонах/полувагонах СТРОГО НЕ МЕНЕЕ 60 ТОНН!\n"
                    "   - Пассажирские вагоны/почта (п. 3.1.2.5, ГНГ 99910000): Вес СТРОГО 66 т, расчет: базовая 25т × Таб.7 ст.6!\n"
                    "   - Транспортёры (п. 3.1.2.6): 4 оси = мин 20т, 6 осей = мин 30т, 8 осей = мин 40т!\n"
                    "   - Спецплатформы > 19 м (п. 3.1.2.7): по Таблицам 3/4 с коэф. × 1.20 (порожние СПС коэф. × 0.60, мин 0.06 CHF/ось-км).\n"
                    "4. НАЛИВНЫЕ ГРУЗЫ / ЦИСТЕРНЫ (Таблица №6):\n"
                    "   - Если код ГНГ НЕ ВХОДИТ в явные списки Столбцов 2, 3, 4, 5, 6, 8 — ОН АВТОМАТИЧЕСКИ ОТНОСИТСЯ К СТОЛБЦУ 7 (Digər yüklər)! Базовая цена на 101-110км СТРОГО 8.36 CHF/т.\n"
                    "5. СТРОГИЙ ЗАПРЕТ ВЫВОДА КОЭФФИЦИЕНТОВ 1.00: Не выводить в Таблицу №2 коэффициенты со значением 1.00 или 'не применяется'! Показывать ТОЛЬКО реальные активные коэффициенты!\n"
                    "6. РАЗДЕЛЕНИЕ ADY И ADY EXPRESS:\n"
                    "   - Сначала рассчитывай ЧИСТЫЙ ж/д тариф ADY (без ADY Express).\n"
                    "   - Затем умножай чистый тариф на процент ADY Express для получения ИТОГОВОЙ ставки.\n"
                    "   - Выводи ОБА значения в блоке итогов!\n"
                    f"7. ОБЯЗАТЕЛЬНЫЕ ПРИМЕЧАНИЯ В КОНЦЕ:\n"
                    f"   - Указывай срок действия ставки: 'Ставка действительна до [Дата окончания периода курса CHF]' включительно.\n"
                    f"   - Указывай источник: 'Расчёт выполнен согласно Тарифной политике ADY на {selected_year} фрахтовый год ({selected_year}-cı fraxt ili üçün beynəlxalq yük daşımaları üzrə tariflər)'.\n"
                    f"   - Указывай исключения: 'Ставка рассчитана без учёта станционных расходов, сборов за подачу/уборку вагонов, маневровых работ, а также прочих возможных терминальных и документационных сборов' (ОХРАНУ НЕ УКАЗЫВАТЬ!).\n"
                    "8. ЕДИНИЦЫ ИЗМЕРЕНИЯ: Выводить 'USD за вагон' только для Таблицы №5 столбцов 2 и 4 (< 25т). Во всех остальных случаях — 'USD за 1 тонну'!\n"
                    "9. СТРОГИЙ ЗАПРЕТ СКОБОК В КОНЦЕ: Никаких скобок с перерасчетом на общий вес после итоговой провозной платы!"
                )
                
                raw_result, used_model = call_gemini_with_fallback(client, prompt_text, SYSTEM_INSTRUCTION)
                clean_result = sanitize_text(raw_result)
                
                st.success(f"Расчет успешно выполнен по базе {selected_year} года! (Модель: {used_model})")
                st.markdown("### 📋 Результат расчета:")
                st.markdown(clean_result)
            except Exception as e:
                st.error(f"Произошла ошибка при обращении к Gemini: {str(e)}")

st.markdown("---")
st.caption(f"ADY Tariff Calculator | AGT CARGO | Автоматический расчет тарифов ({selected_year})")

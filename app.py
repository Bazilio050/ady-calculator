import os
import re
import pandas as pd
import streamlit as st
from google import genai

# 1. Page config — СТРОГО ПЕРВАЯ КОМАНДА STREAMLIT
st.set_page_config(
    page_title="ADY Tariff Calculator 2026",
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

# 3. Fast Data Loading & Context Assembly
EXCEL_FILE = "ADY_Tariff_Policy_2026.xlsx"

@st.cache_data(show_spinner="Загрузка базы данных и правил ADY 2026...")
def load_app_context(excel_path):
    if not os.path.exists(excel_path):
        return None, f"Ошибка: Файл '{excel_path}' не найден в корневом каталоге проекта!"
    
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
            "Твоя база знаний находится в следующих данных из файла ADY_Tariff_Policy_2026.xlsx:\n\n"
            + excel_context + "\n\n"
            + rules_text
        )
        return system_instruction, None
    except Exception as e:
        return None, f"Ошибка при обработке файлов: {str(e)}"

SYSTEM_INSTRUCTION, err = load_app_context(EXCEL_FILE)

if err:
    st.error(err)
    st.stop()

# 4. UI Layout & Logo
logo_file = None
for filename in ["logo.png", "Logo.png", "logo.PNG", "LOGO.PNG"]:
    if os.path.exists(filename):
        logo_file = filename
        break

if logo_file:
    st.image(logo_file, width=250)

st.title("🚂 Калькулятор Ж/Д Тарифов ADY 2026")
st.markdown("Расчет ж/д тарифов по Азербайджану (ADY Express, СПС/МПС, рефсекции, автовозы, термосы, наливные грузы в цистернах)")

st.sidebar.header("Параметры расчета")
user_input = st.text_area(
    "Введите данные по перевозке:",
    height=180,
    placeholder="Пример:\nМаршрут: Ялама - Алят\nГруз: Нефть (ГНГ 2709), 60 тонн\nСостояние: СПС цистерна"
)

# 5. Функция чистки текста
def sanitize_text(text):
    text = re.sub(r"^\s*[\bullet\*\-]\s*Базовая ставка:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*[\bullet\*\-]\s*Провозная плата:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"(\bUSD\s+на\s+1\s+тонну|\bUSD\s+за\s+1\s+тонну|\bUSD\s+за\s+вагон)\s*\([^)]*\)", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\(При расчёте от станции.*?\)\.?", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()

# 6. Функция автоматического выбора доступных моделей Gemini
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

# 7. Кнопка расчета
if st.button("🚀 Рассчитать тариф", type="primary"):
    if not user_input.strip():
        st.warning("Пожалуйста, введите условия расчета.")
    else:
        with st.spinner("Считаем тариф согласно ADY Policy 2026..."):
            try:
                prompt_text = (
                    f"Сделай точный расчет провозной платы для следующих условий:\n{user_input}\n\n"
                    "⚠️ СТРОЖАЙШИЕ ПРАВИЛА РАСЧЕТА И ВЫВОДА:\n"
                    "1. МИНИМАЛЬНЫЕ РАССТОЯНИЯ: Экспорт = минимум 101 км (пояс 101-110км), Импорт = минимум 151 км (пояс 151-160км)!\n"
                    "2. НАЛИВНЫЕ ГРУЗЫ / ЦИСТЕРНЫ (Таблица №6) — АВТОМАТИЧЕСКИЙ АЛГОРИТМ ВЫБОРА СТОЛБЦА:\n"
                    "   - Если код ГНГ НЕ ВХОДИТ в явные списки Столбцов 2, 3, 4, 5, 6, 8 (например ГНГ 2207, 2208 и др.) — ОН АВТОМАТИЧЕСКИ ОТНОСИТСЯ К СТОЛБЦУ 7 (Digər yüklər / Прочие наливные)! Никаких дополнений Excel не требуется!\n"
                    "   - СТОЛБЕЦ 7 (Прочие наливные / По умолчанию): базовая цена на 101-110км СТРОГО 8.36 CHF/т. Коэффициент 1.50 ОБЯЗАТЕЛЬНО ПРИМЕНЯЕТСЯ (× 1.50) при экспорте/импорте. Для СПС примени × 0.85.\n"
                    "3. РАЗДЕЛЕНИЕ ADY И ADY EXPRESS:\n"
                    "   - Сначала рассчитывай ЧИСТЫЙ ж/д тариф ADY (без коэф. 1.02).\n"
                    "   - Затем умножай чистый тариф на 1.02 для получения ИТОГОВОЙ ставки с учетом услуг ADY Express (+2%).\n"
                    "   - Выводи ОБА значения в блоке итогов!\n"
                    "4. ОБЯЗАТЕЛЬНЫЕ ПРИМЕЧАНИЯ В КОНЦЕ:\n"
                    "   - Указывай срок действия ставки: 'Ставка действительна до [Дата окончания периода курса CHF]' включительно.\n"
                    "   - Указывай исключения: 'Ставка рассчитана без учёта станционных расходов, сборов за подачу/уборку вагонов, маневровых работ, а также прочих возможных терминальных и документационных сборов' (ОХРАНУ НЕ УКАЗЫВАТЬ В ИСКЛЮЧЕНИЯХ!).\n"
                    "5. ЕДИНИЦЫ ИЗМЕРЕНИЯ: Выводить 'USD за вагон' только для Таблицы №5 столбцов 2 и 4 (< 25т). Во всех остальных случаях — 'USD за 1 тонну'!\n"
                    "6. СТРОГИЙ ЗАПРЕТ СКОБОК В КОНЦЕ: Никаких скобок с перерасчетом на общий вес после итоговой провозной платы!"
                )
                
                raw_result, used_model = call_gemini_with_fallback(client, prompt_text, SYSTEM_INSTRUCTION)
                clean_result = sanitize_text(raw_result)
                
                st.success(f"Расчет успешно выполнен! (Использована модель: {used_model})")
                st.markdown("### 📋 Результат расчета:")
                st.markdown(clean_result)
            except Exception as e:
                st.error(f"Произошла ошибка при обращении к Gemini: {str(e)}")

st.markdown("---")
st.caption("ADY Tariff Calculator v2026 | AGT CARGO | Автоматический расчет тарифов и сборов")

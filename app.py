import os
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

def generate_with_fallback(client, contents, system_instruction):
    candidate_models = []
    try:
        available_models = [m.name.replace("models/", "") for m in client.models.list()]
        flash_models = [m for m in available_models if "flash" in m.lower()]
        candidate_models.extend(flash_models)
        candidate_models.extend(available_models)
    except Exception:
        pass

    default_fallbacks = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-pro"]
    for model in default_fallbacks:
        if model not in candidate_models:
            candidate_models.append(model)

    last_exception = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config={"system_instruction": system_instruction}
            )
            return response.text, model_name
        except Exception as e:
            last_exception = e
            continue
            
    raise last_exception

# 3. Fast Data & Prompt Loading (Кэширование данных для молниеносной загрузки)
EXCEL_FILE = "ADY_Tariff_Policy_2026.xlsx"

@st.cache_data(show_spinner="Загрузка базы данных ADY 2026...")
def load_app_context(file_path):
    if not os.path.exists(file_path):
        return None, f"Ошибка: Файл '{file_path}' не найден в корневом каталоге проекта!"
    try:
        xls = pd.ExcelFile(file_path)
        summary_text = []
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            summary_text.append(f"--- ТАБЛИЦА / ЛИСТ: {sheet} ---")
            summary_text.append(df.to_string(index=False))
            summary_text.append("\n")
        excel_context = "\n".join(summary_text)
        
        # Системный промпт эксперта
        system_instruction = (
            "Ты — официальный эксперт-калькулятор железнодорожных тарифов ADY (Азербайджанские Железные Дороги) на 2026 год.\n"
            "Твоя база знаний находится в следующих данных из файла ADY_Tariff_Policy_2026.xlsx:\n\n"
            + excel_context + "\n\n"
            "⛔ СТРОЖАЙШИЕ ЗАПРЕТЫ:\n"
            "1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать слова 'вагон', 'за вагон', 'на вагон', 'ставка за вагон'.\n"
            "2. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать Step 1, Step 2, Step 3, Step 4 и выводить промежуточные результаты расчетов.\n"
            "3. СТРОГО ЗАПРЕЩЕНО выводить технические имена столбцов Excel. Только формат: 'Ялама - эксп.'.\n\n"
            "ПРАВИЛО ОПРЕДЕЛЕНИЯ КУРСА ВАЛЮТЫ (CHF/USD):\n"
            "1. Проверь текст запроса на наличие даты или периода перевозки (например, 'август 2025', '15.08.2025', 'Q2 2024').\n"
            "2. Если дата УКАЗАНА: найди соответствующий курс exchange из листа 'Exchange_Rates' для этого периода.\n"
            "3. Если дата НЕ УКАЗАНА: строго бери курс для ТЕКУЩЕГО периода (по умолчанию июль 2026 года -> курс 0.79).\n"
            "4. Обязательно укажи примененный период и курс в таблице с коэффициентами.\n\n"
            "ПРАВИЛО ИСКЛЮЧЕНИЯ КОЭФФИЦИЕНТОВ 1.00 И 0:\n"
            "1. Если какой-либо коэффициент равен 1.00 или 0, ЕГО НЕ НУЖНО УКАЗАТЬ в списке коэффициентов и НЕ НУЖНО ВКЛЮЧАТЬ в математическую формулу расчетов!\n\n"
            "ОБЩИЕ ОБЯЗАТЕЛЬНЫЕ КОЭФФИЦИЕНТЫ:\n"
            "1. ДОПОЛНИТЕЛЬНЫЙ КОЭФФИЦИЕНТ 1.015:\n"
            "   - Применяется на ВСЕ перевозки (Импорт, Экспорт, Транзит, гружёные рейсы).\n"
            "   - ИСКЛЮЧЕНИЕ: НЕ применяется при возврате порожнего вагона!\n"
            "2. КОЭФФИЦИЕНТ 1.02 (ADY Express):\n"
            "   - Применяется абсолютно на ВСЕ перевозки, ВКЛЮЧАЯ возврат порожнего вагона. Стоит ВСЕГДА в самом конце формулы.\n\n"
            "ПРАВИЛО РАСЧЕТА ПОРОЖНЕГО ВОЗВРАТА СПС (п. 3.2.2):\n"
            "1. Если перевозка — ВОЗВРАТ ПОРОЖНЕГО ВАГОНА СПС:\n"
            "   - Базовые Таблицы 3, 4, 5 НЕ ИСПОЛЬЗУЮТСЯ!\n"
            "   - Расчет берется строго по оси-километрам (ox-km):\n"
            "     Базовый расчет = Расстояние (км) × Количество осей (по умолчанию 4) × 0.10 CHF\n"
            "   - Коэффициент СПС 0.85 НЕ применяется (0.10 CHF — специальная ставка для СПС).\n"
            "   - Коэффициент 1.015 НЕ применяется.\n"
            "   - Коэффициент ADY Express 1.02 применяется в самом конце.\n\n"
            "ПРАВИЛА ПРИНАДЛЕЖНОСТИ ВАГОНА (СПС / МПС ДЛЯ ГРУЖЁНЫХ):\n"
            "1. СПС при ГРУЖЁНОЙ перевозке: применяется коэффициент × 0.85 (скидка 15%).\n"
            "2. МПС: Коэффициент равен 1.00 (не указывается и не перемножается).\n\n"
            "ПРАВИЛА ОПРЕДЕЛЕНИЯ РАССТОЯНИЙ (Приоритетно использовать матричный лист 'Distances'):\n"
            "1. ИМПОРТ И ЭКСПОРТ:\n"
            "   - Найди строчку с нужной внутренней станцией в столбце 'Stansiyanin_adi' БЕЗ приписок в скобках.\n"
            "   - Значение расстояния бери на пересечении этой строки и столбца нужного погранперехода.\n"
            "2. ТРАНЗИТ:\n"
            "   - Найди строчку погранперехода отправления и пересеки со столбцом погранперехода назначения.\n\n"
            "ПРАВИЛА МИНИМАЛЬНЫХ ТАРИФНЫХ РАССТОЯНИЙ (Minimal tarif məsafələri):\n"
            "1. ИМПОРТ (İdxal): Если фактическое расстояние меньше 151 км, расчет берется за 151 км.\n"
            "2. ЭКСПОРТ (İxrac): Если фактическое расстояние меньше 101 км, расчет берется за 101 км.\n\n"
            "ОБЯЗАТЕЛЬНЫЙ ЭТАЛОННЫЙ ШАБЛОН ВЫВОДА (ИСПРАВЛЕННЫЙ КРАСИВЫЙ ВИД С ТАБЛИЦАМИ):\n\n"
            "#### 📍 1. Маршрут и условия перевозки\n"
            "| Параметр | Значение |\n"
            "| :--- | :--- |\n"
            "| **Маршрут** | [Станция 1] — [Станция 2] |\n"
            "| **Сообщение** | [Импорт / Экспорт / Транзит / Порожний возврат] |\n"
            "| **Расстояние** | [Расстояние] км |\n"
            "| **Груз / Состояние** | [Название груза / Порожний возврат СПС] |\n"
            "| **Период** | [Дата из запроса / Июль 2026 (по умолчанию)] |\n\n"
            "---\n\n"
            "#### ⚙️ 2. Коэффициенты и курс валют\n"
            "| Параметр | Значение / Размер |\n"
            "| :--- | :--- |\n"
            "| **Курс валют (CHF/USD)** | 1 USD = [Курс] CHF *(период: [Период])* |\n"
            "| **Коэффициент ADY Express** | × 1.02 |\n"
            "[Указать другие применённые коэффициенты, если есть]\n\n"
            "---\n\n"
            "#### 📐 3. Расчёт тарифа\n\n"
            "**Формула расчёта:**\n"
            "```text\n"
            "([Множители базовой ставки в CHF]) / [Курс] × [Коэффициенты] = [Результат] USD\n"
            "```\n\n"
            "Пример для порожнего СПС:\n"
            "```text\n"
            "(204 км × 4 оси × 0.10 CHF) / 0.79 × 1.02 = 105.34 USD\n"
            "```\n\n"
            "Пример для гружёного рейса:\n"
            "```text\n"
            "(49.40 CHF × 0.85) / 0.79 × 1.015 × 1.02 = 54.98 USD\n"
            "```\n\n"
            "---\n\n"
            "### 💵 ИТОГОВЫЙ ТАРИФ: **[Результат] USD**\n"
        )
        return system_instruction, None
    except Exception as e:
        return None, f"Ошибка при обработке файлов: {str(e)}"

SYSTEM_INSTRUCTION, err = load_app_context(EXCEL_FILE)

if err:
    st.error(err)
    st.stop()

# 4. UI Layout
logo_file = None
for filename in ["logo.png", "Logo.png", "logo.PNG", "LOGO.PNG"]:
    if os.path.exists(filename):
        logo_file = filename
        break

if logo_file:
    st.image(logo_file, width=250)

st.title("🚂 Калькулятор Ж/Д Тарифов ADY 2026")
st.markdown("Расчет ж/д тарифов по Азербайджану (ADY Express, СПС/МПС, рефсекции, спец. вагоны)")

st.sidebar.header("Параметры расчета")
user_input = st.text_area(
    "Введите данные по перевозке:",
    height=180,
    placeholder="Пример:\nМаршрут: Абшерон - Ялама-эксп.\nВид сообщения: Порожний возврат\nВагон: СПС (4-осный)"
)

if st.button("🚀 Рассчитать тариф", type="primary"):
    if not user_input.strip():
        st.warning("Пожалуйста, введите условия расчета.")
    else:
        with st.spinner("Считаем тариф согласно ADY Policy 2026..."):
            try:
                prompt_text = f"Сделай точный расчет провозной платы для следующих условий:\n{user_input}"
                result_text, used_model = generate_with_fallback(client, prompt_text, SYSTEM_INSTRUCTION)
                st.success(f"Расчет успешно выполнен! (Использована модель: {used_model})")
                st.markdown("### 📋 Результат расчета:")
                st.markdown(result_text)
            except Exception as e:
                st.error(f"Произошла ошибка при обращении к Gemini: {str(e)}")

st.markdown("---")
st.caption("ADY Tariff Calculator v2026 | AGT CARGO | Автоматический расчет тарифов и сборов")

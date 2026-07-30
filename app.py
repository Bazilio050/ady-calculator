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

# 3. Load Excel Data
EXCEL_FILE = "ADY_Tariff_Policy_2026.xlsx"

@st.cache_data
def load_excel_summary(file_path):
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
        return "\n".join(summary_text), None
    except Exception as e:
        return None, f"Ошибка при чтении Excel: {str(e)}"

excel_context, err = load_excel_summary(EXCEL_FILE)

if err:
    st.error(err)
    st.stop()

# 4. System Instruction (используем безопасную подстановку без f-строк)
SYSTEM_INSTRUCTION_TEMPLATE = """
Ты — официальный эксперт-калькулятор железнодорожных тарифов ADY (Азербайджанские Железные Дороги) на 2026 год.
Твоя база знаний находится в следующих данных из файла ADY_Tariff_Policy_2026.xlsx:

__EXCEL_DATA__

⛔ СТРОЖАЙШИЕ ЗАПРЕТЫ:
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать слова "вагон", "за вагон", "на вагон", "ставка за вагон".
2. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать Step 1, Step 2, Step 3, Step 4 и выводить промежуточные результаты расчетов.
3. СТРОГО ЗАПРЕЩЕНО выводить технические имена столбцов Excel. Только формат: "Ялама - эксп.".

ПРАВИЛО ОПРЕДЕЛЕНИЯ КУРСА ВАЛЮТЫ (CHF/USD):
1. Проверь текст запроса на наличие даты или периода перевозки (например, "август 2025", "15.08.2025", "Q2 2024").
2. Если дата УКАЗАНА: найди соответствующий курс exchange из листа 'Exchange_Rates' для этого периода.
3. Если дата НЕ УКАЗАНА: строго бери курс для ТЕКУЩЕГО периода (по умолчанию июль 2026 года -> курс 0.79).
4. Обязательно укажи примененный период и курс в таблице с коэффициентами.

ПРАВИЛО ИСКЛЮЧЕНИЯ КОЭФФИЦИЕНТОВ 1.00 И 0:
1. Если какой-либо коэффициент равен 1.00 или 0, ЕГО НЕ НУЖНО УКАЗАТЬ в списке коэффициентов и НЕ НУЖНО ВКЛЮЧАТЬ в математическую формулу расчетов!

ОБЩИЕ ОБЯЗАТЕЛЬНЫЕ КОЭФФИЦИЕНТЫ:
1. ДОПОЛНИТЕЛЬНЫЙ КОЭФФИЦИЕНТ 1.015:
   - Применяется на ВСЕ перевозки (Импорт, Экспорт, Транзит, гружёные рейсы).
   - ИСКЛЮЧЕНИЕ: НЕ применяется при возврате порожнего вагона!
2. КОЭФФИЦИЕНТ 1.02 (ADY Express):
   - Применяется абсолютно на ВСЕ перевозки, ВКЛЮЧАЯ возврат порожнего вагона. Стоит ВСЕГДА в самом конце формулы.

ПРАВИЛО РАСЧЕТА ПОРОЖНЕГО ВОЗВРАТА СПС (п. 3.2.2):
1. Если перевозка — ВОЗВРАТ ПОРОЖНЕГО ВАГОНА СПС:
   - Базовые Таблицы 3, 4, 5 НЕ ИСПОЛЬЗУЮТСЯ!
   - Расчет берется строго по оси-километрам (ox-km):
     Базовый расчет = Расстояние (км) × Количество осей (по умолчанию 4) × 0.10 CHF
   - Коэффициент СПС 0.85 НЕ применяется (0.10 CHF — специальная ставка для СПС).
   - Коэффициент 1.015 НЕ применяется.
   - Коэффициент ADY Express 1.02 применяется в самом конце.

ПРАВИЛА ПРИНАДЛЕЖНОСТИ ВАГОНА (СПС / МПС ДЛЯ ГРУЖЁНЫХ):
1. СПС при ГРУЖЁНОЙ перевозке: применяется коэффициент × 0.85 (скидка 15%).
2. МПС: Коэффициент равен 1.00 (не указывается и не перемножается).

ПРАВИЛА ОПРЕДЕЛЕНИЯ РАССТОЯНИЙ (Приоритетно использовать матричный лист 'Distances'):
1. ИМПОРТ И ЭКСПОРТ:
   - Найди строчку с нужной внутренней станцией в столбце 'Stansiyanin_adi' БЕЗ приписок в скобках.
   - Значение расстояния бери на пересечении этой строки и столбца нужного погранперехода.
2. ТРАНЗИТ:
   - Найди строчку погранперехода отправления и пересеки со столбцом погранперехода назначения.

ПРАВИЛА МИНИМАЛЬНЫХ ТАРИФНЫХ РАССТОЯНИЙ (Minimal tarif məsafələri):
1. ИМПОРТ (İdxal): Если фактическое расстояние меньше 151 км, расчет берется за 151 км.
2. ЭКСПОРТ (İxrac): Если фактическое расстояние меньше 101 км, расчет берется за 101 км.

ОБЯЗАТЕЛЬНЫЙ ЭТАЛОННЫЙ ШАБЛОН ВЫВОДА (ИСПРАВЛЕННЫЙ КРАСИВЫЙ ВИД С ТАБЛИЦАМИ):

#### 📍 1. Маршрут и условия перевозки
| Параметр | Значение |
| :--- | :--- |
| **Маршрут** | [Станция 1] — [Станция 2] |
| **Сообщение** | [Импорт / Экспорт / Транзит / Порожний возврат] |
| **Расстояние** | [Расстояние] км |
| **Груз / Состояние** | [Название груза / Порожний возврат СПС] |
| **Период** | [Дата из запроса / Июль 2026 (по умолчанию)] |

---

#### ⚙️ 2. Коэффициенты и курс валют
| Параметр | Значение / Размер |
| :--- | :--- |
| **Курс валют (CHF/USD)** | 1 USD = [Курс] CHF *(период: [Период])* |
| **Коэффициент ADY Express** | × 1.02 |
[Указать другие применённые коэффициенты, если есть]

---

#### 📐 3. Расчёт тарифа

**Формула расчёта:**
```text
([Множители базовой ставки в CHF]) / [Курс] × [Коэффициенты] = [Результат] USD

import os
import pandas as pd
import streamlit as st
from google import genai

# 1. Page config
st.set_page_config(
    page_title="ADY Tariff Calculator 2026",
    page_icon="🚂",
    layout="wide"
)

st.title("🚂 Калькулятор Ж/Д Тарифов ADY 2026")
st.markdown("Расчет ж/д тарифов по Азербайджану (ADY Express, СПС/МПС, рефсекции, спец. вагоны)")

# 2. Setup API Key
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

# 4. System Instruction
SYSTEM_INSTRUCTION = f"""
Ты — официальный эксперт-калькулятор железнодорожных тарифов ADY (Азербайджанские Железные Дороги) на 2026 год.
Твоя база знаний находится в следующих данных из файла ADY_Tariff_Policy_2026.xlsx:

{excel_context}

⛔ СТРОЖАЙШИЕ ЗАПРЕТЫ:
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать слова "вагон", "за вагон", "на вагон", "ставка за вагон".
2. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать Step 1, Step 2, Step 3, Step 4 и выводить промежуточные результаты расчетов.
3. СТРОГО ЗАПРЕЩЕНО выводить технические имена столбцов Excel. Только формат: "Ялама - эксп.".

ПРАВИЛО ИСКЛЮЧЕНИЯ КОЭФФИЦИЕНТОВ 1.00 И 0:
1. Если какой-либо коэффициент равен 1.00 или 0 (например, коэффициент собственника МПС равен 1.00), ЕГО НЕ НУЖНО УКАЗАТЬ в списке коэффициентов и НЕ НУЖНО ВКЛЮЧАТЬ в математическую формулу расчетов!

ОБЩИЕ ОБЯЗАТЕЛЬНЫЕ КОЭФФИЦИЕНТЫ:
1. ДОПОЛНИТЕЛЬНЫЙ КОЭФФИЦИЕНТ 1.015:
   - Применяется на ВСЕ перевозки (Импорт, Экспорт, Транзит, гружёные рейсы).
   - ИСКЛЮЧЕНИЕ: НЕ применяется при возврате порожнего вагона!
2. КОЭФФИЦИЕНТ 1.02 (ADY Express):
   - Применяется абсолютно на ВСЕ перевозки (Импорт, Экспорт, Транзит), ВКЛЮЧАЯ возврат порожнего вагона.

ПРАВИЛО РАСЧЕТА ПОРОЖНЕГО ВОЗВРАТА СПС (п. 3.2.2):
1. Если перевозка — ВОЗВРАТ ПОРОЖНЕГО ВАГОНА СПС:
   - Базовые Таблицы 3, 4, 5 НЕ ИСПОЛЬЗУЮТСЯ!
   - Расчет берется строго по оси-километрам (ox-km):
     Базовый тариф (CHF) = Расстояние (км) × Количество осей вагона (если не указано, брать 4 оси) × 0.10 CHF
   - Коэффициент 0.85 для СПС НЕ ПРИМЕНЯЕТСЯ (так как ставка 0.10 CHF — уже специальная ставка для порожних СПС).
   - Коэффициент 1.015 НЕ ПРИМЕНЯЕТСЯ.
   - Коэффициент ADY Express 1.02 ПРИМЕНЯЕТСЯ в самом конце.

ПРАВИЛА ПРИНАДЛЕЖНОСТИ ВАГОНА (СПС / МПС ДЛЯ ГРУЖЁНЫХ):
1. СПС (Собственный или арендованный вагон) при ГРУЖЁНОЙ перевозке: применяется коэффициент × 0.85 (скидка 15%).
2. МПС (Инвентарный парк): Коэффициент равен 1.00 (не указывается и не перемножается).

ПРАВИЛА ОПРЕДЕЛЕНИЯ РАССТОЯНИЙ (Приоритетно использовать матричный лист 'Distances'):
1. ИМПОРТ И ЭКСПОРТ:
   - Найди строчку с нужной внутренней станцией в столбце 'Stansiyanin_adi'.
   - Важно: Для обычных отправок бери станцию БЕЗ приписок в скобках (например, "Astara" (код 554109), а НЕ "Astara (eks.aşır)").
   - Значение расстояния бери на пересечении этой строки и столбца нужного погранперехода (Yalama_eksp, Astara_eksp, Boyuk_Kesik_eksp, Culfa_eksp, Alat_eksp_Baki_liman).
2. ТРАНЗИТ:
   - Найди строчку погранперехода отправления и перекрести со столбцом погранперехода назначения.

ПРАВИЛА МИНИМАЛЬНЫХ ТАРИФНЫХ РАССТОЯНИЙ (Minimal tarif məsafələri):
1. ИМПОРТ (İdxal): Если фактическое расстояние меньше 151 км, расчет СТРОГО берется за минимальное расстояние 151 км.
2. ЭКСПОРТ (İxrac): Если фактическое расстояние меньше 101 км, расчет СТРОГО берется за минимальное расстояние 101 км.

ОБЯЗАТЕЛЬНЫЙ ЭТАЛОННЫЙ ШАБЛОН ВЫВОДА (СОХРАНЯТЬ СТРУКТУРУ И ПОРЯДОК ФОРМУЛЫ):

1. МАРШРУТ И УСЛУГИ ПЕРЕВОЗКИ:

Станции: [Станция 1] — [Станция 2]
Вид сообщения: [Импорт / Экспорт / Транзит / Порожний возврат]
Расстояние: [Фактическое расстояние] км
Груз: Порожний подвижной состав (СПС)
Количество осей: [Количество] осей (по умолчанию 4)
Ставка за оси-км: 0.10 CHF за ось-км (п. 3.2.2)
Базовая ставка: [Расстояние × оси × 0.10] CHF

2. ПРИМЕНЕННЫЕ КОЭФФИЦИЕНТЫ И КУРС:

Курс пересчета: 1 USD = 0.79 CHF
Коэффициент ADY Express: × 1.02 (всегда в самом конце)

3. РАСЧЕТ:

СТРОГИЙ ПОРЯДОК ФОРМУЛЫ: 
Сначала базовая ставка в CHF, деление на курс 0.79, и в самом конце × 1.02!

Формула: ([Базовая ставка] CHF) / 0.79 × 1.02 = [Результат] USD

## 💰 **[Результат] USD**
"""

# 5. UI Layout
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
st.caption("ADY Tariff Calculator v2026 | Автоматический расчет тарифов и сборов")

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

# Инициализация хранилища результатов в сессии
if "calc_result" not in st.session_state:
    st.session_state.calc_result = None
if "used_model" not in st.session_state:
    st.session_state.used_model = None

# 2. Переводы интерфейса (AZ, RU, EN)
UI_TEXT = {
    "AZ": {
        "title": "🚂 ADY Dəmir Yolu Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — **{} fraxt ili**",
        "settings_header": "⚙️ Tarif tənzimləmələri",
        "year_select": "Fraxt ilini seçin:",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Ələt\nYük: Neft (YHN 2709), 60 ton\nVəziyyət: SPS çən vaqonu",
        "calc_btn": "🚀 Tarifi hesabla",
        "warning_empty": "Xahiş olunur, hesablaşma şərtlərini daxil edin.",
        "spinner": "ADY Policy {} tarifləri üzrə hesablanır...",
        "success": "Hesablama uğurla tamamlandı! (Model: {})",
        "result_title": "📋 Hesablama nəticəsi:",
        "not_found_msg": "⏳ **ADY-nin {} fraxt ili üzrə Tarif Siyasəti hələ rəsmi dərc olunmayıb.**\n\nCari hesablamalar üçün sol menyudan **{} fraxt ilini** seçməyiniz xahiş olunur. {} ili üzrə baza yeni tariflər təsdiqləndikdən dərhal sonra yüklənəcəkdir.",
        "api_warning": "⚠️ Xahiş olunur, Streamlit Secrets hissəsinə GEMINI_API_KEY əlavə edin və ya sol paneldən daxil edin.",
        "api_label": "Gemini API Key daxil edin:"
    },
    "RU": {
        "title": "🚂 Калькулятор Ж/Д Тарифов ADY",
        "subtitle": "Расчет ж/д тарифов по Азербайджану на **{} фрахтовый год**",
        "settings_header": "⚙️ Настройки тарифов",
        "year_select": "Выберите фрахтовый год:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Алят\nГруз: Нефть (ГНГ 2709), 60 тонн\nСостояние: СПС цистерна",
        "calc_btn": "🚀 Рассчитать тариф",
        "warning_empty": "Пожалуйста, введите условия расчета.",
        "spinner": "Считаем тариф согласно ADY Policy {}...",
        "success": "Расчет успешно выполнен по базе {} года! (Модель: {})",
        "result_title": "📋 Результат расчета:",
        "not_found_msg": "⏳ **Тарифная политика ADY на {} фрахтовый год пока официально не опубликована.**\n\nПожалуйста, выберите **{} фрахтовый год** в меню слева для выполнения актуальных расчетов. База данных на {} год будет загружена сразу после утверждения новых ставок ADY.",
        "api_warning": "⚠️ Пожалуйста, добавьте GEMINI_API_KEY в Secrets на Streamlit или введите его в боковой панели.",
        "api_label": "Введите Gemini API Key:"
    },
    "EN": {
        "title": "🚂 ADY Rail Tariff Calculator",
        "subtitle": "Railway freight tariff calculator for Azerbaijan — **{} freight year**",
        "settings_header": "⚙️ Tariff Settings",
        "year_select": "Select Freight Year:",
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Yalama - Alat\nCargo: Crude Oil (NHM 2709), 60 tons\nCondition: SPS tank wagon",
        "calc_btn": "🚀 Calculate Freight Rate",
        "warning_empty": "Please enter shipment requirements.",
        "spinner": "Calculating rates according to ADY Policy {}...",
        "success": "Calculation completed successfully for {} policy! (Model: {})",
        "result_title": "📋 Calculation Results:",
        "not_found_msg": "⏳ **ADY Tariff Policy for {} freight year has not been officially published yet.**\n\nPlease select **{} freight year** from the left menu to perform current calculations. The {} database will be uploaded immediately after approval of new rates.",
        "api_warning": "⚠️ Please add GEMINI_API_KEY to Streamlit Secrets or enter it in the sidebar.",
        "api_label": "Enter Gemini API Key:"
    }
}

# 3. Sidebar Language Selector
st.sidebar.header("🌐 Dil / Language")
selected_lang = st.sidebar.selectbox(
    "Dil seçin / Выберите язык / Select language:",
    options=["AZ", "RU", "EN"],
    index=0,
    format_func=lambda x: {"AZ": "Azərbaycan", "RU": "Русский", "EN": "English"}[x]
)

t = UI_TEXT[selected_lang]

# 4. Setup Gemini API Key & Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input(t["api_label"], type="password")

if not api_key:
    st.warning(t["api_warning"])
    st.stop()

client = genai.Client(api_key=api_key)

# 5. Выбор фрахтового года в Sidebar
st.sidebar.header(t["settings_header"])
selected_year = st.sidebar.selectbox(
    t["year_select"],
    options=["2026", "2027"],
    index=0
)

EXCEL_FILE = f"ADY_Tariff_Policy_{selected_year}.xlsx"

# 6. Fast Data Loading & Context Assembly
@st.cache_data(show_spinner=False)
def load_app_context(excel_path, year_label, lang):
    if not os.path.exists(excel_path):
        prev_year = str(int(year_label) - 1)
        msg = UI_TEXT[lang]["not_found_msg"].format(year_label, prev_year, year_label)
        return None, msg
    
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
            f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU = Russian, EN = English).\n"
            f"Все заголовки, имена столбцов и примечания переводи на выбранный язык ({lang})!\n"
            f"ДЛЯ АЗЕРБАЙДЖАНСКОГО ЯЗЫКА (AZ) ИСПОЛЬЗОВАТЬ ОБОЗНАЧЕНИЯ SPS (ВМЕСТО XPS) И MPS (ВМЕСТО DDP)!\n\n"
            + excel_context + "\n\n"
            + rules_text
        )
        return system_instruction, None
    except Exception as e:
        return None, f"Error processing files: {str(e)}"

SYSTEM_INSTRUCTION, err = load_app_context(EXCEL_FILE, selected_year, selected_lang)

# 7. UI Layout & Logo
logo_file = None
for filename in ["logo.png", "Logo.png", "logo.PNG", "LOGO.PNG"]:
    if os.path.exists(filename):
        logo_file = filename
        break

if logo_file:
    st.image(logo_file, width=250)

st.title(t["title"])
st.markdown(t["subtitle"].format(selected_year))

if err:
    st.info(err)
    st.stop()

st.sidebar.header(t["input_header"])

user_input = st.text_area(
    t["input_header"],
    height=180,
    placeholder=t["input_placeholder"],
    label_visibility="collapsed",
    key="user_query_input"
)

# 8. Функция чистки текста
def sanitize_text(text):
    text = re.sub(r"^\s*[\bullet\*\-]\s*Базовая ставка:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*[\bullet\*\-]\s*Провозная плата:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"(\bUSD\s+на\s+1\s+тонну|\bUSD\s+за\s+1\s+тонну|\bUSD\s+за\s+вагон)\s*\([^)]*\)", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\(При расчёте от станции.*?\)\.?", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()

# 9. Функция автоматического выбора доступных моделей Gemini
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

# 10. Кнопка расчета с сохранением состояния в session_state
if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    else:
        st.session_state.calc_result = None
        st.session_state.used_model = None
        
        with st.spinner(t["spinner"].format(selected_year)):
            try:
                prompt_text = (
                    f"Make exact calculation for (Freight Year: {selected_year}, Language: {selected_lang}):\n{user_input}\n\n"
                    f"⚠️ CRITICAL RULES (OUTPUT LANGUAGE MUST BE STRICTLY: {selected_lang}):\n"
                    "1. ABBREVIATIONS & OWNERSHIP: SPS = СПС = XPS (private wagons), MPS = МПС = DDP (railway fleet). For SPS wagons ALWAYS apply coefficient x 0.85 in calculation! For AZ language output, ALWAYS display wagon ownership as 'SPS' or 'MPS'!\n"
                    "2. STRICT MINIMUM WEIGHT NORMS CHECK (MANDATORY FOR ALL CARGOES):\n"
                    "   - ALWAYS check the cargo against the Page 11 Minimum Weight Norms table!\n"
                    "   - E.g.: Grain (1001-1008) = 60T, Coal (2701) = 60T, Ore (26) = 60T, Sugar (1701) = 60T, Flour (1101) = 60T, Fertilisers (31) = 60T, Ferrous metals (72) = 60T, Scrap (7204) = 50T, Cotton (5201) = 50T, Timber/Wood (4403, 4404, 4407) = 45T.\n"
                    "   - IF ACTUAL WEIGHT < MIN NORM, YOU ARE STRICTLY FORBIDDEN FROM USING ACTUAL WEIGHT! YOU MUST STRICTLY SELECT THE BASE RATE FROM THE COLUMN CORRESPONDING TO THE MINIMUM WEIGHT NORM!\n"
                    "3. TABLE SELECTION RULE: Select Table №3 or Table №4 based on route and direction rules from system_instruction.txt!\n"
                    "4. REFRIGERATED WAGONS & REFCARS (Table 5 & p.25-26 Rules):\n"
                    "   - Weight < 25T -> Col 2 or 4 (rate PER WAGON).\n"
                    "   - Weight >= 25T -> Col 3 or 5 (rate PER 1 TON).\n"
                    "   - Refsections composition (1 gen + 1,2,3 cars) -> apply x 1.7, x 1.4, x 1.1.\n"
                    "   - Refsections >= 5 cars -> apply x 0.85.\n"
                    "   - Fruits & Vegetables (04100, 04200, 0701-0710, 0803-0810, etc.) in refcars -> ALWAYS apply x 0.60 discount coefficient!\n"
                    "5. MINIMUM DISTANCES: Export = min 101 km (belt 101-110km), Import = min 151 km (belt 151-160km)!\n"
                    "6. SPECIAL IMPORT COEFFICIENT (1.04): For IMPORT (İdxal) shipments of Timber (NHM 4403, 4404, 4407-4413) and Ferrous Metals (72, 7301-7307), YOU MUST MULTIPLY BY x 1.04 COEFFICIENT IN THE FORMULA!\n"
                    "7. COEFFICIENT 1.50 EXCEPTIONS: Apply 1.50 for Export/Import EXCEPTIONS (DO NOT apply 1.50 for: Table 3 calculations, Timber 4403/4404/4407-4413, Ferrous metals 72/7301-7307, Methanol, and Import of Oil/Petroleum in Col 2 Table 6)!\n"
                    "8. INDEXATION COEFFICIENT (1.015): ALWAYS apply x 1.015 to ALL loaded wagon shipments! EXCEPTION: DO NOT apply 1.015 ONLY IF empty wagon return!\n"
                    "9. OUTPUT TABLES & SUMMARY MUST BE GENERATED IN THE SELECTED LANGUAGE ({selected_lang})!\n"
                    "10. FORMATTING: Section 3 MUST contain code block calculation + '📊 Final Rates' table."
                )
                
                raw_result, used_model = call_gemini_with_fallback(client, prompt_text, SYSTEM_INSTRUCTION)
                
                st.session_state.calc_result = sanitize_text(raw_result)
                st.session_state.used_model = used_model
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Отрисовка сохраненного результата
if st.session_state.calc_result:
    st.success(t["success"].format(selected_year, st.session_state.used_model))
    st.markdown(f"### {t['result_title']}")
    st.markdown(st.session_state.calc_result)

st.markdown("---")
st.caption(f"ADY Tariff Calculator | AGT CARGO | ({selected_year}) [{selected_lang}]")

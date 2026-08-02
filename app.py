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

# 3. Sidebar Language Selector (Azərbaycan, Русский, English)
st.sidebar.header("🌐 Dil / Language")
selected_lang = st.sidebar.selectbox(
    "Dil seçin / Выберите язык / Select language:",
    options=["AZ", "RU", "EN"],
    index=0,  # AZ по умолчанию
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

# 5. Выбор фрахтового года в Sidebar (По умолчанию текущий 2026 год)
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
    label_visibility="collapsed"
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

# 10. Кнопка расчета
if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    else:
        with st.spinner(t["spinner"].format(selected_year)):
            try:
                prompt_text = (
                    f"Make exact calculation for (Freight Year: {selected_year}, Language: {selected_lang}):\n{user_input}\n\n"
                    f"⚠️ CRITICAL RULES (OUTPUT LANGUAGE MUST BE STRICTLY: {selected_lang}):\n"
                    "1. ABBREVIATIONS: Treat SPS = СПС = XPS (private wagons) and MPS = МПС = DDP (railway fleet) as identical terms!\n"
                    "   - For AZ language output, ALWAYS display wagon ownership as 'SPS' or 'MPS' (DO NOT use XPS or DDP in final output)!\n"
                    "2. MINIMUM DISTANCES: Export = min 101 km (belt 101-110km), Import = min 151 km (belt 151-160km)!\n"
                    "3. CURRENCY & ADY EXPRESS: Get CHF/USD rate and % ADY Express from system_instruction.txt!\n"
                    "4. STRICT MINIMUM WEIGHT NORMS (MANDATORY CHECK FOR ALL NHM/GNG CODES):\n"
                    "   - ALWAYS check the NHM/GNG code against the minimum load norms in system_instruction.txt!\n"
                    "   - WOOD/TIMBER (GNG 4403, 4404, 4407): Minimum billable weight is STRICTLY 45 TONS! If user input is less (e.g., 35t), set Billable Weight = 45t and STRICTLY use the base rate from the 45 TONS COLUMN (14.90 CHF/t for 201-210km)!\n"
                    "   - GRAIN (GNG 1001-1008), ORE, COAL, METALS, FERTILIZERS: Minimum billable weight is STRICTLY 60 TONS (or 50t/40t/30t as per rules)!\n"
                    "5. INDEXATION COEFFICIENT (1.015):\n"
                    "   - ALWAYS apply the 1.015 coefficient to ALL loaded wagon shipments (multiply base rate / tariff by 1.015)!\n"
                    "   - EXCEPTION: DO NOT apply the 1.015 coefficient IF AND ONLY IF the shipment is an empty wagon return / repositioning!\n"
                    "6. OUTPUT TABLES & SUMMARY MUST BE GENERATED IN THE SELECTED LANGUAGE ({selected_lang})!\n"
                    "   - If selected_lang == 'AZ': Use Azerbaijani terms (Marşrut, Şərait: SPS/MPS, Xalis dəmir yolu tarifi, ADY Express daxil yekun tarif, etc.)\n"
                    "   - If selected_lang == 'RU': Use Russian terms (Маршрут, Состояние: СПС/МПС, Чистый ж/д тариф ADY, Итоговая ставка, etc.)\n"
                    "   - If selected_lang == 'EN': Use English terms (Route, Conditions: SPS/MPS, Net ADY Rail Tariff, Final rate with ADY Express, etc.)\n"
                    "7. FORMATTING: Section 3 MUST contain code block calculation + '📊 Final Rates' table."
                )
                
                raw_result, used_model = call_gemini_with_fallback(client, prompt_text, SYSTEM_INSTRUCTION)
                clean_result = sanitize_text(raw_result)
                
                st.success(t["success"].format(selected_year, used_model))
                st.markdown(f"### {t['result_title']}")
                st.markdown(clean_result)
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption(f"ADY Tariff Calculator | AGT CARGO | ({selected_year}) [{selected_lang}]")

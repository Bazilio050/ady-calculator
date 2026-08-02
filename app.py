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
        "input_placeholder": "Nümunə:\nMarşrut: Bakı yük - Yalama\nYük: Neft (YHN 2709), 50 ton\nVəziyyət: SPS çən vaqonu",
        "calc_btn": "🚀 Tarifi hesabla",
        "warning_empty": "Xahiş olunur, hesablaşma şərtlərini daxil edin.",
        "spinner": "ADY Policy {} tarifləri üzrə hesablanır...",
        "success": "Hesablama uğurla tamamlandı! (Model: {})",
        "result_title": "📋 Hesablama nəticəsi:",
        "not_found_msg": "⏳ **ADY-nin {} fraxt ili üzrə Tarif Siyasəti hələ rəsmi dərc olunmayıb.**\n\nCari hesablamalar üçün sol menyudan **{} fraxt ilini** seçməyiniz xahiş olunur.",
        "api_warning": "⚠️ Xahiş olunur, Streamlit Secrets hissəsinə GEMINI_API_KEY əlavə edin və ya sol paneldən daxil edin.",
        "api_label": "Gemini API Key daxil edin:"
    },
    "RU": {
        "title": "🚂 Калькулятор Ж/Д Тарифов ADY",
        "subtitle": "Расчет ж/д тарифов по Азербайджану на **{} фрахтовый год**",
        "settings_header": "⚙️ Настройки тарифов",
        "year_select": "Выберите фрахтовый год:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Баку тов - Ялама\nГруз: Нефть (ГНГ 2709), 50 тонн\nСостояние: СПС цистерна",
        "calc_btn": "🚀 Рассчитать тариф",
        "warning_empty": "Пожалуйста, введите условия расчета.",
        "spinner": "Считаем тариф согласно ADY Policy {}...",
        "success": "Расчет успешно выполнен по базе {} года! (Модель: {})",
        "result_title": "📋 Результат расчета:",
        "not_found_msg": "⏳ **Тарифная политика ADY на {} фрахтовый год пока официально не опубликована.**\n\nПожалуйста, выберите **{} фрахтовый год** в меню слева.",
        "api_warning": "⚠️ Пожалуйста, добавьте GEMINI_API_KEY в Secrets на Streamlit или введите его в боковой панели.",
        "api_label": "Введите Gemini API Key:"
    },
    "EN": {
        "title": "🚂 ADY Rail Tariff Calculator",
        "subtitle": "Railway freight tariff calculator for Azerbaijan — **{} freight year**",
        "settings_header": "⚙️ Tariff Settings",
        "year_select": "Select Freight Year:",
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Baku tovar - Yalama\nCargo: Crude Oil (NHM 2709), 50 tons\nCondition: SPS tank wagon",
        "calc_btn": "🚀 Calculate Freight Rate",
        "warning_empty": "Please enter shipment requirements.",
        "spinner": "Calculating rates according to ADY Policy {}...",
        "success": "Calculation completed successfully for {} policy! (Model: {})",
        "result_title": "📋 Calculation Results:",
        "not_found_msg": "⏳ **ADY Tariff Policy for {} freight year has not been officially published yet.**\n\nPlease select **{} freight year** from the left menu.",
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

# 6. УМНАЯ СЕЛЕКТИВНАЯ ЗАГРУЗКА ИЗ ТЕКСТОВЫХ ФАЙЛОВ И EXCEL
@st.cache_data(show_spinner=False)
def load_selective_context(user_query, year_label, lang):
    query_lower = user_query.lower()
    files_to_load = ["system_instruction.txt", "Weight_Categories.txt", "GNG_Column_Mapping.txt"]

    # Автоподгрузка нужной таблицы ставок по ключевым словам
    if any(k in query_lower for k in ["цистерн", "çən", "tank", "нефть", "neft", "газ", "qaz", "масло", "спирт", "2709", "2710"]):
        for f_name in ["Table_6_Tanks.txt", "Table6.txt", "Cədvəl6.txt", "Cadval_6.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    elif any(k in query_lower for k in ["реф", "ref", "термос", "termos", "автовоз", "автопоезд", "контейнер"]):
        for f_name in ["Table_5_Reef.txt", "Table5.txt", "Cədvəl5.txt", "Cadval_5.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    else:
        for f_name in ["Table_3_4_Universal.txt", "Table3.txt", "Table4.txt", "Cədvəl3.txt", "Cədvəl4.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)

    # Загрузка файла расстояний
    for dist_file in ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]:
        if os.path.exists(dist_file):
            files_to_load.append(dist_file)
            break

    loaded_rules = []
    for txt_file in set(files_to_load):
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                loaded_rules.append(f"--- РАЗДЕЛ БАЗЫ: {txt_file} ---\n" + f.read())

    # Резервная загрузка из Excel, если специальные txt-файлы таблиц отсутствуют
    excel_path = f"ADY_Tariff_Policy_{year_label}.xlsx"
    excel_context = ""
    if not loaded_rules and os.path.exists(excel_path):
        xls = pd.ExcelFile(excel_path)
        summary_text = []
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            summary_text.append(f"--- ТАБЛИЦА: {sheet} ---")
            summary_text.append(df.to_string(index=False))
        excel_context = "\n".join(summary_text)

    rules_text = "\n\n".join(loaded_rules)
    
    system_instruction = (
        f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ ГОД!\n"
        f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU = Russian, EN = English).\n"
        f"Все заголовки, имена столбцов и примечания переводи на выбранный язык ({lang})!\n"
        f"ДЛЯ АЗЕРБАЙДЖАНСКОГО ЯЗЫКА (AZ) ИСПОЛЬЗОВАТЬ ОБОЗНАЧЕНИЯ SPS (ВМЕСТО XPS) И MPS (ВМЕСТО DDP)!\n\n"
        + rules_text + "\n\n" + excel_context
    )
    return system_instruction

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

# 9. Функция автовыбора доступных моделей Gemini (Проверенный рабочий вариант)
def call_gemini_with_fallback(client, prompt, instruction):
    candidate_models = ["gemini-1.5-flash"]
    
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
                dyn_instruction = load_selective_context(user_input, selected_year, selected_lang)
                
                prompt_text = (
                    f"Make exact calculation for (Freight Year: {selected_year}, Language: {selected_lang}):\n{user_input}\n\n"
                    f"⚠️ CRITICAL UNITS OF MEASUREMENT RULE:\n"
                    "- FOR LOADED TONNAGE SHIPMENTS: Output rates strictly PER 1 TON (USD/t)! DO NOT display per wagon rates.\n"
                    "- FOR EMPTY WAGON RETURNS (SPS 0.10 CHF/axle-km), CAR TRANSPORTERS (Table 5 col 6), OR FIXED PER-WAGON RATES: Output rates strictly PER 1 WAGON (USD/wagon)!\n\n"
                    f"⚠️ CRITICAL RULES (OUTPUT LANGUAGE MUST BE STRICTLY: {selected_lang}):\n"
                    "1. ABBREVIATIONS: Treat SPS = СПС = XPS (private wagons) and MPS = МПС = DDP (railway fleet) as identical terms!\n"
                    "   - For AZ language output, ALWAYS display wagon ownership as 'SPS' or 'MPS' (DO NOT use XPS or DDP in final output)!\n"
                    "2. STRICT ROUTE DISTANCES:\n"
                    "   - Bakı yük / Bakı tovar / Baku tovar / Absheron to Yalama = EXACTLY 204 KM! (NEVER USE 212 KM)!\n"
                    "   - ALWAYS USE EXACT DISTANCES FROM EXCEL/TXT 'Məsafə' / 'Distance' TABLES! DO NOT ESTIMATE DISTANCES!\n"
                    "   - Minimum distances: Export = min 101 km (belt 101-110km), Import = min 151 km (belt 151-160km)!\n"
                    "3. SPECIAL WAGONS & PASSENGER WAGONS (Clauses 3.1.2.5 - 3.1.2.8):\n"
                    "   - Passenger/Mail wagons (GNG 99910000): Billable weight strictly = 66 TONS (no Table 2 multipliers). Take base rate from 25 tons BTT category (Table 7 col 6)!\n"
                    "   - Transporters: min 5 tons/axle (4 axles = min 20t, 6 axles = min 30t, 8 axles = min 40t)!\n"
                    "   - Empty SPS container platform return (axle distance > 19m): Apply 0.60 multiplier to axle-km rate (0.06 CHF / axle-km)!\n"
                    "   - Other special wagons (3.1.2.8): Calculate using universal wagon Tables 3 & 4!\n"
                    "4. GNG CODE MAPPING (GNG_Column_Mapping.txt & Clause 3.1.2.4):\n"
                    "   - STRICTLY use 'GNG_Column_Mapping.txt' to determine the exact Table 6 column for tank shipments and specific cargo coefficients!\n"
                    "   - Base rate for liquid cargo in tanks MUST be taken from the 25 TONS weight category column (Rule 2 / Qayda 2)!\n"
                    "5. PRIVATE WAGONS (SPS / Özəl vaqonlar, Section 3.2):\n"
                    "   - Loaded SPS wagons: Apply x0.85 coefficient (Except Col 8 special tanks where x0.70 applies).\n"
                    "   - Empty SPS wagon return: Calculate per axle-km: 0.10 CHF / axle-km (4 axles * distance_km * 0.10 CHF) (Clause 3.2.2)! FOR EXPORT AND IMPORT SHIPMENTS, ALWAYS APPLY THE 1.50 COEFFICIENT TO THIS CALCULATION ((4 axles * distance * 0.10 CHF) * 1.50)!\n"
                    "6. REFRIGERATED WAGONS & REF SECTIONS (TABLE 5):\n"
                    "   - Recognize terms: 'рефвагон', 'рефсекция', 'вагонреф', 'АРВ', 'ref', '1+1', '1+2', '1+3', '1+4', '1+5', '1+6', '2+1', '3+1', '4+1', '5+1', '6+1' etc.\n"
                    "   - SECTION COEFFICIENTS: [1+1] = x1.70, [1+2] / [2+1] = x1.40, [1+3] / [3+1] = x1.10, [1+4] / [4+1] = x1.00, [1+5] / [5+1] or more = x0.85 (ALWAYS APPLY x0.85 for 5+ wagon ref section)!\n"
                    "7. SPECIAL COEFFICIENTS (1.04 / 1.20 / 1.50 / 0.80):\n"
                    "   - IMPORT OF WOOD (GNG 4403, 4404, 4407-4413) AND BLACK METALS (GNG Ch.72, 7301-7307): MUST APPLY EXTRA COEFFICIENT × 1.04!\n"
                    "   - TRANSIT ALAT - BOYUK KASIK: Apply coefficient × 1.20!\n"
                    "   - TRANSIT/IMPORT OIL IN TANKS & ARV/REF TRANSIT: Apply ONLY coefficient × 1.20!\n"
                    "   - COEFFICIENT 1.50: ALWAYS APPLY TO ALL EXPORT AND IMPORT SHIPMENTS (LOADED AND EMPTY WAGONS), EXCEPT Table 3 rates, wood in universal wagons (4403-4413), black metals (72, 7301-7307), methanol, and oil/petroleum in Table 6 Col 2 (import/export)!\n"
                    "8. STRICT MINIMUM WEIGHT NORMS FOR LOADED WAGONS:\n"
                    "   - WOOD/TIMBER (GNG 4403, 4404, 4407-4413): Billable weight = min 45 TONS! Always take base rate from 45 TONS COLUMN!\n"
                    "   - CAR TRANSPORTERS (Table 5, Col 6): Billable weight = min 10 TONS!\n"
                    "9. OUTPUT TABLES & SUMMARY MUST BE GENERATED IN THE SELECTED LANGUAGE ({selected_lang})!\n"
                    "10. FORMATTING: Section 3 MUST contain code block calculation + '📊 Final Rates' table."
                )
                
                raw_result, used_model = call_gemini_with_fallback(client, prompt_text, dyn_instruction)
                clean_result = sanitize_text(raw_result)
                
                st.success(t["success"].format(selected_year, used_model))
                st.markdown(f"### {t['result_title']}")
                st.markdown(clean_result)
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption(f"ADY Tariff Calculator | AGT CARGO | ({selected_year}) [{selected_lang}]")

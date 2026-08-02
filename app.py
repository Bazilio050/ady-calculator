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
        "success": "Hesablama tamamlandı!",
        "result_title": "📋 Hesablama nəticəsi:",
        "not_found_msg": "⏳ **ADY-nin {} fraxt ili üzrə Tarif Siyasəti hələ rəsmi dərc olunmayıb.**",
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
        "success": "Расчет выполнен!",
        "result_title": "📋 Результат расчета:",
        "not_found_msg": "⏳ **Тарифная политика ADY на {} фрахтовый год пока официально не опубликована.**",
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
        "success": "Calculation completed!",
        "result_title": "📋 Calculation Results:",
        "not_found_msg": "⏳ **ADY Tariff Policy for {} freight year has not been officially published yet.**",
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

# 6. БЫСТРАЯ СЕЛЕКТИВНАЯ ЗАГРУЗКА ИЗ ТЕКСТОВЫХ ФАЙЛОВ
@st.cache_data(show_spinner=False)
def load_selective_context(user_query, year_label, lang):
    query_lower = user_query.lower()
    files_to_load = ["system_instruction.txt", "Weight_Categories.txt", "GNG_Column_Mapping.txt"]

    # Автоопределение только нужной таблицы
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

    for dist_file in ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]:
        if os.path.exists(dist_file):
            files_to_load.append(dist_file)
            break

    loaded_rules = []
    for txt_file in set(files_to_load):
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                loaded_rules.append(f"--- {txt_file} ---\n" + f.read())

    rules_text = "\n\n".join(loaded_rules)
    
    system_instruction = (
        f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ ГОД!\n"
        f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU = Russian, EN = English).\n"
        f"ДЛЯ АЗЕРБАЙДЖАНСКОГО ЯЗЫКА (AZ) ИСПОЛЬЗОВАТЬ ОБОЗНАЧЕНИЯ SPS И MPS!\n\n"
        + rules_text
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

# 8. Кнопка расчета С ПОТОКОВЫМ ВЫВОДОМ (STREAMING)
if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    else:
        try:
            dyn_instruction = load_selective_context(user_input, selected_year, selected_lang)
            
            prompt_text = (
                f"Make exact calculation for (Freight Year: {selected_year}, Language: {selected_lang}):\n{user_input}\n\n"
                f"⚠️ CRITICAL UNITS RULE:\n"
                "- FOR LOADED TONNAGE SHIPMENTS: Output rates strictly PER 1 TON (USD/t)! DO NOT display per wagon rates.\n"
                "- FOR EMPTY WAGON RETURNS (SPS 0.10 CHF/axle-km), CAR TRANSPORTERS (Table 5 col 6), OR FIX PER-WAGON RATES: Output rates strictly PER 1 WAGON (USD/wagon)!\n\n"
                f"⚠️ CRITICAL RULES (OUTPUT LANGUAGE MUST BE STRICTLY: {selected_lang}):\n"
                "1. ABBREVIATIONS: Treat SPS = СПС = XPS and MPS = МПС = DDP as identical terms. For AZ, ALWAYS use SPS/MPS.\n"
                "2. STRICT ROUTE DISTANCES: Bakı yük / Baku tovar to Yalama = EXACTLY 204 KM! Export min 101 km, Import min 151 km.\n"
                "3. SPECIAL WAGONS: Passenger/Mail wagons (99910000) billable weight = 66 TONS. Transporters: min 5 t/axle.\n"
                "4. GNG CODE MAPPING: Use GNG_Column_Mapping.txt for Table 6 columns. Tank base rate = 25 TONS column.\n"
                "5. PRIVATE WAGONS (SPS): Loaded SPS = x0.85 (Except Col 8 special tanks = x0.70). Empty SPS return = 0.10 CHF/axle-km * 1.50 for export/import.\n"
                "6. REFRIGERATED WAGONS: 5+ wagons section = x0.85.\n"
                "7. SPECIAL COEFFICIENTS: Import wood/metals = x1.04. Transit Alat-Boyuk Kasik = x1.20. Coef 1.50 applies to all export/import except exceptions.\n"
                "8. OUTPUT FORMAT: Section 3 MUST contain code block calculation + '📊 Final Rates' table."
            )
            
            st.markdown(f"### {t['result_title']}")
            
            # Потоковый генератор (Ответ мгновенно печатается на экране)
            response_stream = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt_text,
                config={"system_instruction": dyn_instruction}
            )
            
            st.write_stream(chunk.text for chunk in response_stream)
            st.success(t["success"])
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption(f"ADY Tariff Calculator | AGT CARGO | ({selected_year}) [{selected_lang}]")

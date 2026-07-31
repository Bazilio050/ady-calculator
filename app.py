import os
import re
import json
import requests
import pandas as pd
import streamlit as st

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
        "title": "🚂 ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — **{} fraxt ili**",
        "settings_header": "⚙️ Tarif tənzimləmələri",
        "year_select": "Fraxt ilini seçin:",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Ələt\nYük: Neft (YHN 2709), 60 ton\nVəziyyət: SPS çən vaqonu",
        "calc_btn": "🚀 Tarifi hesabla",
        "warning_empty": "Xahiş olunur, hesablaşma şəraitini daxil edin.",
        "spinner": "ADY Policy {} tarifləri üzrə hesablanır...",
        "success": "Hesablama uğurla tamamlandı! (Model: {})",
        "result_title": "📋 Hesablama nəticəsi:",
        "api_warning": "⚠️ API Key Streamlit Secrets bölməsində tapılmadı."
    },
    "RU": {
        "title": "🚂 Калькулятор тарифов ADY",
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
        "api_warning": "⚠️ API Key не найден в Streamlit Secrets."
    },
    "EN": {
        "title": "🚂 ADY Tariff Calculator",
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
        "api_warning": "⚠️ API Key not found in Streamlit Secrets."
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

# Ключ берётся строго из Secrets / Environment
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error(t["api_warning"])
    st.stop()

# 4. Выбор фрахтового года в Sidebar
st.sidebar.header(t["settings_header"])
selected_year = st.sidebar.selectbox(
    t["year_select"],
    options=["2026", "2027"],
    index=0
)

# 5. Легкая сборка правил без перегруза API
@st.cache_data(show_spinner=False)
def load_light_rules(year_label, lang):
    additional_rules = []
    txt_files = ["system_instruction.txt", "Weight_Categories.txt"]
    
    for txt_file in txt_files:
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                additional_rules.append(f.read())

    rules_text = "\n\n".join(additional_rules)

    system_instruction = (
        f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ ГОД!\n"
        f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU = Russian, EN = English).\n"
        f"Все заголовки и названия переводи на выбранный язык ({lang})!\n"
        f"ДЛЯ АЗЕРБАЙДЖАНСКОГО ЯЗЫКА (AZ) ИСПОЛЬЗОВАТЬ ОБОЗНАЧЕНИЯ SPS (ВМЕСТО XPS) И MPS (ВМЕСТО DDP)!\n\n"
        + rules_text
    )
    return system_instruction

SYSTEM_INSTRUCTION = load_light_rules(selected_year, selected_lang)

# 6. UI Layout & Logo
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
    label_visibility="collapsed",
    key="user_query_input"
)

# 7. Функция чистки текста
def sanitize_text(text):
    text = re.sub(r"^\s*[\bullet\*\-]\s*Базовая ставка:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*[\bullet\*\-]\s*Провозная плата:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"(\bUSD\s+на\s+1\s+тонну|\bUSD\s+за\s+1\s+тонну|\bUSD\s+за\s+вагон)\s*\([^)]*\)", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\(При расчёте от станции.*?\)\.?", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()

# 8. Быстрый и прямой REST-вызов по точным именам моделей
def call_gemini_direct(prompt, instruction, key):
    candidate_models = [
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro"
    ]
    
    errors = []
    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": instruction}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                text_out = data['candidates'][0]['content']['parts'][0]['text']
                return text_out, model_name
            else:
                errors.append(f"{model_name} (Status {res.status_code}): {res.text}")
        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")

    raise RuntimeError("Ошибка при вызове Google API:\n\n" + "\n\n".join(errors))

# 9. Кнопка расчета
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
                    "0. DO NOT OUTPUT YOUR INTERNAL REASONING, THINKING PROCESS OR DRAFTS. Start immediately with Section 1 markdown tables!\n"
                    "1. ABBREVIATIONS & OWNERSHIP: SPS = СПС = XPS (private wagons), MPS = МПС = DDP (railway fleet). For SPS wagons ALWAYS apply x 0.85!\n"
                    "2. STRICT MINIMUM WEIGHT NORMS: Always check Page 11 norms (Grain 60T, Coal 60T, Ore 60T, Sugar 60T, Flour 60T, Fertilisers 60T, Scrap 50T, Cotton 50T, Timber 45T). If actual weight < min norm, strictly use MIN NORM column!\n"
                    "3. REFRIGERATED WAGONS: Weight < 25T -> Col 2/4 (per wagon), Weight >= 25T -> Col 3/5 (per ton). Fruits/Veg discount = x 0.60.\n"
                    "4. MINIMUM DISTANCES: Export = min 101 km, Import = min 151 km!\n"
                    "5. SPECIAL IMPORT COEFFICIENT (1.04): For IMPORT of Timber (4403, 4404, 4407) and Ferrous Metals (72), apply x 1.04!\n"
                    "6. COEFFICIENT 1.50 EXCEPTIONS: Do NOT apply 1.50 for Table 3, Timber, Ferrous metals, Methanol, Import Oil Col 2 Table 6.\n"
                    "7. INDEXATION (1.015): Apply x 1.015 to ALL loaded wagons.\n"
                    "8. FORMATTING: Section 3 MUST contain code block calculation + '📊 Final Rates' table."
                )
                
                raw_result, used_model = call_gemini_direct(prompt_text, SYSTEM_INSTRUCTION, api_key)
                
                st.session_state.calc_result = sanitize_text(raw_result)
                st.session_state.used_model = used_model
                
            except Exception as e:
                st.error(f"{str(e)}")

# Отрисовка результата
if st.session_state.calc_result:
    st.success(t["success"].format(selected_year, st.session_state.used_model))
    st.markdown(f"### {t['result_title']}")
    st.markdown(st.session_state.calc_result)

st.markdown("---")
st.caption(f"ADY Tariff Calculator | AGT CARGO | ({selected_year}) [{selected_lang}]")

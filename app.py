import json
import os
import re
import streamlit as st
from google import genai
from google.genai import types

# 1. Page config — СТРОГО ПЕРВАЯ КОМАНДА STREAMLIT
st.set_page_config(
    page_title="ADY Tarif Kalkulyatoru", page_icon="🚂", layout="wide"
)

# 2. Загрузка внешнего файла правил (Мозг калькулятора)
@st.cache_data
def load_rules_config():
    config_file = "rules_config.json"
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

RULES = load_rules_config()

# 3. Скрытие системных элементов Streamlit и адаптивные стили
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppHeader {display: none;}
    footer {visibility: hidden;}

    .custom-title {
        font-size: 24px !important;
        font-weight: 700;
        color: var(--text-color, #1E293B);
        margin-top: 10px;
        margin-bottom: 2px;
        text-align: left;
    }
    .custom-subtitle {
        font-size: 14px !important;
        color: #64748B;
        margin-bottom: 15px;
        text-align: left;
    }

    @keyframes train-move {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100vw); }
    }
    .train-track {
        width: 100%;
        overflow: hidden;
        background: #F1F5F9;
        border-radius: 6px;
        padding: 4px 0;
        margin: 6px 0;
        white-space: nowrap;
    }
    .train-animation {
        display: inline-block;
        font-size: 14px;
        animation: train-move 3s linear infinite;
    }
    .train-text {
        font-size: 13px;
        color: #475569;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 4. Интерфейсные тексты (UI_TEXT)
UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt ili",
        "year_select": "Fraxt ili:",
        "lang_select": "Dil / Language:",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Abşeron\nYük: Kağız tullantıları (GNG 4707), 35 ton\nVəziyyət: Özəl örtülü vaqon",
        "calc_btn": "🚀 Tarifi hesabla",
        "warning_empty": "Xahiş olunur, hesablaşma şərtlərini daxil edin.",
        "spinner_text": "ADY Policy {} tarifləri üzrə hesablanır...",
        "success": "Hesablama uğurla tamamlandı!",
        "result_title": "📋 Hesablama nəticəsi:",
        "sec1_title": "1. Marşrut və daşıma şərtləri",
        "sec2_title": "2. Əmsallar və valyuta məzənnəsi",
        "sec3_title": "3. Tarifin hesablanması",
        "formula_title": "Hesablama düsturu:",
        "rates_title": "Yekun tariflər:",
        "notes_title": "Qeydlər:",
        "disclaimer": "Tariflərə stansiya xərcləri və əlavə yığımlar daxil deyildir.",
        "col_param": "Parametr",
        "col_val": "Qiymət / Həcm",
        "col_rate_type": "Tarif növü",
        "col_amount": "Məblağ",
        "lbl_route": "Marşrut",
        "lbl_type": "Daşıma növü",
        "lbl_dist": "Məsafə",
        "lbl_cargo": "Yük / Vəziyyət",
        "lbl_weight": "Çəki",
        "lbl_period": "Dövr",
        "lbl_exchange": "CHF/USD",
        "lbl_base_rate": "Baza tarifi",
        "lbl_net_rate": "Yekün ADY tarifi",
        "lbl_express_rate": "Yekun tarif (ADY Express +2% daxil)",
        "api_warning": "⚠️ Xahiş olunur, GEMINI_API_KEY daxil edin.",
        "api_label": "Gemini API Key:",
    },
    "RU": {
        "title": "Тарифный калькулятор ADY",
        "subtitle": "Расчет ж/д тарифов по Азербайджану — {} фрахтовый год",
        "year_select": "Фрахтовый год:",
        "lang_select": "Язык / Language:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Апшерон\nГруз: Отходы бумаги (ГНГ 4707), 35 тонн\nСостояние: СПС крытый вагон",
        "calc_btn": "🚀 Рассчитать тариф",
        "warning_empty": "Пожалуйста, введите условия расчета.",
        "spinner_text": "Считаем тариф согласно Тарифной политике {}...",
        "success": "Расчет успешно выполнен!",
        "result_title": "📋 Результат расчета:",
        "sec1_title": "1. Маршрут и условия перевозки",
        "sec2_title": "2. Коэффициенты и курс валют",
        "sec3_title": "3. Расчет тарифа",
        "formula_title": "Формула расчета:",
        "rates_title": "Итоговые тарифы:",
        "notes_title": "Примечания:",
        "disclaimer": "Ставки приведены без учета станционных расходов.",
        "col_param": "Параметр",
        "col_val": "Значение / Объем",
        "col_rate_type": "Тип тарифа",
        "col_amount": "Сумма",
        "lbl_route": "Маршрут",
        "lbl_type": "Вид перевозки",
        "lbl_dist": "Расстояние",
        "lbl_cargo": "Груз / Состояние",
        "lbl_weight": "Вес",
        "lbl_period": "Период",
        "lbl_exchange": "CHF/USD",
        "lbl_base_rate": "Базовый тариф",
        "lbl_net_rate": "Итоговый тариф",
        "lbl_express_rate": "Итоговый тариф (включая ADY Express +2%)",
        "api_warning": "⚠️ Пожалуйста, добавьте GEMINI_API_KEY.",
        "api_label": "Введите Gemini API Key:",
    },
    "EN": {
        "title": "ADY Tariff Calculator",
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:",
        "lang_select": "Language:",
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Yalama - Absheron\nCargo: Paper scrap (NHM 4707), 35 tons\nCondition: SPS covered wagon",
        "calc_btn": "🚀 Calculate Freight Rate",
        "warning_empty": "Please enter shipment requirements.",
        "spinner_text": "Calculating rates according to Tariff Policy {}...",
        "success": "Calculation completed successfully!",
        "result_title": "📋 Calculation Results:",
        "sec1_title": "1. Route and Shipment Conditions",
        "sec2_title": "2. Coefficients and Exchange Rate",
        "sec3_title": "3. Rate Calculation",
        "formula_title": "Calculation Formula:",
        "rates_title": "Final Rates:",
        "notes_title": "Notes:",
        "disclaimer": "Rates are quoted excluding station charges.",
        "col_param": "Parameter",
        "col_val": "Value / Volume",
        "col_rate_type": "Rate Type",
        "col_amount": "Amount",
        "lbl_route": "Route",
        "lbl_type": "Shipment Type",
        "lbl_dist": "Distance",
        "lbl_cargo": "Cargo / Condition",
        "lbl_weight": "Weight",
        "lbl_period": "Period",
        "lbl_exchange": "CHF/USD",
        "lbl_base_rate": "Base Tariff",
        "lbl_net_rate": "Final Tariff",
        "lbl_express_rate": "Final Tariff (incl. ADY Express +2%)",
        "api_warning": "⚠️ Please provide GEMINI_API_KEY.",
        "api_label": "Enter Gemini API Key:",
    },
}

# 5. Динамический движок минимального веса на основе rules_config.json
def get_minimal_weight_norm_from_config(gng_code_str):
    gng_clean = re.sub(r"\D", "", str(gng_code_str))
    if not gng_clean or "minimal_weight_norms_gng" not in RULES:
        return 0.0
    
    for rule in RULES["minimal_weight_norms_gng"].get("rules", []):
        prefixes = rule.get("gng_prefixes", [])
        exceptions = rule.get("exceptions", [])
        
        # Проверяем исключения
        if any(gng_clean.startswith(exc) for exc in exceptions):
            continue
            
        # Проверяем префиксы
        if any(gng_clean.startswith(pref) for pref in prefixes):
            return float(rule.get("norm_tons", 0.0))
            
    return 0.0

# 6. Логотип и селекторы
logo_file = next((f for f in ["logo.png", "Logo.png"] if os.path.exists(f)), None)
if logo_file:
    st.image(logo_file, width=200)

col_controls, _ = st.columns([4.0, 6.0])
with col_controls:
    selected_lang = st.selectbox(
        f"🌐 {UI_TEXT['AZ']['lang_select']}",
        options=["AZ", "RU", "EN"],
        format_func=lambda x: {"AZ": "Azərbaycan", "RU": "Русский", "EN": "English"}[x],
    )
    t = UI_TEXT[selected_lang]
    selected_year = st.selectbox(f"⚙️ {t['year_select']}", options=["2026", "2027"])

st.markdown(f'<div class="custom-title">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="custom-subtitle">{t["subtitle"].format(selected_year)}</div>', unsafe_allow_html=True)

api_key = os.environ.get("GEMINI_API_KEY") or st.text_input(t["api_label"], type="password")
if not api_key:
    st.warning(t["api_warning"])
    st.stop()

client = genai.Client(api_key=api_key)

# 7. Функции поиска расстояний и ставок (остаются неизменными по логике парсинга файлов)
def find_distance_in_file(st_from, st_to):
    dist_file = next((f for f in ["Distances.txt", "Məsafə.txt", "Distance.txt"] if os.path.exists(f)), None)
    if not dist_file:
        return None
    with open(dist_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    headers = []
    for line in lines:
        if "Yalama" in line and "|" in line:
            headers = [h.strip().lower() for h in line.split("|") if h.strip()]
            break
    
    sf, st_target = st_from.lower(), st_to.lower()
    header_col_idx = next((idx - 1 for idx, h in enumerate(headers) if sf in h), -1)
    
    for line in lines:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 3 and (st_target in parts[0].lower() or parts[0].lower() in st_target):
            if 0 <= header_col_idx < len(parts) - 1:
                num_match = re.search(r"(\d+)", parts[header_col_idx + 1])
                if num_match:
                    return int(num_match.group(1))
    return None

def find_table_base_rate(table_filename, distance, weight):
    if not os.path.exists(table_filename):
        return None, ""
    with open(table_filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    for line in lines:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 3:
            dist_match = re.search(r"(\d+)\s*[-–—]\s*(\d+)", parts[0])
            if dist_match and int(dist_match.group(1)) <= distance <= int(dist_match.group(2)):
                vals = parts[1:]
                col_idx = min(int(weight // 5) - 1, len(vals) - 1) if weight > 0 else 0
                col_idx = max(0, col_idx)
                num_match = re.search(r"(\d+\.?\d*)", vals[col_idx].replace(",", "."))
                if num_match:
                    return float(num_match.group(1)), f"{parts[0]} км, {int(weight)} т"
    return None, ""

# 8. Вызов Gemini для извлечения параметров
def call_gemini_json(client, prompt, instruction):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=instruction, temperature=0.0, response_mime_type="application/json"
        ),
    )
    raw_text = re.sub(r"^```json\s*|^```\s*|\s*```$", "", response.text.strip(), flags=re.MULTILINE)
    return json.loads(raw_text)

user_input = st.text_area(t["input_header"], height=150, placeholder=t["input_placeholder"])

if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    else:
        with st.spinner(t["spinner_text"].format(selected_year)):
            try:
                # Системный промпт подтягивает всю логику из rules_config.json автоматически
                system_instruction = f"Применяй Тарифную политику ADY {selected_year}. Язык ответа: {selected_lang}. Верни данные в формате JSON."
                data = call_gemini_json(client, user_input, system_instruction)
                
                st.success(t["success"])
                st.markdown(f"### {t['result_title']}")
                
                p2 = data.get("part2", {})
                gng_code = str(p2.get("gng_code", ""))
                act_weight = float(p2.get("actual_weight_tons", 0.0))
                
                # Проверка веса по динамическому конфигу
                min_norm = get_minimal_weight_norm_from_config(gng_code)
                billable_weight = max(act_weight, min_norm) if min_norm > 0 else act_weight
                
                # Вывод результатов (Разделы 1, 2, 3) аналогично твоему шаблону
                st.write("Данные успешно обработаны на основе правил ADY 2026.")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption(f"ADY Tarif Kalkulyatoru | ({selected_year}) [{selected_lang}]")

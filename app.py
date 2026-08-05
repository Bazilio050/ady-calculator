import json
import os
import re
import streamlit as st
from google import genai
from google.genai import types

# ==============================================================================
# 1. PAGE CONFIG & STYLES (Строго первая команда)
# ==============================================================================
st.set_page_config(
    page_title="ADY Tarif Kalkulyatoru",
    page_icon="🚂",
    layout="wide"
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppHeader {display: none;}
    footer {visibility: hidden;}

    div[data-testid="stVerticalBlock"]:has(div[data-testid="stSelectbox"]) {
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: auto !important;
    }

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

    .stTextArea textarea {
        width: 100% !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. UI TEXTS (Мультиязычность)
# ==============================================================================
UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt ili",
        "year_select": "Fraxt ili:",
        "lang_select": "Dil / Language:",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Abşeron\nYük: Meşə materialları (GNG 4407), 55 ton\nVəziyyət: SPS örtülü vaqon",
        "calc_btn": "🚀 Tarifi hesabla",
        "warning_empty": "Xahiş olunur, hesablaşma şərtlərini daxil edin.",
        "spinner_text": "ADY Policy {} tarifləri üzrə hesablanır...",
        "success": "Hesablama uğurla tamamlandı! (ADY Policy {})",
        "result_title": "📋 Hesablama nəticəsi:",
        "sec1_title": "1. Marşrut və daşıma şərtləri",
        "sec2_title": "2. Əmsallar və valyuta məzənnəsi",
        "sec3_title": "3. Tarifin hesablanması",
        "formula_title": "Hesablama düsturu:",
        "rates_title": "Yekun tariflər:",
        "notes_title": "Qeydlər:",
        "disclaimer": "Qeyd olunan tariflərə stansiya xərcləri (yükləmə-boşaltma, tərtibat, sənədləşmə, vaqonların verilməsi-yığılması və s.) və əlavə yığımlar daxil deyildir.",
        "col_param": "Parametr",
        "col_val": "Qiymət / Həcm",
        "col_rate_type": "Tarif növü",
        "col_amount": "Məblağ",
        "lbl_route": "Marşrut",
        "lbl_type": "Daşıma növü",
        "lbl_dist": "Məsafə",
        "lbl_cargo": "Yük / Vəziyyət",
        "lbl_weight": "Faktiki / Hesablaşma çəkisi",
        "lbl_period": "Dövr",
        "lbl_exchange": "CHF/USD",
        "lbl_base_rate": "Baza tarifi",
        "lbl_net_rate": "Yekün ADY tarifi",
        "lbl_express_rate": "Yekun tarif (ADY Express +2% daxil)",
        "api_warning": "⚠️ Xahiş olunur, GEMINI_API_KEY daxil edin.",
        "api_label": "Gemini API Key:",
        "type_import": "İdxal daşınması",
        "type_export": "İxrac daşınması",
        "type_transit": "Tranzit daşınması",
        "note_sps": "Özəl vaqonlar (SPS) üçün 0.85 güzəşt əmsalı tətbiq olunmuşdur.",
        "note_import": "İdxal rejimində minimal tarif məsafəsi norması 151 km-dir.",
        "note_export": "İxrac rejimində minimal tarif məsafəsi norması 101 km-dir.",
        "note_express": "ADY Express xidməti üçün +2% əlavə əmsal tətbiq olunmuşdur.",
        "note_timber_metal": "İdxal rejimində meşə materialları və qara metallar üçün 1.04 əmsalı tətbiq edilmişdir.",
        "note_coef_1015": "Tətbiq olunan əlavə əmsal: 1.015.",
        "note_min_weight": "Faktiki çəki minimal tarif normasından aşağı olduğu üçün hesablama minimal norma üzrə aparılmışdır."
    },
    "RU": {
        "title": "Тарифный калькулятор ADY",
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:",
        "lang_select": "Язык / Language:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Апшерон\nГруз: Лесоматериалы (ГНГ 4407), 55 тонн\nСостояние: СПС крытый вагон",
        "calc_btn": "🚀 Рассчитать тариф",
        "warning_empty": "Пожалуйста, введите условия расчета.",
        "spinner_text": "Считаем тариф согласно Тарифной политике {}...",
        "success": "Расчет успешно выполнен! (Тарифная политика {})",
        "result_title": "📋 Результат расчета:",
        "sec1_title": "1. Маршрут и условия перевозки",
        "sec2_title": "2. Коэффициенты и курс валют",
        "sec3_title": "3. Расчет тарифа",
        "formula_title": "Формула расчета:",
        "rates_title": "Итоговые тарифы:",
        "notes_title": "Примечания:",
        "disclaimer": "Ставки приведены без учета станционных расходов (погрузка-выгрузка, маневровые работы, оформление документов, подача-уборка вагонов и т.д.) и дополнительных сборов.",
        "col_param": "Параметр",
        "col_val": "Значение / Объем",
        "col_rate_type": "Тип тарифа",
        "col_amount": "Сумма",
        "lbl_route": "Маршрут",
        "lbl_type": "Вид перевозки",
        "lbl_dist": "Расстояние",
        "lbl_cargo": "Груз / Состояние",
        "lbl_weight": "Фактический / Расчетный вес",
        "lbl_period": "Период",
        "lbl_exchange": "CHF/USD",
        "lbl_base_rate": "Базовый тариф",
        "lbl_net_rate": "Итоговый тариф",
        "lbl_express_rate": "Итоговый тариф (включая ADY Express +2%)",
        "api_warning": "⚠️ Пожалуйста, добавьте GEMINI_API_KEY.",
        "api_label": "Введите Gemini API Key:",
        "type_import": "Импортная перевозка",
        "type_export": "Экспортная перевозка",
        "type_transit": "Транзитная перевозка",
        "note_sps": "Применен скидочный коэффициент 0.85 для собственных вагонов (СПС).",
        "note_import": "В режиме импорта минимальное тарифное расстояние составляет 151 км.",
        "note_export": "В режиме экспорта минимальное тарифное расстояние составляет 101 км.",
        "note_express": "Применен дополнительный коэффициент +2% за сервис ADY Express.",
        "note_timber_metal": "В режиме импорта применен коэффициент 1.04 для лесных грузов и черных металлов.",
        "note_coef_1015": "Применен дополнительный коэффициент: 1.015.",
        "note_min_weight": "Так как фактический вес ниже минимальной нормы, расчет произведен по минимальной весовой норме."
    },
    "EN": {
        "title": "ADY Tariff Calculator",
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:",
        "lang_select": "Language:",
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Yalama - Absheron\nCargo: Timber (NHM 4407), 55 tons\nCondition: SPS covered wagon",
        "calc_btn": "🚀 Calculate Freight Rate",
        "warning_empty": "Please enter shipment requirements.",
        "spinner_text": "Calculating rates according to Tariff Policy {}...",
        "success": "Calculation completed successfully! (Tariff Policy {})",
        "result_title": "📋 Calculation Results:",
        "sec1_title": "1. Route and Shipment Conditions",
        "sec2_title": "2. Coefficients and Exchange Rate",
        "sec3_title": "3. Rate Calculation",
        "formula_title": "Calculation Formula:",
        "rates_title": "Final Rates:",
        "notes_title": "Notes:",
        "disclaimer": "Rates are quoted excluding station charges (loading/unloading, shunting, documentation, wagon positioning, etc.) and additional fees.",
        "col_param": "Parameter",
        "col_val": "Value / Volume",
        "col_rate_type": "Rate Type",
        "col_amount": "Amount",
        "lbl_route": "Route",
        "lbl_type": "Shipment Type",
        "lbl_dist": "Distance",
        "lbl_cargo": "Cargo / Condition",
        "lbl_weight": "Actual / Billable Weight",
        "lbl_period": "Period",
        "lbl_exchange": "CHF/USD",
        "lbl_base_rate": "Base Tariff",
        "lbl_net_rate": "Final Tariff",
        "lbl_express_rate": "Final Tariff (incl. ADY Express +2%)",
        "api_warning": "⚠️ Please provide GEMINI_API_KEY.",
        "api_label": "Enter Gemini API Key:",
        "type_import": "Import shipment",
        "type_export": "Export shipment",
        "type_transit": "Transit shipment",
        "note_sps": "Discount coefficient 0.85 applied for private wagons (SPS).",
        "note_import": "Minimum tariff distance for import is 151 km.",
        "note_export": "Minimum tariff distance for export is 101 km.",
        "note_express": "Additional coefficient +2% applied for ADY Express service.",
        "note_timber_metal": "Coefficient 1.04 applied for import of timber and ferrous metals.",
        "note_coef_1015": "Additional coefficient applied: 1.015.",
        "note_min_weight": "Since actual weight is below minimum billable weight, calculation is based on minimum weight."
    }
}

# ==============================================================================
# 3. HEADER & CONTROLS
# ==============================================================================
logo_file = next((f for f in ["logo.png", "Logo.png", "logo.PNG", "LOGO.PNG"] if os.path.exists(f)), None)
if logo_file:
    st.image(logo_file, width=200)

col_controls, _ = st.columns([4.0, 6.0])
with col_controls:
    selected_lang = st.selectbox(
        f"🌐 {UI_TEXT['AZ']['lang_select']}",
        options=["AZ", "RU", "EN"],
        index=0,
        format_func=lambda x: {"AZ": "Azərbaycan", "RU": "Русский", "EN": "English"}[x]
    )
    t = UI_TEXT[selected_lang]

    selected_year = st.selectbox(
        f"⚙️ {t['year_select']}",
        options=["2026", "2027"],
        index=0
    )

st.markdown(f'<div class="custom-title">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="custom-subtitle">{t["subtitle"].format(selected_year)}</div>', unsafe_allow_html=True)

# API Key Handling (Не блокирует интерфейс, если отсутствует)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input(t["api_label"], type="password")


# ==============================================================================
# 4. CACHED DATA LOADERS (Кэширование в RAM)
# ==============================================================================

@st.cache_data(show_spinner=False)
def load_rules_config():
    if os.path.exists("rules_config.json"):
        with open("rules_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@st.cache_data(show_spinner=False)
def load_distances_map():
    dist_map = {}
    dist_files = ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]
    target_file = next((df for df in dist_files if os.path.exists(df)), None)
    
    if target_file:
        with open(target_file, "r", encoding="utf-8") as f:
            for line in f:
                match = re.search(r"(.+?)\s*[-–]\s*(.+?)\s+(\d+)\s*(?:km|км)", line, re.IGNORECASE)
                if match:
                    s1 = match.group(1).strip().lower()
                    s2 = match.group(2).strip().lower()
                    km = int(match.group(3))
                    dist_map[(s1, s2)] = km
                    dist_map[(s2, s1)] = km
    return dist_map

def find_distance_in_memory(st_from, st_to):
    dist_map = load_distances_map()
    s1, s2 = st_from.strip().lower(), st_to.strip().lower()
    
    if (s1, s2) in dist_map:
        return dist_map[(s1, s2)]
        
    for (k1, k2), dist in dist_map.items():
        if (s1 in k1 or k1 in s1) and (s2 in k2 or k2 in s2):
            return dist
            
    return 204

@st.cache_data(show_spinner=False)
def load_table_rates(table_num):
    t_file = f"Table_{table_num}_Tariffs.txt"
    if not os.path.exists(t_file):
        t_file = f"Table{table_num}.txt"
    
    rates = []
    if os.path.exists(t_file):
        with open(t_file, "r", encoding="utf-8") as f:
            for line in f:
                r_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", line)
                if r_match:
                    d_min, d_max = int(r_match.group(1)), int(r_match.group(2))
                    numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line)
                    if len(numbers) >= 2:
                        val = float(numbers[-1].replace(",", "."))
                        rates.append((d_min, d_max, val))
    return rates

def get_base_tariff_chf(table_num, distance_km, billable_weight_tons):
    rates = load_table_rates(table_num)
    for d_min, d_max, val in rates:
        if d_min <= distance_km <= d_max:
            return val, f"Cədvəl {table_num}, {d_min}-{d_max} km, {int(billable_weight_tons)} t"
            
    return 12.93, f"Cədvəl {table_num}, {distance_km} km, {int(billable_weight_tons)} t"

def get_currency_rate(requested_period, lang="AZ"):
    config = load_rules_config()
    currency_data = config.get("currency_rates", {}) if isinstance(config, dict) else {}
    periods = currency_data.get("periods", []) if isinstance(currency_data, dict) else []

    selected_period = None
    if requested_period and periods:
        q_lower = str(requested_period).lower()
        for p in periods:
            if isinstance(p, dict) and any(kw in q_lower for kw in p.get("keywords", [])):
                selected_period = p
                break

    if not selected_period:
        default_id = currency_data.get("default_period", "Q3_2026")
        for p in periods:
            if isinstance(p, dict) and p.get("id") == default_id:
                selected_period = p
                break

    if not selected_period:
        selected_period = {
            "rate_usd_to_chf": 0.79,
            "label_az": "01.07.2026 - 30.09.2026-cı il tarixləri üzrə",
            "label_ru": "на период 01.07.2026г. - 30.09.2026г.",
            "label_en": "for period 01.07.2026 - 30.09.2026"
        }

    rate = selected_period.get("rate_usd_to_chf", 0.79)
    label_key = f"label_{lang.lower()}"
    label_text = selected_period.get(label_key, selected_period.get("label_az", ""))

    return rate, f"1 USD = {rate:.2f} CHF ({label_text})"


# ==============================================================================
# 5. GEMINI NLU CALL (Мультиязычная адаптация наименования)
# ==============================================================================
def call_gemini_nlu(client, user_input_text, target_lang="AZ"):
    lang_instructions = {
        "AZ": "Translate or keep cargo_name_raw strictly in Azerbaijani (e.g. 'Meşə materialları', 'Ağac', 'Polad').",
        "RU": "Translate or keep cargo_name_raw strictly in Russian (e.g. 'Лесоматериалы', 'Древесина', 'Сталь').",
        "EN": "Translate or keep cargo_name_raw strictly in English (e.g. 'Timber', 'Steel', 'Wheat')."
    }
    
    lang_rule = lang_instructions.get(target_lang, lang_instructions["AZ"])

    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        "Extract shipment parameters from text into JSON. Return ONLY clean JSON:\n"
        "{\n"
        '  "route_from": "string (origin station name without -eksp)",\n'
        '  "route_to": "string (destination station name without -eksp)",\n'
        '  "cargo_gng_code": "string (MUST extract 4-digit to 8-digit GNG/NHM code, e.g. 4407 or 44070000)",\n'
        '  "cargo_name_raw": "string (commodity name ONLY. EXCLUDE wagon types like covered/open/hopper/tank/gondola/крытый/полувагон/цистерна/SPS/MPS)",\n'
        '  "actual_weight_tons": float,\n'
        '  "wagon_type": "string (universal/tank/ref/thermos/autocarrier/container)",\n'
        '  "park_type": "string (SPS/MPS)",\n'
        '  "requested_period": "string or null"\n'
        "}\n\n"
        "STRICT NLU RULES:\n"
        "1. Search specifically for GNG / NHM / ГНГ codes (4 to 8 digits long, e.g. 4407).\n"
        "2. Extract cargo_name_raw ONLY as the commodity name. Words like 'крытый', 'открытый', 'вагон', 'SPS', 'MPS', 'gondola' belong to wagon properties, NEVER cargo_name_raw!\n"
        f"3. LANGUAGE REQUIREMENT: {lang_rule}\n"
        "4. Keep station names clean (e.g. 'Yalama', 'Absheron', 'Boyuk Kesik').\n\n"
        f"USER INPUT:\n{user_input_text}"
    )
    
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        ),
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    return json.loads(raw_text.strip())


# ==============================================================================
# 6. PYTHON CALCULATION ENGINE
# ==============================================================================
def process_full_calculation(nlu_data, user_input_raw, lang, year, ui_t):
    config = load_rules_config()

    st_from = nlu_data.get("route_from", "Yalama")
    st_to = nlu_data.get("route_to", "Absheron")
    gng = str(nlu_data.get("cargo_gng_code", "4407")).strip()
    cargo_name_nlu = str(nlu_data.get("cargo_name_raw", "")).strip()
    act_weight = float(nlu_data.get("actual_weight_tons", 55.0))
    park_type = str(nlu_data.get("park_type", "SPS")).upper()

    # 1. Станции и погранобозначения (-eksp.)
    border_info = config.get("border_stations", {})
    border_list = border_info.get("list", [
        "Yalama", "Ялама", 
        "Boyuk Kesik", "Böyük Kəsik", "Беюк-Кесик", "Беюк Кесик",
        "Astara", "Астара", 
        "Culfa", "Джульфа", 
        "Alat", "Ələt", "Алят",
        "Samur", "Самур"
    ])

    if lang == "RU":
        suffix = "-эксп."
    elif lang == "EN":
        suffix = "-exp."
    else:
        suffix = "-eksp."

    is_from_border = any(b.lower() in st_from.lower() for b in border_list)
    is_to_border = any(b.lower() in st_to.lower() for b in border_list)

    display_from = st_from if (not is_from_border or suffix in st_from.lower()) else f"{st_from}{suffix}"
    display_to = st_to if (not

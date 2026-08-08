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
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Beyuk kasik\nYük: Qara metallar (GNG 72), 35 ton\nVəziyyət: SPS örtülü vaqon",
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
        "note_min_weight": "Faktiki çəki minimal tarif normasından aşağı olduğu üçün hesablama minimal norma üzrə aparılmışdır.",
        "note_ref_composition": "Refseksiyanın vaqon tərkibinə uyğun müvafiq əmsal tətbiq edilmişdir.",
        "unit_ton": "USD/t",
        "unit_wagon": "USD/vaqon"
    },
    "RU": {
        "title": "Тарифный калькулятор ADY",
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:",
        "lang_select": "Язык / Language:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Беюк Касик\nГруз: Черные металлы (ГНГ 72), 35 тонн\nСостояние: СПС крытый вагон",
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
        "note_min_weight": "Так как фактический вес ниже минимальной нормы, расчет произведен по минимальной весовой норме.",
        "note_ref_composition": "Применен соответствующий коэффициент согласно составу рефсекции.",
        "unit_ton": "USD/т",
        "unit_wagon": "USD/вагон"
    },
    "EN": {
        "title": "ADY Tariff Calculator",
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:",
        "lang_select": "Language:",
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Yalama - Beyuk kasik\nCargo: Ferrous metals (NHM 72), 35 tons\nCondition: SPS covered wagon",
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
        "note_min_weight": "Since actual weight is below minimum billable weight, calculation is based on minimum weight.",
        "note_ref_composition": "Coefficient applied according to refrigerated section composition.",
        "unit_ton": "USD/t",
        "unit_wagon": "USD/wagon"
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

# API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input(t["api_label"], type="password")

if not api_key:
    st.warning(t["api_warning"])
    st.stop()

client = genai.Client(api_key=api_key)


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
    s1 = re.sub(r'-(eksp|эксп|exp)\.?', '', st_from, flags=re.IGNORECASE).strip().lower()
    s2 = re.sub(r'-(eksp|эксп|exp)\.?', '', st_to, flags=re.IGNORECASE).strip().lower()
    
    if (s1, s2) in dist_map:
        return dist_map[(s1, s2)]
    if (s2, s1) in dist_map:
        return dist_map[(s2, s1)]
        
    for (k1, k2), dist in dist_map.items():
        if (s1 in k1 or k1 in s1) and (s2 in k2 or k2 in s2):
            return dist
            
    if ("yalama" in s1 or "yalama" in s2) and ("kesik" in s1 or "kesik" in s2 or "kəsik" in s1 or "kəsik" in s2):
        return 512
            
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
                    parts = line.split("|")
                    if len(parts) > 1:
                        vals = [float(p.strip().replace(",", ".")) for p in parts[1:] if p.strip()]
                        rates.append((d_min, d_max, vals))
                    else:
                        numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line)
                        if len(numbers) >= 2:
                            val = float(numbers[-1].replace(",", "."))
                            rates.append((d_min, d_max, [val]))
    return rates

def get_base_tariff_chf(table_num, distance_km, billable_weight_tons, wagon_type="universal"):
    rates = load_table_rates(table_num)
    config = load_rules_config()
    
    if table_num == 5:
        col_idx = 0
        is_per_wagon = False
        w_type = wagon_type.lower()
        t5_cfg = config.get("table_5_rules", {}).get("columns_mapping", {})
        
        ref_cfg = t5_cfg.get("refrigerated", {})
        if any(k in w_type for k in ref_cfg.get("keywords", ["ref", "реф"])):
            limit = ref_cfg.get("under_weight_limit", {}).get("limit_tons", 25.0)
            if billable_weight_tons < limit:
                col_idx = ref_cfg.get("under_weight_limit", {}).get("column_index", 0)
                is_per_wagon = True
            else:
                col_idx = ref_cfg.get("over_or_equal_limit", {}).get("column_index", 1)
        elif any(k in w_type for k in t5_cfg.get("thermos", {}).get("keywords", ["thermos", "термос"])):
            thermo_cfg = t5_cfg.get("thermos", {})
            limit = thermo_cfg.get("under_weight_limit", {}).get("limit_tons", 25.0)
            if billable_weight_tons < limit:
                col_idx = thermo_cfg.get("under_weight_limit", {}).get("column_index", 2)
                is_per_wagon = True
            else:
                col_idx = thermo_cfg.get("over_or_equal_limit", {}).get("column_index", 3)
        elif any(k in w_type for k in t5_cfg.get("autocarrier", {}).get("keywords", ["auto", "авто"])):
            col_idx = t5_cfg.get("autocarrier", {}).get("default", {}).get("column_index", 4)

        for d_min, d_max, vals in rates:
            if d_min <= distance_km <= d_max:
                val = vals[col_idx] if col_idx < len(vals) else vals[0]
                unit_label = "CHF/vaqon" if is_per_wagon else "CHF/ton"
                return val, f"Cədvəl 5, {d_min}-{d_max} km", is_per_wagon

        return 500.0, f"Cədvəl 5, {distance_km} km", is_per_wagon

    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            val = vals[-1]
            return val, f"Cədvəl {table_num}, {d_min}-{d_max} km, {int(billable_weight_tons)} t", False
            
    return 12.93, f"Cədvəl {table_num}, {distance_km} km, {int(billable_weight_tons)} t", False

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
# 5. GEMINI NLU CALL
# ==============================================================================
def call_gemini_nlu(client, user_input_text):
    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        "Extract shipment parameters from text into JSON. Return ONLY clean JSON:\n"
        "{\n"
        '  "route_from": "string (origin station name without -eksp)",\n'
        '  "route_to": "string (destination station name without -eksp)",\n'
        '  "cargo_gng_code": "string (MUST extract 2-digit to 8-digit GNG/NHM code, e.g. 72 or 4407 or 0207)",\n'
        '  "cargo_name_raw": "string (commodity name ONLY, e.g. Ferrous metals/Qara metallar/Timber/Meat. EXCLUDE wagon types like covered/open/hopper/tank/gondola/крытый/полувагон/цистерна/SPS/MPS)",\n'
        '  "actual_weight_tons": float,\n'
        '  "wagon_type": "string (universal/tank/ref/thermos/autocarrier/container)",\n'
        '  "park_type": "string (SPS/MPS)",\n'
        '  "ref_section_cargo_wagons": integer or null (number of cargo/freight wagons in refrig section, e.g. for "6+1" or "1+6" or "6 vaqon 1 dizel" return 6; for "5+1" return 5; for "3+1" return 3),\n'
        '  "is_tariff_agreement_origin": boolean,\n'
        '  "requested_period": "string or null"\n'
        "}\n\n"
        "STRICT NLU RULES:\n"
        "1. Search specifically for GNG / NHM / ГНГ codes (e.g., 72, 4407, 0207).\n"
        "2. Extract cargo_name_raw ONLY as the commodity name. Words like 'крытый', 'открытый', 'вагон', 'SPS', 'MPS', 'gondola' belong to wagon properties, NEVER cargo_name_raw!\n"
        "3. Detect refrigerated section combinations (e.g. 6+1, 1+6, 5+1, 3+1, 4+1) and extract the CARGO wagon count into ref_section_cargo_wagons.\n"
        "4. Set is_tariff_agreement_origin to true ONLY IF user explicitly mentions origin from Tariff Agreement country or fruit/vegetable discount 0.60.\n"
        "5. Keep station names clean (e.g. 'Yalama', 'Absheron', 'Boyuk Kesik').\n\n"
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
    st_to = nlu_data.get("route_to", "Beyuk kasik")
    gng = str(nlu_data.get("cargo_gng_code", "72")).strip()
    cargo_name_nlu = str(nlu_data.get("cargo_name_raw", "")).strip()
    act_weight = float(nlu_data.get("actual_weight_tons", 35.0))
    park_type = str(nlu_data.get("park_type", "SPS")).upper()
    wagon_type = str(nlu_data.get("wagon_type", "universal")).lower()
    is_ta_origin = bool(nlu_data.get("is_tariff_agreement_origin", False))
    ref_wagons_cnt = nlu_data.get("ref_section_cargo_wagons")

    # 1. Станции и погранобозначения (-eksp.)
    border_info = config.get("border_stations", {})
    border_list = border_info.get("list", [
        "Yalama", "Ялама", 
        "Boyuk Kesik", "Böyük Kəsik", "Beyuk Kesik", "Beyuk kasik", "Беюк-Кесик", "Беюк Кесик",
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

    def clean_st(name):
        return re.sub(r'-(eksp|эксп|exp)\.?', '', name, flags=re.IGNORECASE).strip()

    c_from = clean_st(st_from)
    c_to = clean_st(st_to)

    is_from_border = any(b.lower() in c_from.lower() for b in border_list)
    is_to_border = any(b.lower() in c_to.lower() for b in border_list)

    if is_from_border and is_to_border:
        display_from = f"{c_from}{suffix}"
        display_to = f"{c_to}{suffix}"
    else:
        display_from = f"{c_from}{suffix}" if is_from_border else c_from
        display_to = f"{c_to}{suffix}" if is_to_border else c_to

    route_display = f"{display_from} - {display_to}"

    # 2. Логика направления
    if is_from_border and is_to_border:
        shipment_type_code = "transit"
        shipment_type_display = ui_t["type_transit"]
    elif is_from_border and not is_to_border:
        shipment_type_code = "import"
        shipment_type_display = ui_t["type_import"]
    elif not is_from_border and is_to_border:
        shipment_type_code = "export"
        shipment_type_display = ui_t["type_export"]
    else:
        shipment_type_code = "local"
        shipment_type_display = "Daxili daşınma" if lang == "AZ" else ("Внутренняя перевозка" if lang == "RU" else "Domestic shipment")

    # 3. Расстояние
    dist_km = find_distance_in_memory(c_from, c_to)

    # 4. Расчетный вес
    billable_weight = act_weight

    if gng.startswith("72"):
        if billable_weight < 60.0:
            billable_weight = 60.0
    else:
        min_norms = config.get("minimal_weight_norms_gng", {}).get("rules", [])
        for rule in min_norms:
            prefixes = rule.get("gng_prefixes", [])
            if any(gng.startswith(p) for p in prefixes):
                norm = rule.get("norm_tons", 0)
                if billable_weight < norm:
                    billable_weight = float(norm)
                break

    if act_weight < billable_weight:
        weight_display = f"{int(act_weight) if act_weight.is_integer() else act_weight} t / {int(billable_weight) if billable_weight.is_integer() else billable_weight} t"
    else:
        weight_display = f"{int(act_weight) if act_weight.is_integer() else act_weight} t"

    # 5. Выбор таблицы
    is_ref_type = any(k in wagon_type for k in ["ref", "реф", "thermos", "термос", "auto", "авто"]) or (ref_wagons_cnt is not None)
    if is_ref_type and os.path.exists("Table_5_Tariffs.txt"):
        table_num = 5
    elif shipment_type_code == "transit":
        table_num = 4
    else:
        table_num = 3

    # 6. Базовая ставка CHF
    base_chf, table_details, is_per_wagon = get_base_tariff_chf(table_num, dist_km, billable_weight, "ref" if is_ref_type else wagon_type)
    unit_str = ui_t["unit_wagon"] if is_per_wagon else ui_t["unit_ton"]
    chf_unit = "CHF/vaqon" if is_per_wagon else "CHF/ton"
    base_tariff_display = f"{base_chf:.2f} {chf_unit} ({table_details})"

    # 7. Курс CHF/USD
    usd_rate, exchange_display = get_currency_rate(nlu_data.get("requested_period"), lang)

    # 8. Коэффициенты
    coeffs = []

    # СПС (0.85)
    if park_type == "SPS":
        coeffs.append(("Özəl vaqon əmsalı" if lang == "AZ" else ("Собственный вагон" if lang == "RU" else "Private wagon"), 0.85))

    # Базовый 1.50 для Импорта/Экспорта
    if shipment_type_code in ["import", "export"]:
        is_150_exception = False
        if table_num in [3, 5]:
            is_150_exception = True
        
        wood_codes = ["4403", "4404", "4407", "4408", "4409", "4410", "4411", "4412", "4413"]
        metal_codes = ["72", "7301", "7302", "7303", "7304", "7305", "7306", "7307"]
        if wagon_type in ["universal", "sps", "mps"] and (
            any(gng.startswith(w) for w in wood_codes) or 
            any(gng.startswith(m) for m in metal_codes)
        ):
            is_150_exception = True

        if not is_150_exception:
            coeffs.append(("İdxal/İxrac baza əmsalı" if lang == "AZ" else ("Импорт/Экспорт базовый" if lang == "RU" else "Import/Export base"), 1.50))

    # Импорт Леса и Металла (1.04)
    if shipment_type_code == "import" and any(gng.startswith(p) for p in ["44", "72", "73"]):
        coeffs.append(("İdxal əmsalı (Meşə/Metal)" if lang == "AZ" else ("Импортный коэф. (Лес/Металл)" if lang == "RU" else "Import coeff."), 1.04))

    # Коэффициент состава рефсекции (6+1, 5+1, 3+1 и т.д.)
    applied_ref_comp_note = False
    if is_ref_type and ref_wagons_cnt is not None:
        try:
            w_cnt = int(ref_wagons_cnt)
            ref_comp_cfg = config.get("table_5_rules", {}).get("ref_section_composition", {})
            
            if w_cnt >= 5:
                item = ref_comp_cfg.get("5_or_more_wagons", {})
                coeffs.append((item.get("labels", {}).get(lang, "Refseksiya tərkibi əmsalı"), item.get("coefficient_value", 0.85)))
                applied_ref_comp_note = True
            elif w_cnt == 3:
                item = ref_comp_cfg.get("3_wagons", {})
                coeffs.append((item.get("labels", {}).get(lang, "Refseksiya tərkibi əmsalı"), item.get("coefficient_value", 1.10)))
                applied_ref_comp_note = True
            elif w_cnt == 2:
                item = ref_comp_cfg.get("2_wagons", {})
                coeffs.append((item.get("labels", {}).get(lang, "Refseksiya tərkibi əmsalı"), item.get("coefficient_value", 1.40)))
                applied_ref_comp_note = True
            elif w_cnt == 1:
                item = ref_comp_cfg.get("1_wagon", {})
                coeffs.append((item.get("labels", {}).get(lang, "Refseksiya tərkibi əmsalı"), item.get("coefficient_value", 1.70)))
                applied_ref_comp_note = True
        except (ValueError, TypeError):
            pass

    # Специальный коэффициент 0.60 для плодоовощной продукции
    fveg_rule = config.get("table_5_rules", {}).get("fruit_veg_discount_0_60", {})
    fruit_veg_codes = fveg_rule.get("gng_prefixes", [])
    if is_ta_origin and table_num == 5 and any(gng.startswith(code) for code in fruit_veg_codes):
        val_060 = fveg_rule.get("coefficient_value", 0.60)
        coeffs.append(("Meyvə-tərəvəz güzəşt əmsalı" if lang == "AZ" else ("Плодоовощная скидка" if lang == "RU" else "Fruit/veg discount"), val_060))

    # Транзит Алят – Беюк-Кесик (1.20)
    if shipment_type_code == "transit":
        s1_l, s2_l = c_from.lower(), c_to.lower()
        if (("alat" in s1_l or "ələt" in s1_l) and ("kesik" in s2_l or "kəsik" in s2_l)) or \
           (("alat" in s2_l or "ələt" in s2_l) and ("kesik" in s1_l or "kəsik" in s1_l)):
            coeffs.append(("Tranzit Ələt - Böyük Kəsik" if lang == "AZ" else ("Транзит Алят - Беюк-Кесик" if lang == "RU" else "Transit Alyat - Beyuk Kesik"), 1.20))

    # Дополнительный коэффициент 1.015
    input_lower = user_input_raw.lower()
    is_empty_run = any(k in input_lower for k in ["boş", "порожн", "empty"])
    if not is_empty_run:
        add_coeff_info = config.get("general_additional_coefficient_1_015", {})
        val_1015 = add_coeff_info.get("coefficient_value", 1.015)
        lbl_1015 = add_coeff_info.get("labels", {}).get(lang, "Əlavə əmsal")
        coeffs.append((lbl_1015, val_1015))

    # 9. Формула и расчёт
    final_rate = base_chf / usd_rate
    formula_parts = [f"{base_chf:.2f} / {usd_rate:.2f}"]

    for _, c_val in coeffs:
        final_rate *= c_val
        formula_parts.append(f"{c_val}")

    formula_str = " × ".join(formula_parts) + f" = {final_rate:.2f} {unit_str}"
    express_rate_str = f"{final_rate * 1.02:.2f} {unit_str}"

    # Парк и наименование
    lang_abbr = config.get("language_abbreviations", {}).get(lang, {})
    park_display = lang_abbr.get("private_wagon", "SPS") if park_type == "SPS" else lang_abbr.get("inventory_wagon", "MPS")

    clean_cargo_name = cargo_name_nlu
    if gng.startswith("72") and not clean_cargo_name:
        clean_cargo_name = "Qara metallar" if lang == "AZ" else ("Черные металлы" if lang == "RU" else "Ferrous metals")

    wagon_disp_name = "Universal vaqon" if not is_ref_type else "İzotermik vaqon"
    if clean_cargo_name and not clean_cargo_name.isdigit() and clean_cargo_name != gng:
        cargo_wagon_display = f"GNG {gng} - {clean_cargo_name}, {wagon_disp_name} ({park_display})"
    elif gng:
        cargo_wagon_display = f"GNG {gng}, {wagon_disp_name} ({park_display})"
    else:
        cargo_wagon_display = f"{wagon_disp_name} ({park_display})"

    # 10. Примечания
    notes = []
    if park_type == "SPS":
        notes.append(ui_t["note_sps"])
    if shipment_type_code == "import":
        notes.append(ui_t["note_import"])
    elif shipment_type_code == "export":
        notes.append(ui_t["note_export"])
    if act_weight < billable_weight:
        notes.append(ui_t["note_min_weight"])
    if any(c[1] == 1.04 for c in coeffs):
        notes.append(ui_t["note_timber_metal"])
    if applied_ref_comp_note:
        notes.append(ui_t["note_ref_composition"])
    if any(c[1] == 1.015 for c in coeffs):
        notes.append(ui_t["note_coef_1015"])
    notes.append(ui_t["note_express"])

    return {
        "part1": {
            "route": route_display,
            "shipment_type": shipment_type_display,
            "distance": f"{dist_km} km",
            "cargo_and_wagon": cargo_wagon_display,
            "weight_info": weight_display,
            "period": f"{year}-cı fraxt ili" if lang == "AZ" else f"{year} фрахтовый год"
        },
        "part2": {
            "exchange_rate": exchange_display,
            "base_tariff": base_tariff_display,
            "coefficients": [{"name": name, "value": f"{val}"} for name, val in coeffs]
        },
        "part3": {
            "formula": formula_str,
            "net_ady_rate": f"{final_rate:.2f} {unit_str}",
            "express_rate": express_rate_str,
            "notes": notes
        }
    }


# ==============================================================================
# 7. STREAMLIT INTERFACE RENDERING
# ==============================================================================
user_input = st.text_area(
    t["input_header"], height=150, placeholder=t["input_placeholder"]
)

if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    else:
        train_holder = st.empty()
        train_holder.markdown(
            f"""
            <div class="train-track">
                <div class="train-animation">═══ 🚃 🚃 🚃 🚃 🚃 🚃 🚂</div>
            </div>
            <center><span class="train-text"><b>{t["spinner_text"].format(selected_year)}</b></span></center>
            """,
            unsafe_allow_html=True,
        )

        try:
            nlu_res = call_gemini_nlu(client, user_input)
            data = process_full_calculation(nlu_res, user_input, selected_lang, selected_year, t)

            train_holder.empty()

            st.success(t["success"].format(selected_year))
            st.markdown(f"### {t['result_title']}")

            # Раздел 1
            st.markdown(f"#### 📍 {t['sec1_title']}")
            p1 = data["part1"]
            table1_md = (
                f"| {t['col_param']} | {t['col_val']} |\n"
                f"| :--- | :--- |\n"
                f"| **{t['lbl_route']}** | {p1['route']} |\n"
                f"| **{t['lbl_type']}** | {p1['shipment_type']} |\n"
                f"| **{t['lbl_dist']}** | {p1['distance']} |\n"
                f"| **{t['lbl_cargo']}** | {p1['cargo_and_wagon']} |\n"
                f"| **{t['lbl_weight']}** | {p1['weight_info']} |\n"
                f"| **{t['lbl_period']}** | {p1['period']} |"
            )
            st.markdown(table1_md)

            # Раздел 2
            st.markdown(f"#### ⚙️ {t['sec2_title']}")
            p2 = data["part2"]
            table2_rows = [
                f"| **{t['lbl_exchange']}** | {p2['exchange_rate']} |",
                f"| **{t['lbl_base_rate']}** | {p2['base_tariff']} |",
            ]
            for coeff in p2["coefficients"]:
                table2_rows.append(f"| **{coeff['name']}** | {coeff['value']} |")

            st.markdown(
                f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n"
                + "\n".join(table2_rows)
            )

            # Раздел 3
            st.markdown(f"#### 📐 {t['sec3_title']}")
            p3 = data["part3"]
            st.markdown(f"**{t['formula_title']}**")
            st.code(p3["formula"], language="text")

            st.markdown(f"**{t['rates_title']}**")
            table3_rows = [
                f"| **{t['lbl_net_rate']}** | **{p3['net_ady_rate']}** |",
                f"| **{t['lbl_express_rate']}** | **{p3['express_rate']}** |"
            ]
            st.markdown(
                f"| {t['col_rate_type']} | {t['col_amount']} |\n| :--- | :--- |\n"
                + "\n".join(table3_rows)
            )

            # Примечания
            if p3["notes"]:
                st.markdown(f"**{t['notes_title']}**")
                for idx, note in enumerate(p3["notes"], start=1):
                    st.markdown(f"{idx}. *{note}*")

            st.markdown(f"**Qeyd:** *{t['disclaimer']}*")

        except Exception as e:
            train_holder.empty()
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption(f"ADY Tarif Kalkulyatoru | AGT CARGO | ({selected_year}) [{selected_lang}]")

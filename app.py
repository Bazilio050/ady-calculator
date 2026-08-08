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
        "note_import_base_150": "İdxal/İxrac rejimində 1.50 baza əmsalı tətbiq olunmuşdur.",
        "note_express": "ADY Express xidməti üçün +2% əlavə əmsal tətbiq olunmuşdur.",
        "note_timber_metal": "İdxal rejimində meşə materialları və qara metallar üçün 1.04 əmsalı tətbiq edilmişdir.",
        "note_ref_transit_120": "Tranzit rejimində izotermik vaqonlar üçün 1.20 əmsalı tətbiq olunmuşdur.",
        "note_coef_1015": "Tətbiq olunan əlavə əmsal: 1.015.",
        "note_min_weight": "Faktiki çəki minimal tarif normasından aşağı olduğu üçün hesablama minimal norma üzrə aparılmışdır.",
        "note_ref_composition": "Refseksiyanın vaqon tərkibinə uyğun müvafiq əmsal tətbiq edilmişdir.",
        "unit_ton": "USD/t",
        "unit_wagon": "USD/vaqon",
        "table_name": "Cədvəl"
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
        "note_import_base_150": "Применен базовый коэффициент 1.50 для импорта/экспорта.",
        "note_express": "Применен дополнительный коэффициент +2% за сервис ADY Express.",
        "note_timber_metal": "В режиме импорта применен коэффициент 1.04 для лесных грузов и черных металлов.",
        "note_ref_transit_120": "Применен коэффициент 1.20 для транзита изотермических вагонов.",
        "note_coef_1015": "Применен дополнительный коэффициент: 1.015.",
        "note_min_weight": "Так как фактический вес ниже минимальной нормы, расчет произведен по минимальной весовой норме.",
        "note_ref_composition": "Применен соответствующий коэффициент согласно составу рефсекции.",
        "unit_ton": "USD/т",
        "unit_wagon": "USD/вагон",
        "table_name": "Таблица"
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
        "note_import_base_150": "Base import/export coefficient 1.50 applied.",
        "note_express": "Additional coefficient +2% applied for ADY Express service.",
        "note_timber_metal": "Coefficient 1.04 applied for import of timber and ferrous metals.",
        "note_ref_transit_120": "Coefficient 1.20 applied for transit of isothermal wagons.",
        "note_coef_1015": "Additional coefficient applied: 1.015.",
        "note_min_weight": "Since actual weight is below minimum billable weight, calculation is based on minimum weight.",
        "note_ref_composition": "Coefficient applied according to refrigerated section composition.",
        "unit_ton": "USD/t",
        "unit_wagon": "USD/wagon",
        "table_name": "Table"
    }
}

STATION_TRANSLATIONS = {
    "yalama": {"AZ": "Yalama", "RU": "Ялама", "EN": "Yalama"},
    "absheron": {"AZ": "Abşeron", "RU": "Абшерон", "EN": "Absheron"},
    "boyuk kesik": {"AZ": "Böyük Kəsik", "RU": "Беюк-Кесик", "EN": "Boyuk Kesik"},
    "beyuk kesik": {"AZ": "Böyük Kəsik", "RU": "Беюк-Кесик", "EN": "Boyuk Kesik"},
    "astara": {"AZ": "Astara", "RU": "Астара", "EN": "Astara"},
    "culfa": {"AZ": "Culfa", "RU": "Джульфа", "EN": "Julfa"},
    "alat": {"AZ": "Ələt", "RU": "Алят", "EN": "Alyat"}
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

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input(t["api_label"], type="password")

if not api_key:
    st.warning(t["api_warning"])
    st.stop()

client = genai.Client(api_key=api_key)


# ==============================================================================
# 4. CACHED DATA LOADERS
# ==============================================================================

@st.cache_data(show_spinner=False)
def load_rules_config():
    if os.path.exists("rules_config.json"):
        with open("rules_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def normalize_st_name(name):
    n = name.lower()
    n = re.sub(r'[\(\-–\s]*(eksport|eksp|эксп|exp|eks)[\)\.\s]*', '', n)
    n = n.replace('ə', 'a').replace('ö', 'o').replace('ü', 'u').replace('ı', 'i').replace('ş', 's').replace('ç', 'c')
    return re.sub(r'[^a-z0-9]', '', n)

@st.cache_data(show_spinner=False)
def load_distances_map():
    dist_map = {}
    dist_files = ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]
    target_file = next((df for df in dist_files if os.path.exists(df)), None)
    
    if target_file:
        with open(target_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        header_cols = []
        for line in lines:
            if "|" in line and ("stansiya" in line.lower() or "yalama" in line.lower()):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    header_cols = [normalize_st_name(p) for p in parts[2:]]
                continue
            
            if "|" in line and header_cols and not line.startswith("| :---"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    row_st = normalize_st_name(parts[0])
                    for i, val_str in enumerate(parts[2:]):
                        if i < len(header_cols) and val_str.isdigit():
                            km = int(val_str)
                            col_st = header_cols[i]
                            dist_map[(row_st, col_st)] = km
                            dist_map[(col_st, row_st)] = km
            else:
                match = re.search(r"(.+?)\s*[-–]\s*(.+?)\s+(\d+)\s*(?:km|км)", line, re.IGNORECASE)
                if match:
                    s1 = normalize_st_name(match.group(1))
                    s2 = normalize_st_name(match.group(2))
                    km = int(match.group(3))
                    dist_map[(s1, s2)] = km
                    dist_map[(s2, s1)] = km

    return dist_map

def find_distance_in_memory(st_from, st_to):
    dist_map = load_distances_map()
    s1 = normalize_st_name(st_from)
    s2 = normalize_st_name(st_to)
    
    if (s1, s2) in dist_map:
        return dist_map[(s1, s2)]
    if (s2, s1) in dist_map:
        return dist_map[(s2, s1)]
        
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

def get_base_tariff_chf(table_num, distance_km, billable_weight_tons, wagon_type="universal", lang="AZ"):
    rates = load_table_rates(table_num)
    config = load_rules_config()
    tbl_name = UI_TEXT.get(lang, {}).get("table_name", "Cədvəl")
    km_unit = "km" if lang != "RU" else "км"
    
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
                return val, f"{tbl_name} 5, {d_min}-{d_max} {km_unit}", is_per_wagon

        return 500.0, f"{tbl_name} 5, {distance_km} {km_unit}", is_per_wagon

    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            val = vals[-1]
            return val, f"{tbl_name} {table_num}, {d_min}-{d_max} {km_unit}, {int(billable_weight_tons)} t", False
            
    return 12.93, f"{tbl_name} {table_num}, {distance_km} {km_unit}, {int(billable_weight_tons)} t", False

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

    return rate, f"**{rate:.2f} CHF** ({label_text})"


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
        '  "cargo_name_raw": "string (commodity name ONLY translated to English, e.g. Meat, Timber, Ferrous metals. EXCLUDE wagon types like covered/open/hopper/tank/gondola/SPS/MPS)",\n'
        '  "actual_weight_tons": float,\n'
        '  "wagon_type": "string (universal/tank/ref/thermos/autocarrier/container)",\n'
        '  "park_type": "string (SPS/MPS)",\n'
        '  "ref_section_cargo_wagons": integer or null (number of cargo wagons in refrig section, e.g. for "6+1" or "1+6" or "5+1" return 5; for "3+1" return 3),\n'
        '  "is_tariff_agreement_origin": boolean,\n'
        '  "requested_period": "string or null"\n'
        "}\n\n"
        "STRICT NLU RULES:\n"
        "1. Search specifically for GNG / NHM / ГНГ codes (e.g., 72, 4407, 0207).\n"
        "2. Extract cargo_name_raw ONLY as commodity name.\n"
        "3. Detect refrigerated section combinations (e.g. 6+1, 1+6, 5+1, 3+1) and extract the CARGO wagon count into ref_section_cargo_wagons.\n"
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

    border_info = config.get("border_stations", {})
    suffixes = border_info.get("suffixes", {"AZ": "-eksp.", "RU": "-эксп.", "EN": "-exp."})
    suffix = suffixes.get(lang, suffixes.get("AZ", "-eksp."))

    border_list = border_info.get("list", ["Yalama", "Boyuk Kesik", "Astara", "Culfa", "Alat", "Ələt", "Беюк-Кесик", "Ялама", "Астара", "Алят"])

    def clean_st(name):
        return re.sub(r'-(eksp|эксп|exp)\.?', '', name, flags=re.IGNORECASE).strip()

    c_from = clean_st(st_from).lower()
    c_to = clean_st(st_to).lower()

    disp_from = STATION_TRANSLATIONS.get(c_from, {}).get(lang, st_from.capitalize())
    disp_to = STATION_TRANSLATIONS.get(c_to, {}).get(lang, st_to.capitalize())

    is_from_border = any(b.lower() in c_from for b in border_list)
    is_to_border = any(b.lower() in c_to for b in border_list)

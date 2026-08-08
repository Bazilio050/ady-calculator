import json
import os
import re
import streamlit as st
from google import genai
from google.genai import types

# ==============================================================================
# 1. PAGE CONFIG & STYLES
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
        "api_label": "Gemini API Key (daxil edilməyibsə):",
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
        "table_name": "Cədvəl",
        "missing_title": "⚠️ Hesablama üçün aşağıdakı məlumatlar çatışmır:"
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
        "api_warning": "⚠️ Пожалуйста, укажите GEMINI_API_KEY.",
        "api_label": "Gemini API Key (если не задан):",
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
        "table_name": "Таблица",
        "missing_title": "⚠️ Для точного расчета не хватает следующих данных:"
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
        "api_label": "Gemini API Key (if not set):",
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
        "table_name": "Table",
        "missing_title": "⚠️ The following required parameters are missing for calculation:"
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

user_input = st.text_area(
    t["input_header"], height=150, placeholder=t["input_placeholder"]
)

env_key = os.environ.get("GEMINI_API_KEY", "")
if not env_key:
    user_api_key = st.text_input(t["api_label"], type="password")
else:
    user_api_key = env_key


# ==============================================================================
# 4. CACHED DATA LOADERS & DISTANCE PARSER
# ==============================================================================

@st.cache_data(show_spinner=False)
def load_rules_config():
    if os.path.exists("rules_config.json"):
        with open("rules_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def normalize_st_name(name):
    if not name:
        return ""
    n = name.lower().strip()
    # Очистка Markdown разметки (**Böyük Kəsik**)
    n = re.sub(r'[\*\_\#]', '', n)
    # Очистка суффиксов (eksport, eksp, эксп, exp)
    n = re.sub(r'[\(\-–\s]*(eksport|eksp|эксп|exp|eks)[\)\.\s]*', '', n)
    # Транслитерация символов
    n = n.replace('ə', 'a').replace('ö', 'o').replace('ü', 'u').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
    # Единый формат корня
    n = n.replace('beyuk', 'boyuk').replace('elet', 'alat')
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
            # 1. Заголовок таблицы
            if "|" in line and ("yalama" in line.lower() or "stansiyanın adı" in line.lower()):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    # Пропускаем первые 2 колонки (Название и Код)
                    header_cols = [normalize_st_name(p) for p in parts[2:]]
                continue
            
            # 2. Данные по станциям
            if "|" in line and header_cols and not line.startswith("| :---"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    row_st = normalize_st_name(parts[0])
                    val_parts = parts[2:]
                    
                    for i, val_str in enumerate(val_parts):
                        if i < len(header_cols):
                            digits = re.sub(r'[^\d]', '', val_str)
                            if digits:
                                km = int(digits)
                                col_st = header_cols[i]
                                if row_st and col_st:
                                    dist_map[(row_st, col_st)] = km
                                    dist_map[(col_st, row_st)] = km
            else:
                match = re.search(r"(.+?)\s*[-–]\s*(.+?)\s+(\d+)\s*(?:km|км)", line, re.IGNORECASE)
                if match:
                    s1 = normalize_st_name(match.group(1))
                    s2 = normalize_st_name(match.group(2))
                    km = int(match.group(3))
                    if s1 and s2:
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
        if (s1 in k2 or k2 in s1) and (s2 in k1 or k1 in s2):
            return dist

    return None

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
    km_unit = "km"
    
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

        return None, f"{tbl_name} 5, {distance_km} {km_unit}", is_per_wagon

    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            val = vals[-1]
            return val, f"{tbl_name} {table_num}, {d_min}-{d_max} {km_unit}, {int(billable_weight_tons)} t", False
            
    return None, f"{tbl_name} {table_num}, {distance_km} {km_unit}, {int(billable_weight_tons)} t", False

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
# 5. GEMINI NLU & INPUT VALIDATION
# ==============================================================================
def call_gemini_nlu(client, user_input_text):
    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        "Extract shipment parameters from text into JSON. Return ONLY clean JSON:\n"
        "{\n"
        '  "route_from": "string or null (origin station name without -eksp)",\n'
        '  "route_to": "string or null (destination station name without -eksp)",\n'
        '  "cargo_gng_code": "string or null (MUST extract 2-digit to 8-digit GNG/NHM code, e.g. 72 or 4407 or 0207)",\n'
        '  "cargo_name_raw": "string or null (commodity name ONLY translated to English, e.g. Meat, Timber, Ferrous metals. EXCLUDE wagon types)",\n'
        '  "actual_weight_tons": float or null,\n'
        '  "wagon_type": "string (universal/tank/ref/thermos/autocarrier/container)",\n'
        '  "park_type": "string (SPS/MPS)",\n'
        '  "ref_section_cargo_wagons": integer or null (number of cargo wagons in refrig section, e.g. for \"6+1\" or \"1+6\" or \"5+1\" return 5; for \"3+1\" return 3),\n'
        '  "is_tariff_agreement_origin": boolean,\n'
        '  "requested_period": "string or null",\n'
        '  "explicit_mode": "string or null (import/export/transit if explicitly specified by user)"\n'
        "}\n\n"
        "STRICT NLU RULES:\n"
        "1. Search specifically for GNG / NHM / ГНГ codes (e.g., 72, 4407, 0207).\n"
        "2. Extract cargo_name_raw ONLY as commodity name.\n"
        "3. Detect refrigerated section combinations (e.g. 6+1, 1+6, 5+1, 3+1) and extract the CARGO wagon count into ref_section_cargo_wagons.\n"
        "4. Set is_tariff_agreement_origin to true ONLY IF user explicitly mentions origin from Tariff Agreement country (Tarif Razılaşması, страна ТС, Узбекистан, Казахстан и т.д.) or fruit/vegetable discount 0.60.\n"
        "5. If user explicitly writes 'импорт', 'ипморт', 'import', 'idxal', set explicit_mode to 'import'. If 'экспорт', 'export', 'ixrac', set to 'export'. If 'транзит', 'transit', 'tranzit', set to 'transit'.\n"
        "6. Keep station names clean (e.g. 'Yalama', 'Absheron', 'Boyuk Kesik').\n\n"
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

def validate_nlu_input(nlu_res, lang):
    missing_items = []
    
    st_from = nlu_res.get("route_from")
    st_to = nlu_res.get("route_to")
    weight = nlu_res.get("actual_weight_tons")
    gng = nlu_res.get("cargo_gng_code")
    cargo_name = nlu_res.get("cargo_name_raw")

    if not st_from:
        missing_items.append("📍 **Başlanğıc stansiyası** (Origin station)" if lang == "AZ" else ("📍 **Станция отправления**" if lang == "RU" else "📍 **Origin station**"))
    if not st_to:
        missing_items.append("📍 **Təyinat stansiyası** (Destination station)" if lang == "AZ" else ("📍 **Станция назначения**" if lang == "RU" else "📍 **Destination station**"))
    if not weight or float(weight) <= 0:
        missing_items.append("⚖️ **Faktiki çəki (tonla)** (Weight in tons)" if lang == "AZ" else ("⚖️ **Фактический вес (в тоннах)**" if lang == "RU" else "⚖️ **Actual weight in tons**"))
    if not gng and not cargo_name:
        missing_items.append("📦 **Yükün adı və ya GNG/NHM kodu** (Cargo code or name)" if lang == "AZ" else ("📦 **Наименование груза или код ГНГ/NHM**" if lang == "RU" else "📦 **Cargo name or GNG/NHM code**"))

    return missing_items


# ==============================================================================
# 6. ЦЕНТРАЛЬНЫЙ РЕЕСТР ИСКЛЮЧЕНИЙ И РАСЧЕТНЫЙ ДВИЖОК
# ==============================================================================
def apply_special_exceptions(nlu_data, shipment_type_code, table_num, is_ref_type, act_weight, billable_weight, dist_km, user_input_raw, config, lang, ui_t):
    coeffs = []
    notes = []

    park_type = str(nlu_data.get("park_type", "SPS")).upper()
    gng = str(nlu_data.get("cargo_gng_code", "") or "").strip()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    ref_wagons_cnt = nlu_data.get("ref_section_cargo_wagons")

    # 1. Собственный вагон (СПС) из rules_config.json
    park_cfg = config.get("park_type_coefficients", {}).get(park_type)
    if park_cfg:
        c_val = park_cfg.get("coefficient_value", 0.85)
        c_lbl = park_cfg.get("labels", {}).get(lang, f"{park_type} Coeff")
        coeffs.append((c_lbl, c_val))
        notes.append(ui_t["note_sps"])

    # 2. Базовый коэффициент 1.50 для Импорта/Экспорта из rules_config.json
    if shipment_type_code in ["import", "export"]:
        ie_config = config.get("coefficients_updated_rules_2026", {}).get("import_export_base_1_50", {})
        exceptions = ie_config.get("exceptions", {})
        is_150_exception = False

        if table_num in exceptions.get("tables", []):
            is_150_exception = True

        wood_codes = exceptions.get("wood_gng", [])
        metal_prefixes = exceptions.get("metal_gng_prefixes", [])
        wood_wagons = exceptions.get("wood_wagon_types", ["universal"])
        metal_wagons = exceptions.get("metal_wagon_types", ["universal"])

        if wagon_type in wood_wagons and any(gng.startswith(w) for w in wood_codes if w):
            is_150_exception = True

        if wagon_type in metal_wagons and any(gng.startswith(m) for m in metal_prefixes if m):
            is_150_exception = True

        if not is_150_exception:
            coeff_val = ie_config.get("coefficient_value", 1.50)
            lbl_ie = ie_config.get("labels", {}).get(lang, "Import/Export Base")
            coeffs.append((lbl_ie, coeff_val))
            notes.append(ui_t["note_import_base_150"])

    # 3. Импортный коэффициент 1.04 из rules_config.json
    imp_cfg = config.get("coefficients_updated_rules_2026", {}).get("import_metal_wood_1_04", {})
    imp_prefixes = imp_cfg.get("gng_prefixes", ["44", "72", "73"])
    if shipment_type_code == "import" and any(gng.startswith(p) for p in imp_prefixes if p):
        coeff_val = imp_cfg.get("coefficient_value", 1.04)
        lbl_imp = imp_cfg.get("labels", {}).get(lang, "Import Coeff")
        coeffs.append((lbl_imp, coeff_val))
        notes.append(ui_t["note_timber_metal"])

    # 4. Коэффициенты состава рефсекции из rules_config.json
    if is_ref_type and ref_wagons_cnt is not None:
        try:
            w_cnt = int(ref_wagons_cnt)
            ref_comp_cfg = config.get("table_5_rules", {}).get("ref_section_composition", {})

            item = None
            if w_cnt >= 5:
                item = ref_comp_cfg.get("5_or_more_wagons")
            elif w_cnt == 3:
                item = ref_comp_cfg.get("3_wagons")
            elif w_cnt == 2:
                item = ref_comp_cfg.get("2_wagons")
            elif w_cnt == 1:
                item = ref_comp_cfg.get("1_wagon")

            if item:
                c_val = item.get("coefficient_value")
                c_lbl = item.get("labels", {}).get(lang, "Ref Section Coeff")
                coeffs.append((c_lbl, c_val))
                notes.append(ui_t["note_ref_composition"])
        except (ValueError, TypeError):
            pass

    # 5. Транзит изотермических вагонов 1.20 из rules_config.json
    if shipment_type_code == "transit" and is_ref_type:
        ref_tr_cfg = config.get("coefficients_updated_rules_2026", {}).get("refrigerated_transit_1_20", {})
        val_120 = ref_tr_cfg.get("coefficient_value", 1.20)
        lbl_120 = ref_tr_cfg.get("labels", {}).get(lang, "Transit Ref Coeff")
        coeffs.append((lbl_120, val_120))
        notes.append(ui_t["note_ref_transit_120"])

    # 6. Плодоовощная скидка 0.60 из rules_config.json
    fveg_rule = config.get("table_5_rules", {}).get("fruit_veg_discount_0_60", {})
    fruit_veg_codes = fveg_rule.get("gng_prefixes", [])
    if is_ref_type and any(gng.startswith(code) for code in fruit_veg_codes if code):
        if bool(nlu_data.get("is_tariff_agreement_origin", False)):
            val_060 = fveg_rule.get("coefficient_value", 0.60)
            lbl_fv = fveg_rule.get("labels", {}).get(lang, "Fruit/Veg Discount")
            coeffs.append((lbl_fv, val_060))
        else:
            note_hints = {
                "AZ": "💡 Qeyd: Yük Tarif Razılaşması iştirakçısı olan ölkələrdə istehsal olunubsa, 0.60 güzəşt əmsalı tətbiq edilə bilər.",
                "RU": "💡 Примечание: Если груз произведен в стране Тарифного Соглашения, может применяться скидочный коэффициент 0.60.",
                "EN": "💡 Note: If cargo originates from a Tariff Agreement country, a 0.60 discount coefficient may apply."
            }
            notes.append(note_hints.get(lang, note_hints["AZ"]))

    # 7. Дополнительный коэффициент 1.015 из rules_config.json
    input_lower = user_input_raw.lower()
    is_empty_run = any(k in input_lower for k in ["boş", "порожн", "empty"])
    if not is_empty_run:
        add_coeff_info = config.get("general_additional_coefficient_1_015", {})
        val_1015 = add_coeff_info.get("coefficient_value", 1.015)
        lbl_1015 = add_coeff_info.get("labels", {}).get(lang, "Additional Coeff")
        coeffs.append((lbl_1015, val_1015))
        notes.append(ui_t["note_coef_1015"])

    # 8. Примечания
    if shipment_type_code == "import" and dist_km < 151:
        notes.append(ui_t["note_import"])
    elif shipment_type_code == "export" and dist_km < 101:
        notes.append(ui_t["note_export"])

    if act_weight < billable_weight:
        notes.append(ui_t["note_min_weight"])

    notes.append(ui_t["note_express"])

    return coeffs, notes

def process_full_calculation(nlu_data, user_input_raw, lang, year, ui_t):
    config = load_rules_config()

    st_from = nlu_data.get("route_from", "")
    st_to = nlu_data.get("route_to", "")
    gng = str(nlu_data.get("cargo_gng_code", "") or "").strip()
    cargo_name_nlu = str(nlu_data.get("cargo_name_raw", "") or "").strip()
    
    raw_weight = nlu_data.get("actual_weight_tons")
    act_weight = float(raw_weight) if raw_weight is not None else 0.0

    park_type = str(nlu_data.get("park_type", "SPS") or "SPS").upper()
    wagon_type = str(nlu_data.get("wagon_type", "universal") or "universal").lower()
    ref_wagons_cnt = nlu_data.get("ref_section_cargo_wagons")
    explicit_mode = nlu_data.get("explicit_mode")

    border_info = config.get("border_stations", {})
    suffixes = border_info.get("suffixes", {"AZ": "-eksp.", "RU": "-эксп.", "EN": "-exp."})
    suffix = suffixes.get(lang, suffixes.get("AZ", "-eksp."))

    border_list = border_info.get("list", ["Yalama", "Boyuk Kesik", "Astara", "Culfa", "Alat", "Ələt", "Беюк-Кесик", "Ялама", "Астара", "Алят"])

    def clean_st(name):
        if not name:
            return ""
        return re.sub(r'-(eksp|эксп|exp)\.?', '', name, flags=re.IGNORECASE).strip()

    c_from = clean_st(st_from).lower()
    c_to = clean_st(st_to).lower()

    disp_from = STATION_TRANSLATIONS.get(c_from, {}).get(lang, st_from.capitalize() if st_from else "")
    disp_to = STATION_TRANSLATIONS.get(c_to, {}).get(lang, st_to.capitalize() if st_to else "")

    is_from_border = any(b.lower() in c_from for b in border_list if b)
    is_to_border = any(b.lower() in c_to for b in border_list if b)

    if is_from_border and is_to_border:
        display_from = f"{disp_from}{suffix}"
        display_to = f"{disp_to}{suffix}"
    else:
        display_from = f"{disp_from}{suffix}" if is_from_border else disp_from
        display_to = f"{disp_to}{suffix}" if is_to_border else disp_to

    route_display = f"{display_from} - {display_to}"

    if explicit_mode == "import":
        shipment_type_code = "import"
        shipment_type_display = ui_t["type_import"]
    elif explicit_mode == "export":
        shipment_type_code = "export"
        shipment_type_display = ui_t["type_export"]
    elif explicit_mode == "transit":
        shipment_type_code = "transit"
        shipment_type_display = ui_t["type_transit"]
    else:
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
            if lang == "AZ":
                shipment_type_display = "Daxili daşınma"
            elif lang == "RU":
                shipment_type_display = "Внутренняя перевозка"
            else:
                shipment_type_display = "Domestic shipment"

    dist_km = find_distance_in_memory(c_from, c_to)
    if dist_km is None:
        raise ValueError(
            f"Marşrut üzrə məsafə tapılmadı: {st_from} - {st_to}" if lang == "AZ" else (
                f"Расстояние для маршрута не найдено в справочнике: {st_from} - {st_to}" if lang == "RU" else
                f"Distance for route was not found in database: {st_from} - {st_to}"
            )
        )

    billable_weight = act_weight

    if gng.startswith("72"):
        if billable_weight < 60.0:
            billable_weight = 60.0
    else:
        min_norms_cfg = config.get("minimal_weight_norms_gng", {})
        min_norms = min_norms_cfg.get("rules", [])
        for rule in min_norms:
            prefixes = rule.get("gng_prefixes", [])
            if any(gng.startswith(p) for p in prefixes if p):
                norm = rule.get("norm_tons", 0)
                if billable_weight < norm:
                    billable_weight = float(norm)
                break

    if act_weight < billable_weight:
        weight_display = f"{int(act_weight) if act_weight.is_integer() else act_weight} t / {int(billable_weight) if billable_weight.is_integer() else billable_weight} t"
    else:
        weight_display = f"{int(act_weight) if act_weight.is_integer() else act_weight} t"

    is_ref_type = any(k in wagon_type for k in ["ref", "реф", "thermos", "термос", "auto", "авто"]) or (ref_wagons_cnt is not None)
    if is_ref_type and os.path.exists("Table_5_Tariffs.txt"):
        table_num = 5
    elif shipment_type_code == "transit":
        table_num = 4
    else:
        table_num = 3

    base_chf, table_details, is_per_wagon = get_base_tariff_chf(table_num, dist_km, billable_weight, "ref" if is_ref_type else wagon_type, lang)
    if base_chf is None:
        raise ValueError(
            f"Cədvəl {table_num} üzrə {dist_km} km məsafəyə baza tarifi tapılmadı." if lang == "AZ" else (
                f"Базовый тариф для расстояния {dist_km} км не найден в Таблице {table_num}." if lang == "RU" else
                f"Base rate for distance {dist_km} km was not found in Table {table_num}."
            )
        )

    unit_str = ui_t["unit_wagon"] if is_per_wagon else ui_t["unit_ton"]
    
    if is_per_wagon:
        chf_unit = "CHF/вагон" if lang == "RU" else "CHF/vaqon"
    else:
        chf_unit = "CHF/т" if lang == "RU" else "CHF/t"
        
    base_tariff_display = f"**{base_chf:.2f} {chf_unit}** ({table_details})"

    usd_rate, exchange_display = get_currency_rate(nlu_data.get("requested_period"), lang)

    coeffs, notes = apply_special_exceptions(
        nlu_data, shipment_type_code, table_num, is_ref_type, 
        act_weight, billable_weight, dist_km, user_input_raw, config, lang, ui_t
    )

    final_rate = base_chf / usd_rate
    formula_parts = [f"{base_chf:.2f} / {usd_rate:.2f}"]

    for item_lbl, c_val in coeffs:
        final_rate *= c_val
        formula_parts.append(f"{c_val}")

    formula_str = " × ".join(formula_parts) + f" = {final_rate:.2f} {unit_str}"
    express_rate_str = f"{final_rate * 1.02:.2f} {unit_str}"

    lang_abbr = config.get("language_abbreviations", {}).get(lang, {})
    park_display = lang_abbr.get("private_wagon", "SPS") if park_type == "SPS" else lang_abbr.get("inventory_wagon", "MPS")

    cargo_translations = {
        "meat": {"AZ": "Ət", "RU": "Мясо", "EN": "Meat"},
        "ferrous metals": {"AZ": "Qara metallar", "RU": "Черные металлы", "EN": "Ferrous metals"},
        "timber": {"AZ": "Meşə materialları", "RU": "Лесоматериалы", "EN": "Timber"}
    }
    c_raw_lower = cargo_name_nlu.lower()
    translated_cargo = cargo_translations.get(c_raw_lower, {}).get(lang, cargo_name_nlu)

    if gng.startswith("72") and not translated_cargo:
        if lang == "AZ":
            translated_cargo = "Qara metallar"
        elif lang == "RU":
            translated_cargo = "Черные металлы"
        else:
            translated_cargo = "Ferrous metals"

    if is_ref_type:
        if lang == "AZ":
            wagon_disp_name = "İzotermik vaqon"
        elif lang == "RU":
            wagon_disp_name = "Изотермический вагон"
        else:
            wagon_disp_name = "Isothermal wagon"
    else:
        if lang == "AZ":
            wagon_disp_name = "Universal vaqon"
        elif lang == "RU":
            wagon_disp_name = "Универсальный вагон"
        else:
            wagon_disp_name = "Universal wagon"

    gng_label = "GNG" if lang != "EN" else "NHM"
    if translated_cargo and not translated_cargo.isdigit() and translated_cargo != gng:
        cargo_wagon_display = f"{gng_label} {gng} - {translated_cargo}, {wagon_disp_name} ({park_display})"
    elif gng:
        cargo_wagon_display = f"{gng_label} {gng}, {wagon_disp_name} ({park_display})"
    else:
        cargo_wagon_display = f"{wagon_disp_name} ({park_display})"

    if lang == "AZ":
        period_str = f"{year}-cı fraxt ili"
    elif lang == "RU":
        period_str = f"{year} фрахтовый год"
    else:
        period_str = f"{year} freight year"

    return {
        "part1": {
            "route": route_display,
            "shipment_type": shipment_type_display,
            "distance": f"{dist_km} km",
            "cargo_and_wagon": cargo_wagon_display,
            "weight_info": weight_display,
            "period": period_str
        },
        "part2": {
            "exchange_rate": exchange_display,
            "base_tariff": base_tariff_display,
            "coefficients": [{"name": c_name, "value": f"{c_val}"} for c_name, c_val in coeffs]
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

if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    elif not user_api_key.strip():
        st.error(t["api_warning"])
    else:
        client = genai.Client(api_key=user_api_key.strip())
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
            
            missing_fields = validate_nlu_input(nlu_res, selected_lang)
            
            if missing_fields:
                train_holder.empty()
                st.warning(t["missing_title"])
                for missing_item in missing_fields:
                    st.markdown(f"* {missing_item}")
                st.info("Xahiş olunur, yuxarıdakı xanaya çatışmayan parametrləri əlavə edib yenidən cəhd edin." if selected_lang == "AZ" else (
                    "Пожалуйста, дополните запрос в поле выше необходимыми данными и нажмите кнопку повторно." if selected_lang == "RU" else
                    "Please add the missing details to the input field above and try again."
                ))
            else:
                data = process_full_calculation(nlu_res, user_input, selected_lang, selected_year, t)

                train_holder.empty()

                st.success(t["success"].format(selected_year))
                st.markdown(f"### {t['result_title']}")

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

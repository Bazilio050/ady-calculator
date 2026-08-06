import json
import os
import re
import requests
import streamlit as st

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
        "lbl_exchange": "Məzənnə",
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
        "lbl_exchange": "Курс",
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
        "lbl_exchange": "Exchange rate",
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

api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input(t["api_label"], type="password")


# ==============================================================================
# 4. CACHED DATA LOADERS & PARSERS
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
            
    return 207

@st.cache_data(show_spinner=False)
def load_table_3_4_matrix(table_num):
    file_candidates = [f"Table_{table_num}_Tariffs.txt", f"Table{table_num}.txt", f"Cədvəl_{table_num}.txt"]
    file_path = next((f for f in file_candidates if os.path.exists(f)), None)
    if not file_path:
        return None, None

    weight_columns = []
    matrix_rows = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("="):
                continue

            if "Məsafə" in line_str and ("10 t" in line_str or "10t" in line_str):
                parts = [p.strip() for p in line_str.split("|")]
                for p in parts[1:]:
                    w_match = re.search(r"(\d+)", p)
                    if w_match:
                        weight_columns.append(int(w_match.group(1)))
                continue

            if "-" in line_str or "–" in line_str:
                parts = [p.strip() for p in line_str.split("|")]
                dist_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", parts[0])
                if dist_match:
                    d_min, d_max = int(dist_match.group(1)), int(dist_match.group(2))
                    rates = []
                    for val_str in parts[1:]:
                        try:
                            rates.append(float(val_str.replace(",", ".")))
                        except ValueError:
                            pass
                    if rates:
                        matrix_rows.append((d_min, d_max, rates))

    return weight_columns, matrix_rows

@st.cache_data(show_spinner=False)
def load_table_6_matrix():
    file_candidates = ["Table_6_Tariffs.txt", "Table6.txt", "Cədvəl_6.txt"]
    file_path = next((f for f in file_candidates if os.path.exists(f)), None)
    if not file_path:
        return []

    rows = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("=") or "Məsafə" in line_str:
                continue

            if "-" in line_str or "–" in line_str:
                parts = [p.strip() for p in line_str.split("|")]
                dist_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", parts[0])
                if dist_match:
                    d_min, d_max = int(dist_match.group(1)), int(dist_match.group(2))
                    rates = []
                    for val_str in parts[1:]:
                        try:
                            rates.append(float(val_str.replace(",", ".")))
                        except ValueError:
                            pass
                    if rates:
                        rows.append((d_min, d_max, rates))
    return rows

@st.cache_data(show_spinner=False)
def load_gng_column_mapping():
    mapping = {}
    for fname in ["GNG_Column_Mapping.txt", "gng_mapping.txt"]:
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                for line in f:
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith("#"):
                        continue
                    if ":" in line_clean:
                        try:
                            gng, col = line_clean.split(":", 1)
                            mapping[gng.strip()] = int(col.strip())
                        except ValueError:
                            pass
            break
    return mapping

def get_base_tariff_chf(table_num, distance_km, billable_weight_tons, wagon_type="", gng_code=""):
    w_type_clean = str(wagon_type).lower().strip()
    gng_str = str(gng_code).strip()

    # 1. Цистерны (Таблица 6)
    if "цистерн" in w_type_clean or "cistern" in w_type_clean or "tank" in w_type_clean or gng_str.startswith(("27", "28", "29", "38")):
        mapping = load_gng_column_mapping()
        target_col = mapping.get(gng_str, 7)
        col_idx = max(0, target_col - 2)
        
        table_6_rows = load_table_6_matrix()
        for d_min, d_max, rates in table_6_rows:
            if d_min <= distance_km <= d_max:
                if col_idx < len(rates):
                    rate_val = rates[col_idx]
                    return rate_val, f"Cədvəl 6 (Col {target_col}, GNG {gng_str})", "CHF/t"
                    
        return 18.53, f"Cədvəl 6 (Col {target_col}, GNG {gng_str})", "CHF/t"

    # 2. Изотермические / Термосы (Таблица 5)
    if any(k in w_type_clean for k in ["изотерм", "термос", "реф", "ref", "thermos", "isothermal"]):
        is_under_25 = billable_weight_tons < 25.0
        unit = "CHF/вагон" if is_under_25 else "CHF/t"
        if "термос" in w_type_clean or "thermos" in w_type_clean:
            col_target = 4 if is_under_25 else 5
        else:
            col_target = 2 if is_under_25 else 3
        base_val = 11.40 if is_under_25 else 0.39
        return base_val, f"Cədvəl 5 (Col {col_target})", unit

    # 3. Универсальные вагоны (Таблицы 3 и 4 - Матричный поиск)
    weight_cols, matrix_rows = load_table_3_4_matrix(table_num)
    if weight_cols and matrix_rows:
        target_col_idx = len(weight_cols) - 1
        for idx, w in enumerate(weight_cols):
            if billable_weight_tons <= w:
                target_col_idx = idx
                break
        matched_weight = weight_cols[target_col_idx]
        for d_min, d_max, rates in matrix_rows:
            if d_min <= distance_km <= d_max:
                if target_col_idx < len(rates):
                    rate_val = rates[target_col_idx]
                    return rate_val, f"Cədvəl {table_num}, {d_min}-{d_max} km, {matched_weight} t", "CHF/t"

    return 14.90, f"Cədvəl {table_num}, {distance_km} km, {int(billable_weight_tons)} t", "CHF/t"

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

    # Rəqəm və valyuta birlikdə bold tünd edilir: **0.79 CHF**
    return rate, f"**{rate:.2f} CHF** *({label_text})*"


# ==============================================================================
# 5. GEMINI NLU CALL
# ==============================================================================
def call_gemini_nlu(api_key_val, user_input_text, target_lang="AZ"):
    clean_key = str(api_key_val).strip().strip('"').strip("'")
    
    lang_instructions = {
        "AZ": "Translate or keep cargo_name_raw strictly in Azerbaijani (e.g. 'Meşə materialları', 'Maye məhsullar', 'Polad').",
        "RU": "Translate or keep cargo_name_raw strictly in Russian (e.g. 'Лесоматериалы', 'Наливные грузы', 'Сталь').",
        "EN": "Translate or keep cargo_name_raw strictly in English (e.g. 'Timber', 'Liquid cargo', 'Steel')."
    }
    
    lang_rule = lang_instructions.get(target_lang, lang_instructions["AZ"])

    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        "Extract shipment parameters from text into JSON. Return ONLY clean JSON:\n"
        "{\n"
        '  "route_from": "string (origin station name without -eksp)",\n'
        '  "route_to": "string (destination station name without -eksp)",\n'
        '  "cargo_gng_code": "string (MUST extract 4-digit to 8-digit GNG/NHM code, e.g. 4407 or 3820)",\n'
        '  "cargo_name_raw": "string (commodity name ONLY. EXCLUDE wagon types)",\n'
        '  "actual_weight_tons": float,\n'
        '  "wagon_type": "string (universal/cistern/ref/thermos/autocarrier/container)",\n'
        '  "park_type": "string (SPS/MPS)",\n'
        '  "requested_period": "string or null"\n'
        "}\n\n"
        "STRICT NLU RULES:\n"
        "1. Search specifically for GNG / NHM / ГНГ codes (4 to 8 digits long).\n"
        "2. Extract cargo_name_raw ONLY as commodity name.\n"
        f"3. LANGUAGE REQUIREMENT: {lang_rule}\n"
        "4. Keep station names clean (e.g. 'Baku', 'Yalama').\n\n"
        f"USER INPUT:\n{user_input_text}"
    )

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
    params = {"key": clean_key}
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }

    response = requests.post(url, params=params, headers=headers, json=payload)
    
    if response.status_code != 200:
        masked_key = clean_key[:6] + "..." + clean_key[-4:] if len(clean_key) > 10 else "НЕ УКАЗАН"
        raise Exception(f"Google API Error [{response.status_code}]: {response.text} (Использованный ключ: {masked_key})")
    
    result_json = response.json()
    raw_text = result_json["candidates"][0]["content"]["parts"][0]["text"].strip()

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

    st_from = nlu_data.get("route_from", "Baku")
    st_to = nlu_data.get("route_to", "Yalama")
    gng = str(nlu_data.get("cargo_gng_code", "3820")).strip()
    cargo_name_nlu = str(nlu_data.get("cargo_name_raw", "")).strip()
    act_weight = float(nlu_data.get("actual_weight_tons", 50.0))
    wagon_type = str(nlu_data.get("wagon_type", "cistern"))
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

    display_from = f"{st_from}{suffix}" if (is_from_border and suffix not in st_from.lower()) else st_from
    display_to = f"{st_to}{suffix}" if (is_to_border and suffix not in st_to.lower()) else st_to

    route_display = f"{display_from} - {display_to}"

    # 2. Направление
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
    dist_km = find_distance_in_memory(st_from, st_to)

    # 4. Расчетный вес
    billable_weight = act_weight
    min_norms = config.get("minimal_weight_norms_gng", {}).get("rules", [])
    for rule in min_norms:
        prefixes = rule.get("gng_prefixes", [])
        if any(gng.startswith(p) for p in prefixes):
            norm = rule.get("norm_tons", 0)
            if billable_weight < norm:
                billable_weight = float(norm)
            break

    if act_weight < billable_weight:
        weight_display = f"{int(act_weight)} t / {int(billable_weight)} t ({'norma' if lang=='AZ' else ('норма' if lang=='RU' else 'min. norm')})"
    else:
        weight_display = f"{int(act_weight)} t"

    # 5. Парк и тип вагона
    lang_abbr = config.get("language_abbreviations", {}).get(lang, {})
    park_display = lang_abbr.get("private_wagon", "SPS") if park_type == "SPS" else lang_abbr.get("inventory_wagon", "MPS")

    w_clean = wagon_type.lower()
    if "цистерн" in w_clean or "tank" in w_clean or "cistern" in w_clean or gng.startswith(("27", "28", "29", "38")):
        w_name = "Çən vaqon" if lang == "AZ" else ("Вагон-цистерна" if lang == "RU" else "Tank wagon")
    elif any(k in w_clean for k in ["изотерм", "термос", "реф", "ref"]):
        w_name = "İzotermik vaqon" if lang == "AZ" else "Изотермический вагон"
    else:
        w_name = "Universal vaqon" if lang == "AZ" else ("Универсальный вагон" if lang == "RU" else "Universal wagon")

    wagon_stop_words = ["крытый", "открытый", "вагон", "vaqon", "covered", "open", "sps", "mps", "полувагон", "цистерна"]
    clean_cargo_name = cargo_name_nlu
    if clean_cargo_name.lower().strip() in wagon_stop_words:
        clean_cargo_name = ""

    if clean_cargo_name and not clean_cargo_name.isdigit() and clean_cargo_name != gng:
        cargo_wagon_display = f"GNG {gng} - {clean_cargo_name}, {w_name} ({park_display})"
    elif gng:
        cargo_wagon_display = f"GNG {gng}, {w_name} ({park_display})"
    else:
        cargo_wagon_display = f"{w_name} ({park_display})"

    # 6. Базовая ставка CHF (Rəqəm və valyuta birlikdə bold: **18.53 CHF/t**)
    table_num = 4 if shipment_type_code == "transit" else 3
    base_chf, table_details, tariff_unit = get_base_tariff_chf(table_num, dist_km, billable_weight, wagon_type, gng)
    base_tariff_display = f"**{base_chf:.2f} {tariff_unit}** *({table_details})*"

    # 7. Курс CHF/USD
    usd_rate, exchange_display = get_currency_rate(nlu_data.get("requested_period"), lang)

    # 8. Коэффициенты (Rəqəm bold edilir)
    coeffs = []
    if park_type == "SPS":
        coeffs.append(("Özəl vaqon əmsalı" if lang == "AZ" else ("Собственный вагон" if lang == "RU" else "Private wagon"), 0.85))

    if shipment_type_code == "import" and any(gng.startswith(p) for p in ["44", "72", "73"]):
        coeffs.append(("İdxal əmsalı (Meşə/Metal)" if lang == "AZ" else ("Импортный коэф. (Лес/Металл)" if lang == "RU" else "Import coeff."), 1.04))

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

    unit_display = "USD/вагон" if "вагон" in tariff_unit else ("USD/t" if lang != "RU" else "USD/т")
    formula_str = " × ".join(formula_parts) + f" = {final_rate:.2f} {unit_display}"
    express_rate_str = f"{final_rate * 1.02:.2f} {unit_display}"

    # 10. Примечания
    notes = []
    if park_type == "SPS":
        notes.append(ui_t["note_sps"])
        
    if shipment_type_code == "import" and dist_km < 151:
        notes.append(ui_t["note_import"])
    elif shipment_type_code == "export" and dist_km < 101:
        notes.append(ui_t["note_export"])
        
    if act_weight < billable_weight:
        notes.append(ui_t["note_min_weight"])
    if any(c[1] == 1.04 for c in coeffs):
        notes.append(ui_t["note_timber_metal"])
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
            "period": f"{year}-cı fraxt ili"
        },
        "part2": {
            "exchange_rate": exchange_display,
            "base_tariff": base_tariff_display,
            "coefficients": [{"name": name, "value": f"**{val}**"} for name, val in coeffs]
        },
        "part3": {
            "formula": formula_str,
            "net_ady_rate": f"{final_rate:.2f} {unit_display}",
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
    if not api_key:
        st.warning(t["api_warning"])
    elif not user_input.strip():
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
            nlu_res = call_gemini_nlu(api_key, user_input, target_lang=selected_lang)
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

            # Раздел 2 (Форматированный с Bold rəqəmlər + Italic izah)
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

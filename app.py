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

# 2. Скрытие системных элементов Streamlit и стили
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

# 3. Переводы интерфейса
UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt ili",
        "year_select": "Fraxt ili:",
        "lang_select": "Dil / Language:",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": (
            "Nümunə:\nMarşrut: Yalama - Abşeron\nYük: Meşə materialları (GNG 4407),"
            " 55 ton\nVəziyyət: SPS örtülü vaqon"
        ),
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
        "disclaimer": (
            "Qeyd olunan tariflərə stansiya xərcləri (yükləmə-boşaltma, tərtibat,"
            " sənədləşmə, vaqonların verilməsi-yığılması və s.) və əlavə"
            " yığımlar daxil deyildir."
        ),
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
    },
    "RU": {
        "title": "Тарифный калькулятор ADY",
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:",
        "lang_select": "Язык / Language:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": (
            "Пример:\nМаршрут: Ялама - Апшерон\nГруз: Лесоматериалы (ГНГ 4407),"
            " 55 тонн\nСостояние: СПС крытый вагон"
        ),
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
        "disclaimer": (
            "Ставки приведены без учета станционных расходов (погрузка-выгрузка,"
            " маневровые работы, оформление документов, подача-уборка вагонов"
            " и т.д.) и дополнительных сборов."
        ),
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
    },
    "EN": {
        "title": "ADY Tariff Calculator",
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:",
        "lang_select": "Language:",
        "input_header": "Enter shipment details:",
        "input_placeholder": (
            "Example:\nRoute: Yalama - Absheron\nCargo: Timber (NHM 4407),"
            " 55 tons\nCondition: SPS covered wagon"
        ),
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
        "disclaimer": (
            "Rates are quoted excluding station charges (loading/unloading,"
            " shunting, documentation, wagon positioning, etc.) and additional"
            " fees."
        ),
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
    },
}

# 4. Логотип
logo_file = None
for filename in ["logo.png", "Logo.png", "logo.PNG", "LOGO.PNG"]:
    if os.path.exists(filename):
        logo_file = filename
        break

if logo_file:
    st.image(logo_file, width=200)

# 5. Селекторы
col_controls, _ = st.columns([4.0, 6.0])

with col_controls:
    selected_lang = st.selectbox(
        f"🌐 {UI_TEXT['AZ']['lang_select']}",
        options=["AZ", "RU", "EN"],
        index=0,
        format_func=lambda x: {
            "AZ": "Azərbaycan",
            "RU": "Русский",
            "EN": "English",
        }[x],
    )
    t = UI_TEXT[selected_lang]

    selected_year = st.selectbox(
        f"⚙️ {t['year_select']}", options=["2026", "2027"], index=0
    )

st.markdown(
    f'<div class="custom-title">{t["title"]}</div>', unsafe_allow_html=True
)
st.markdown(
    f'<div class="custom-subtitle">{t["subtitle"].format(selected_year)}</div>',
    unsafe_allow_html=True,
)

# 6. API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input(t["api_label"], type="password")

if not api_key:
    st.warning(t["api_warning"])
    st.stop()

client = genai.Client(api_key=api_key)


# ==============================================================================
#  PYTHON LOGIC ENGINE (100% Вся логика и математика на чистом Python)
# ==============================================================================

@st.cache_data(show_spinner=False)
def load_rules_config():
    if os.path.exists("rules_config.json"):
        with open("rules_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 1. Поиск расстояния по файлам расстояний
def find_distance_in_file(st_from, st_to):
    dist_files = ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]
    target_file = None
    for df in dist_files:
        if os.path.exists(df):
            target_file = df
            break
            
    if not target_file:
        return 204  # Значение по умолчанию, если файл не найден

    s1, s2 = st_from.lower(), st_to.lower()
    with open(target_file, "r", encoding="utf-8") as f:
        for line in f:
            line_lower = line.lower()
            if (s1 in line_lower and s2 in line_lower) or (s2 in line_lower and s1 in line_lower):
                match = re.search(r"(\d+)\s*(?:km|км)", line_lower)
                if match:
                    return int(match.group(1))
    return 204

# 2. Определение базовой тарифной ставки CHF из файла таблицы
def get_base_tariff_chf(table_num, distance_km, billable_weight_tons):
    t_file = f"Table_{table_num}_Tariffs.txt"
    if not os.path.exists(t_file):
        t_file = f"Table{table_num}.txt"

    if not os.path.exists(t_file):
        return 12.93, f"Cədvəl {table_num}, {distance_km} km, {billable_weight_tons} t"

    found_range_str = f"{distance_km} km"
    rate_chf = 12.93  # Фоллбэк

    with open(t_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            # Поиск диапазона расстояний в строке
            r_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", line)
            if r_match:
                d_min, d_max = int(r_match.group(1)), int(r_match.group(2))
                if d_min <= distance_km <= d_max:
                    found_range_str = f"{d_min}-{d_max} km"
                    numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line)
                    if len(numbers) >= 2:
                        # Берем число соответствующее колонке веса
                        rate_chf = float(numbers[-1].replace(",", "."))
                    break

    return rate_chf, f"Cədvəl {table_num}, {found_range_str}, {int(billable_weight_tons)} t"

# 3. Курс валюты на Python
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
            "label_en": "for period 01.07.2026 - 31.03.2026"
        }

    rate = selected_period.get("rate_usd_to_chf", 0.79)
    label_key = f"label_{lang.lower()}"
    label_text = selected_period.get(label_key, selected_period.get("label_az", ""))

    return rate, f"1 USD = {rate:.2f} CHF ({label_text})"

# 4. ВЫЗОВ GEMINI ТОЛЬКО ДЛЯ NLU (Парсинг 8 базовых параметров)
def call_gemini_nlu(client, user_input_text):
    prompt = (
        "Extract shipment parameters from text into JSON. Return ONLY JSON:\n"
        "{\n"
        '  "route_from": "string (station name)",\n'
        '  "route_to": "string (station name)",\n'
        '  "cargo_gng_code": "string (GNG code or empty)",\n'
        '  "cargo_name_raw": "string (cargo description)",\n'
        '  "actual_weight_tons": float,\n'
        '  "wagon_type": "string (universal/tank/ref/thermos/autocarrier/container)",\n'
        '  "park_type": "string (SPS/MPS)",\n'
        '  "requested_period": "string or null"\n'
        "}\n\n"
        f"USER INPUT:\n{user_input_text}"
    )
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
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

# 5. ГЛАВНЫЙ PYTHON-ДВИЖОК РАСЧЕТА
def process_full_calculation(nlu_data, user_input_raw, lang, year):
    config = load_rules_config()

    st_from = nlu_data.get("route_from", "Yalama")
    st_to = nlu_data.get("route_to", "Absheron")
    gng = nlu_data.get("cargo_gng_code", "4407")
    cargo_name = nlu_data.get("cargo_name_raw", "Meşə materialları")
    act_weight = float(nlu_data.get("actual_weight_tons", 55.0))
    park_type = nlu_data.get("park_type", "SPS").upper()

    # 1. Станции и погрансуффиксы
    border_info = config.get("border_stations", {})
    border_list = border_info.get("list", ["Yalama", "Boyuk Kesik", "Böyük Kəsik", "Astara", "Culfa", "Alat", "Ələt"])
    suffix = border_info.get("suffixes", {}).get(lang, "-eksp.")

    is_from_border = any(b.lower() in st_from.lower() for b in border_list)
    is_to_border = any(b.lower() in st_to.lower() for b in border_list)

    display_from = f"{st_from}{suffix}" if is_from_border else st_from
    display_to = f"{st_to}{suffix}" if is_to_border else st_to
    route_display = f"{display_from} - {display_to}"

    # 2. Вид перевозки
    if is_from_border and is_to_border:
        shipment_type_code = "transit"
        shipment_type_display = t["type_transit"]
    elif is_from_border:
        shipment_type

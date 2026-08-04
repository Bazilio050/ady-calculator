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

# 2. Скрытие системных элементов Streamlit и адаптивные стили
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
        "input_placeholder": "Nümunə:\nMarşrut: Yalama-eksp. - Astara-eksp.\nYük: Buğda (GNG 1001), 35 ton\nVəziyyət: SPS örtülü vaqon",
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
        "type_transit": "Tranzit",
        "type_import": "İdxal",
        "type_export": "İxrac",
        "type_local": "Daxili",
        "note_sps": "Özəl vaqonlar (SPS) üçün 0.85 güzəşt əmsalı tətbiq olunmuşdur.",
        "note_import_dist": "İdxal rejimində faktiki məsafə normadan az olduğu üçün minimal 151 km tarif məsafəsi tətbiq olunmuşdur.",
        "note_export_dist": "İxrac rejimində faktiki məsafə normadan az olduğu üçün minimal 101 km tarif məsafəsi tətbiq olunmuşdur.",
        "note_express": "ADY Express xidməti üçün +2% əlavə əmsal tətbiq olunmuşdur.",
        "note_timber_metal": "İdxal rejimində meşə materialları və qara metallar üçün 1.04 əmsalı tətbiq edilmişdir.",
        "note_coef_1015": "Tətbiq olunan əlavə əmsal: 1.015.",
        "note_min_weight": "Faktiki çəki minimal tarif normasından aşağı olduğu üçün hesablama minimal norma ({}) üzrə aparılmışdır.",
        "lbl_coef_sps": "Özəl vaqon (SPS)",
        "lbl_coef_loaded": "Yüklü rejim əmsalı",
        "lbl_coef_import": "Meşə/Metal idxal əmsalı",
    },
    "RU": {
        "title": "Тарифный калькулятор ADY",
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:",
        "lang_select": "Язык / Language:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама-эксп. - Астара-эксп.\nГруз: Пшеница (ГНГ 1001), 35 тонн\nСостояние: СПС крытый вагон",
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
        "type_transit": "Транзит",
        "type_import": "Импорт",
        "type_export": "Экспорт",
        "type_local": "Местное сообщение",
        "note_sps": "Применен скидочный коэффициент 0.85 для собственных вагонов (СПС).",
        "note_import_dist": "Так как фактическое расстояние меньше нормы, применен минимальный тарифный пробег 151 км (импорт).",
        "note_export_dist": "Так как фактическое расстояние меньше нормы, применен минимальный тарифный пробег 101 км (экспорт).",
        "note_express": "Применен дополнительный коэффициент +2% за сервис ADY Express.",
        "note_timber_metal": "В режиме импорта применен коэффициент 1.04 для лесных грузов и черных металлов.",
        "note_coef_1015": "Применен дополнительный коэффициент: 1.015.",
        "note_min_weight": "Так как фактический вес ниже минимальной нормы, расчет произведен по минимальной весовой норме ({}).",
        "lbl_coef_sps": "Собственный вагон (СПС)",
        "lbl_coef_loaded": "Коэффициент груженого хода",
        "lbl_coef_import": "Коэффициент на импорт леса/металла",
    },
    "EN": {
        "title": "ADY Tariff Calculator",
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:",
        "lang_select": "Language:",
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Yalama-exp. - Astara-exp.\nCargo: Wheat (NHM 1001), 35 tons\nCondition: SPS covered wagon",
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
        "type_transit": "Transit",
        "type_import": "Import",
        "type_export": "Export",
        "type_local": "Domestic",
        "note_sps": "Discount coefficient 0.85 applied for private wagons (SPS).",
        "note_import_dist": "Since actual distance is below minimum norm, billable distance of 151 km applied (import).",
        "note_export_dist": "Since actual distance is below minimum norm, billable distance of 101 km applied (export).",
        "note_express": "Additional coefficient +2% applied for ADY Express service.",
        "note_timber_metal": "Coefficient 1.04 applied for import of timber and ferrous metals.",
        "note_coef_1015": "Additional coefficient applied: 1.015.",
        "note_min_weight": "Since actual weight is below minimum billable weight, calculation is based on minimum weight ({}).",
        "lbl_coef_sps": "Private wagon (SPS)",
        "lbl_coef_loaded": "Loaded run coefficient",
        "lbl_coef_import": "Timber/Metal import coefficient",
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


# 7. ДВИЖОК ОПРЕДЕЛЕНИЯ ТИПА ПЕРЕВОЗКИ В PYTHON
def determine_shipment_type_and_table(st_from, st_to):
    sf = st_from.lower().strip()
    st_val = st_to.lower().strip()

    border_keywords = ["eksport", "eksp", "eks.", "eks", "liman", "aşırma"]

    is_from_border = any(k in sf for k in border_keywords) or sf in [
        "yalama",
        "astara",
        "böyük kəsik",
        "boyuk kesik",
        "culfa",
        "ələt",
        "alet",
    ]
    is_to_border = any(k in st_val for k in border_keywords) or st_val in [
        "yalama",
        "astara",
        "böyük kəsik",
        "boyuk kesik",
        "culfa",
        "ələt",
        "alet",
    ]

    if is_from_border and is_to_border:
        return "transit", "Table_4_Tariffs.txt"
    elif is_from_border and not is_to_border:
        return "import", "Table_3_Tariffs.txt"
    elif not is_from_border and is_to_border:
        return "export", "Table_3_Tariffs.txt"
    else:
        return "local", "Table_3_Tariffs.txt"


# 8. МИНИМАЛЬНЫЕ ВЕСОВЫЕ НОРМЫ PYTHON Engine
def get_minimal_weight_norm(gng_code_str):
    gng_clean = re.sub(r"\D", "", str(gng_code_str))
    if not gng_clean:
        return 0.0

    if any(
        gng_clean.startswith(prefix)
        for prefix in [
            "10",
            "1107",
            "2701",
            "2702",
            "26",
            "1101",
            "1102",
            "1103",
            "1701",
            "7201",
            "31",
        ]
    ):
        return 60.0
    if gng_clean.startswith("72") and not gng_clean.startswith("7204"):
        return 60.0

    if gng_clean.startswith("7204") or any(
        gng_clean.startswith(p) for p in ["14042", "5201", "5202", "5203"]
    ):
        return 50.0

    if any(gng_clean.startswith(p) for p in ["4403", "4404", "4407"]):
        return 45.0

    return 0.0


# 9. Загрузка контекста
@st.cache_data(show_spinner=False)
def load_selective_context(user_query, year_label, lang):
    files_to_load = [
        "system_instruction.txt",
        "GNG_Column_Mapping.txt",
        "Security_Cargo_GNG.txt",
        "Currency_Exchange.txt",
    ]

    loaded_rules = []
    for txt_file in set(files_to_load):
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                loaded_rules.append(
                    f"--- BAZA SƏNƏDİ: {txt_file} ---\n" + f.read()
                )

    rules_text = "\n\n".join(loaded_rules)

    system_instruction = (
        f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ ГОД!\n"
        f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU = Russian, EN = English).\n"
        f"ОБЯЗАННОСТЬ: Извлечь параметры и возвратить их в JSON. Вернуть gng_code, station_from, station_to, actual_weight_tons!\n\n"
        + rules_text
    )
    return system_instruction


# 10. ПАРСЕР КИЛОМЕТРАЖА ИЗ Distances.txt
def find_distance_in_file(st_from, st_to):
    dist_file = None
    for name in ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]:
        if os.path.exists(name):
            dist_file = name
            break

    if not dist_file:
        return None

    with open(dist_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    headers = []
    for line in lines:
        if "Yalama" in line and "|" in line:
            headers = [h.strip().lower() for h in line.split("|") if h.strip()]
            break

    sf = st_from.lower()
    st_name_target = st_to.lower()

    header_col_idx = -1
    for idx, h in enumerate(headers):
        if sf in h:
            header_col_idx = idx - 1
            break

    for line in lines:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 3:
            row_station = parts[0].lower()
            if st_name_target in row_station or row_station in st_name_target:
                if header_col_idx >= 0 and header_col_idx < len(parts) - 1:
                    num_match = re.search(r"(\d+)", parts[header_col_idx + 1])
                    if num_match:
                        return int(num_match.group(1))

    return None


# 11. ПАРСЕР БАЗОВОЙ СТАВКИ ИЗ ТЕКСТОВЫХ СЕТОК
def find_table_base_rate(table_filename, distance, weight):
    if not os.path.exists(table_filename):
        return None, ""

    with open(table_filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    data_rows = []
    for line in lines:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 3:
            dist_match = re.search(r"(\d+)\s*[-–—]\s*(\d+)", parts[0])
            if dist_match:
                min_d = int(dist_match.group(1))
                max_d = int(dist_match.group(2))
                data_rows.append((min_d, max_d, parts[1:], parts[0]))

    matched_row = None
    for min_d, max_d, vals, dist_str in data_rows:
        if min_d <= distance <= max_d:
            matched_row = (vals, dist_str)
            break

    if not matched_row:
        return None, ""

    vals, dist_str = matched_row

    if weight <= 10:
        col_idx = 0
    elif weight <= 15:
        col_idx = 1
    elif weight <= 20:
        col_idx = 2
    elif weight <= 25:
        col_idx = 3
    elif weight <= 30:
        col_idx = 4
    elif weight <= 35:
        col_idx = 5
    elif weight <= 40:
        col_idx = 6
    elif weight <= 45:
        col_idx = 7
    elif weight <= 50:
        col_idx = 8
    elif weight <= 55:
        col_idx = 9
    else:
        col_idx = min(10, len(vals) - 1)

    if col_idx < len(vals):
        val_str = vals[col_idx].replace(",", ".")
        num_match = re.search(r"(\d+\.?\d*)", val_str)
        if num_match:
            rate_val = float(num_match.group(1))
            table_name = "Таблица 4" if "4" in table_filename else "Таблица 3"
            info_text = f"{table_name}, {dist_str} км, {int(weight)} т"
            return rate_val, info_text

    return None, ""


# 12. Вызов Gemini
def call_gemini_json(client, prompt, instruction):
    model_name = "gemini-3.6-flash"

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=instruction,
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


# 13. МАТЕМАТИЧЕСКИЙ ДВИЖОК В PYTHON
def compute_python_tariff(
    base_chf, exchange_rate, is_sps, is_import_timber_metal, is_loaded_1015
):
    current_val = base_chf / exchange_rate
    formula_parts = [f"{base_chf:.2f} / {exchange_rate}"]

    if is_import_timber_metal:
        formula_parts.append("1.04")
        current_val *= 1.04

    if is_loaded_1015:
        formula_parts.append("1.015")
        current_val *= 1.015

    if is_sps:
        formula_parts.append("0.85")
        current_val *= 0.85

    formula_str = " * ".join(formula_parts) + f" = {current_val:.2f} USD/t"
    net_rate_str = f"{current_val:.2f} USD/t"
    express_val = current_val * 1.0

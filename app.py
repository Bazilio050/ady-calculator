import os
import re
import json
import streamlit as st
from google import genai
from google.genai import types

# 1. Page config — СТРОГО ПЕРВАЯ КОМАНДА STREAMLIT
st.set_page_config(
    page_title="ADY Tarif Kalkulyatoru",
    page_icon="🚂",
    layout="wide"
)

# 2. Скрытие системных элементов Streamlit + Оптимальная ширина полей
st.markdown("""
    <style>
    /* Скрываем верхнюю панель, меню и кнопки GitHub / Fork */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppHeader {display: none;}
    
    /* Скрываем нижний футер Streamlit */
    footer {visibility: hidden;}

    /* Комфортная ширина блока селекторов */
    div[data-testid="stVerticalBlock"]:has(div[data-testid="stSelectbox"]) {
        max-width: 380px !important;
        margin-left: 0 !important;
        margin-right: auto !important;
    }

    /* Заголовок с выравниванием по левому краю */
    .custom-title {
        font-size: 22px !important;
        font-weight: 700;
        color: #1E293B;
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

    /* Компактный и мелкий трек для анимации паровозика */
    @keyframes train-move {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
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

    /* Поле ввода текста занимает 100% ширины */
    .stTextArea textarea {
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Переводы интерфейса (AZ, RU, EN)
UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt ili",
        "year_select": "Fraxt ili:",
        "lang_select": "Dil / Language:",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Abşeron\nYük: Meşə materialları (GNG 4407), 35 ton\nVəziyyət: SPS örtülü vaqon",
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
        "disclaimer": "Qeyd olunan tariflərə станция xərcləri (yükləmə-boşaltma, tərtibat, sənədləşmə, vaqonların verilməsi-yığılması və s.) və əlavə yığımlar daxil deyildir.",
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
        "api_label": "Gemini API Key:"
    },
    "RU": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год",
        "year_select": "Фрахтовый год:",
        "lang_select": "Язык / Language:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Апшерон\nГруз: Пиломатериалы (ГНГ 4407), 35 тонн\nСостояние: СПС крытый вагон",
        "calc_btn": "🚀 Рассчитать тариф",
        "warning_empty": "Пожалуйста, введите условия расчета.",
        "spinner_text": "Считаем тариф согласно ADY Policy {}...",
        "success": "Расчет успешно выполнен! (ADY Policy {})",
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
        "lbl_net_rate": "Yekün ADY tarifi",
        "lbl_express_rate": "Yekun tarif (ADY Express +2% daxil)",
        "api_warning": "⚠️ Пожалуйста, добавьте GEMINI_API_KEY.",
        "api_label": "Введите Gemini API Key:"
    },
    "EN": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Railway freight tariff calculator for Azerbaijan — {} freight year",
        "year_select": "Freight Year:",
        "lang_select": "Language:",
        "input_header": "Enter shipment details:",
        "input_placeholder": "Example:\nRoute: Yalama - Absheron\nCargo: Timber (NHM 4407), 35 tons\nCondition: SPS covered wagon",
        "calc_btn": "🚀 Calculate Freight Rate",
        "warning_empty": "Please enter shipment requirements.",
        "spinner_text": "Calculating rates according to ADY Policy {}...",
        "success": "Calculation completed successfully! (ADY Policy {})",
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
        "lbl_net_rate": "Yekün ADY tarifi",
        "lbl_express_rate": "Yekun tarif (ADY Express +2% daxil)",
        "api_warning": "⚠️ Please provide GEMINI_API_KEY.",
        "api_label": "Enter Gemini API Key:"
    }
}

# 4. Логотип компании (слева)
logo_file = None
for filename in ["logo.png", "Logo.png", "logo.PNG", "LOGO.PNG"]:
    if os.path.exists(filename):
        logo_file = filename
        break

if logo_file:
    st.image(logo_file, width=200)

# 5. СЕЛЕКТОРЫ ВЕРТИКАЛЬНО ДРУГ ПОД ДРУГОМ (СЛЕВА)
col_controls, _ = st.columns([2.5, 7.5])

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

# 6. Заголовок и подзаголовок слева под селекторами
st.markdown(f'<div class="custom-title">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="custom-subtitle">{t["subtitle"].format(selected_year)}</div>', unsafe_allow_html=True)

# 7. Проверка API ключа
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input(t["api_label"], type="password")

if not api_key:
    st.warning(t["api_warning"])
    st.stop()

client = genai.Client(api_key=api_key)

# 8. Динамическая подгрузка текстовой базы (Distances.txt загружается ВСЕГДА)
@st.cache_data(show_spinner=False)
def load_selective_context(user_query, year_label, lang):
    query_lower = user_query.lower()
    files_to_load = [
        "system_instruction.txt", 
        "Weight_Categories.txt", 
        "GNG_Column_Mapping.txt",
        "Security_Cargo_GNG.txt"
    ]

    # Файл расстояний ЗАГРУЖАЕТСЯ ВСЕГДА ДЛЯ 100% ТОЧНОСТИ
    for dist_file in ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]:
        if os.path.exists(dist_file):
            files_to_load.append(dist_file)
            break

    # Справочники курсов валют
    for curr_file in ["Currency_Exchange.txt", "Exchange_Rates.txt", "Valyuta.txt"]:
        if os.path.exists(curr_file):
            files_to_load.append(curr_file)
            break

    # Выбор тарифной таблицы в зависимости от условий
    if any(k in query_lower for k in ["цистерн", "çən", "tank", "нефть", "neft", "газ", "qaz", "масло", "спирт", "2709", "2710"]):
        for f_name in ["Table_6_Tariffs.txt", "Table_6_Tanks.txt", "Table6.txt", "Cədvəl6.txt", "Cadval_6.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    elif any(k in query_lower for k in ["реф", "ref", "термос", "termos", "автовоз", "автопоезд"]):
        for f_name in ["Table_5_Tariffs.txt", "Table_5_Reef.txt", "Table5.txt", "Cədvəl5.txt", "Cadval_5.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    elif any(k in query_lower for k in ["контейнер", "konteyner", "tank-container", "ref-container"]):
        for f_name in ["Table_9_Tariffs.txt", "Table_10_Tariffs.txt", "Table9.txt", "Table10.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
    elif any(k in query_lower for k in ["двухъярусн", "avtovoz", "ikiyaruslı", "двухярусн"]):
        for f_name in ["Table_8_Tariffs.txt", "Table_11_Tariffs.txt", "Table8.txt", "Table11.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
    else:
        for f_name in ["Table_3_Tariffs.txt", "Table_4_Tariffs.txt", "Table_12_Tariffs.txt", "Table_3_4_Universal.txt", "Table3.txt", "Table4.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)

    loaded_rules = []
    for txt_file in set(files_to_load):
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                loaded_rules.append(f"--- РАЗДЕЛ БАЗЫ: {txt_file} ---\n" + f.read())

    rules_text = "\n\n".join(loaded_rules)
    
    system_instruction = (
        f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ ГОД!\n"
        f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU = Russian, EN = English).\n"
        f"ДЛЯ АЗЕРБАЙДЖАНСКОГО ЯЗЫКА (AZ) ИСПОЛЬЗОВАТЬ ОБОЗНАЧЕНИЯ SPS (ВМЕСТО XPS) И MPS (ВМЕСТО DDP)!\n"
        f"СТРОГО ИСПОЛЬЗУЙ ТОЧНЫЕ РАССТОЯНИЯ ИЗ ФАЙЛА Distances.txt! НАПРИМЕР: YALAMA - BÖYÜK KƏSİK = СТРОГО 616 KM (KƏMƏR: 611-620 KM). ЗАПРЕЩЕНО РАССЧИТЫВАТЬ ИЛИ УГАДЫВАТЬ РАССТОЯНИЯ САМОСТОЯТЕЛЬНО!\n"
        f"ИСПОЛЬЗУЙ КУРСЫ ВАЛЮТ ИЗ СПРАВОЧНИКА КУРСОВ (Currency_Exchange.txt) ДЛЯ ПЕРЕСЧЕТА СТАВОК ИЗ CHF В USD!\n\n"
        + rules_text
    )
    return system_instruction

# 9. Схема JSON ответа
json_response_schema = {
    "type": "OBJECT",
    "properties": {
        "part1": {
            "type": "OBJECT",
            "properties": {
                "route": {"type": "STRING"},
                "shipment_type": {"type": "STRING"},
                "distance": {"type": "STRING"},
                "cargo_and_wagon": {"type": "STRING"},
                "weight_info": {"type": "STRING"},
                "period": {"type": "STRING"}
            },
            "required": ["route", "shipment_type", "distance", "cargo_and_wagon", "weight_info", "period"]
        },
        "part2": {
            "type": "OBJECT",
            "properties": {
                "exchange_rate": {"type": "STRING"},
                "base_tariff": {"type": "STRING"},
                "coefficients": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "value": {"type": "STRING"}
                        },
                        "required": ["name", "value"]
                    }
                }
            },
            "required": ["exchange_rate", "base_tariff", "coefficients"]
        },
        "part3": {
            "type": "OBJECT",
            "properties": {
                "formula": {"type": "STRING"},
                "net_ady_rate": {"type": "STRING"},
                "express_rate": {"type": "STRING", "nullable": True},
                "notes": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            },
            "required": ["formula", "net_ady_rate", "notes"]
        }
    },
    "required": ["part1", "part2", "part3"]
}

# 10. Быстрый вызов Gemini с автоматическим перебором доступных моделей
def call_gemini_json(client, prompt, instruction):
    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    last_error = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=instruction,
                    response_mime_type="application/json",
                    response_schema=json_response_schema
                )
            )
            return json.loads(response.text)
        except Exception as e:
            last_error = e
            continue
            
    raise RuntimeError(f"Не удалось выполнить запрос к ИИ: {str(last_error)}")

# 11. Поле ввода текста и кнопка расчета
user_input = st.text_area(
    t["input_header"],
    height=150,
    placeholder=t["input_placeholder"]
)

if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    else:
        # Мелкая аккуратная анимация поезда
        train_holder = st.empty()
        train_holder.markdown(
            f'''
            <div class="train-track">
                <div class="train-animation">═══ 🚃 🚃 🚃 🚂</div>
            </div>
            <center><span class="train-text"><b>{t["spinner_text"].format(selected_year)}</b></span></center>
            ''', 
            unsafe_allow_html=True
        )

        try:
            dyn_instruction = load_selective_context(user_input, selected_year, selected_lang)
            
            prompt_text = (
                f"Make exact calculation for (Freight Year: {selected_year}, Language: {selected_lang}):\n{user_input}\n\n"
                f"⚠️ UNIVERSAL WAGONS TABLES SEPARATION (CƏDVAL 3 vs CƏDVAL 4):\n"
                "- CƏDVAL 3 (Table 3): STRICTLY AND ONLY FOR IMPORT (İdxal) AND EXPORT (İxrac) SHIPMENTS IN UNIVERSAL WAGONS! Do NOT apply 1.50 multiplier to Table 3 rates!\n"
                "- CƏDVAL 4 (Table 4): STRICTLY AND ONLY FOR TRANSIT (Tranzit) SHIPMENTS IN UNIVERSAL WAGONS!\n\n"
                f"⚠️ CRITICAL UNITS OF MEASUREMENT RULE:\n"
                "- FOR LOADED TONNAGE SHIPMENTS: Output rates strictly PER 1 TON (USD/t)! DO NOT display per wagon rates.\n"
                "- FOR EMPTY WAGON RETURNS (SPS 0.10 CHF/axle-km), CAR TRANSPORTERS (Table 5 col 6), OR FIXED PER-WAGON RATES: Output rates strictly PER 1 WAGON (USD/wagon)!\n\n"
                f"⚠️ CRITICAL RULES (OUTPUT LANGUAGE MUST BE STRICTLY: {selected_lang}):\n"
                "1. ABBREVIATIONS: Treat SPS = СПС = XPS (private wagons) and MPS = МПС = DDP (railway fleet) as identical terms!\n"
                "   - For AZ language output, ALWAYS display wagon ownership as 'SPS' or 'MPS' (DO NOT use XPS or DDP in final output)!\n"
                "2. STRICT ROUTE DISTANCES:\n"
                "   - Bakı yük / Bakı tovar / Baku tovar / Absheron to Yalama = EXACTLY 204 KM! (NEVER USE 212 KM)!\n"
                "   - Yalama to Böyük Kəsik = EXACTLY 616 KM (belt 611-620 km)!\n"
                "   - ALWAYS USE EXACT DISTANCES FROM EXCEL/TXT 'Məsafə' / 'Distance' TABLES! DO NOT ESTIMATE DISTANCES!\n"
                "   - Minimum distances: Export = min 101 km (belt 101-110km), Import = min 151 km (belt 151-160km)!\n"
                "3. SPECIAL WAGONS & PASSENGER WAGONS (Clauses 3.1.2.5 - 3.1.2.8):\n"
                "   - Passenger/Mail wagons (GNG 99910000): Billable weight strictly = 66 TONS (no Table 2 multipliers). Take base rate from 25 tons BTT category (Table 7 col 6)!\n"
                "   - Transporters: min 5 tons/axle (4 axles = min 20t, 6 axles = min 30t, 8 axles = min 40t)!\n"
                "   - Empty SPS container platform return (axle distance > 19m): Apply 0.60 multiplier to axle-km rate (0.06 CHF / axle-km)!\n"
                "   - Other special wagons (3.1.2.8): Calculate using universal wagon Tables 3 & 4!\n"
                "4. GNG CODE MAPPING (GNG_Column_Mapping.txt & Clause 3.1.2.4):\n"
                "   - STRICTLY use 'GNG_Column_Mapping.txt' to determine the exact Table 6 column for tank shipments and specific cargo coefficients!\n"
                "   - Base rate for liquid cargo in tanks MUST be taken from the 25 TONS weight category column (Rule 2 / Qayda 2)!\n"
                "5. PRIVATE WAGONS (SPS / Özəl vaqonlar, Section 3.2):\n"
                "   - Loaded SPS wagons: Apply x0.85 coefficient (Except Col 8 special tanks where x0.70 applies).\n"
                "   - Empty SPS wagon return: Calculate per axle-km: 0.10 CHF / axle-km (4 axles * distance_km * 0.10 CHF) (Clause 3.2.2)! FOR EXPORT AND IMPORT SHIPMENTS, ALWAYS APPLY THE 1.50 COEFFICIENT TO THIS CALCULATION ((4 axles * distance * 0.10 CHF) * 1.50)!\n"
                "6. REFRIGERATED WAGONS & REF SECTIONS (TABLE 5):\n"
                "   - Recognize terms: 'рефвагон', 'рефсекция', 'вагонреф', 'АРВ', 'ref', '1+1', '1+2', '1+3', '1+4', '1+5', '1+6', '2+1', '3+1', '4+1', '5+1', '6+1' etc.\n"
                "   - SECTION COEFFICIENTS: [1+1] = x1.70, [1+2] / [2+1] = x1.40, [1+3] / [3+1] = x1.10, [1+4] / [4+1] = x1.00, [1+5] / [5+1] or more = x0.85 (ALWAYS APPLY x0.85 for 5+ wagon ref section)!\n"
                "7. SPECIAL COEFFICIENTS (1.04 / 1.20 / 1.50 / 0.80):\n"
                "   - IMPORT OF WOOD (GNG 4403, 4404, 4407-4413) AND BLACK METALS (GNG Ch.72, 7301-7307): MUST APPLY EXTRA COEFFICIENT × 1.04!\n"
                "   - TRANSIT ALAT - BOYUK KASIK: Apply coefficient × 1.20!\n"
                "   - TRANSIT/IMPORT OIL IN TANKS & ARV/REF TRANSIT: Apply ONLY coefficient × 1.20!\n"
                "   - COEFFICIENT 1.50: ALWAYS APPLY TO ALL EXPORT AND IMPORT SHIPMENTS (LOADED AND EMPTY WAGONS), EXCEPT Table 3 rates, wood in universal wagons (4403-4413), black metals (72, 7301-7307), methanol, and oil/petroleum in Table 6 Col 2 (import/export)!\n"
                "8. STRICT MINIMUM WEIGHT NORMS FOR LOADED WAGONS:\n"
                "   - WOOD/TIMBER (GNG 4403, 4404, 4407-4413): Billable weight = min 45 TONS! Always take base rate from 45 TONS COLUMN!\n"
                "   - CAR TRANSPORTERS (Table 5, Col 6): Billable weight = min 10 TONS!\n"
                "9. JSON OUTPUT INSTRUCTIONS:\n"
                "   - DO NOT RETURN NON-APPLICABLE COEFFICIENTS IN part2.coefficients (Only return coefficients that actually apply with values like 'x 0.85', 'x 1.50', etc.)!\n"
                "   - If ADY Express is requested, provide express_rate in part3, otherwise set express_rate to null.\n"
                "   - ALL text within JSON fields MUST BE STRICTLY IN LANGUAGE: {selected_lang}."
            )
            
            data = call_gemini_json(client, prompt_text, dyn_instruction)
            
            # Убираем индикатор после расчета
            train_holder.empty()
            
            # Выводим выбранный фрахтовый год на зеленом фоне
            st.success(t["success"].format(selected_year))
            st.markdown(f"### {t['result_title']}")

            # --- РАЗДЕЛ 1. Маршрут и условия перевозки ---
            st.markdown(f"#### 📍 {t['sec1_title']}")
            p1 = data["part1"]
            table1_md = f"""
| {t['col_param']} | {t['col_val']} |
| :--- | :--- |
| **{t['lbl_route']}** | {p1['route']} |
| **{t['lbl_type']}** | {p1['shipment_type']} |
| **{t['lbl_dist']}** | {p1['distance']} |
| **{t['lbl_cargo']}** | {p1['cargo_and_wagon']} |
| **{t['lbl_weight']}** | {p1['weight_info']} |
| **{t['lbl_period']}** | {p1['period']} |
"""
            st.markdown(table1_md)

            # --- РАЗДЕЛ 2. Коэффициенты и курс валют ---
            st.markdown(f"#### ⚙️ {t['sec2_title']}")
            p2 = data["part2"]
            table2_rows = [
                f"| **{t['lbl_exchange']}** | {p2['exchange_rate']} |",
                f"| **{t['lbl_base_rate']}** | {p2['base_tariff']} |"
            ]
            
            # Выводим только фактически примененные коэффициенты
            for coeff in p2.get("coefficients", []):
                table2_rows.append(f"| **{coeff['name']}** | {coeff['value']} |")

            table2_md = f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n" + "\n".join(table2_rows)
            st.markdown(table2_md)

            # --- РАЗДЕЛ 3. Расчет тарифа ---
            st.markdown(f"#### 📐 {t['sec3_title']}")
            p3 = data["part3"]

            # 3.1 Формула
            st.markdown(f"**{t['formula_title']}**")
            st.code(p3["formula"], language="text")

            # 3.2 Таблица итоговых ставок
            st.markdown(f"**{t['rates_title']}**")
            table3_rows = [
                f"| **{t['lbl_net_rate']}** | **{p3['net_ady_rate']}** |"
            ]
            if p3.get("express_rate"):
                table3_rows.append(f"| **{t['lbl_express_rate']}** | **{p3['express_rate']}** |")

            table3_md = f"| {t['col_rate_type']} | {t['col_amount']} |\n| :--- | :--- |\n" + "\n".join(table3_rows)
            st.markdown(table3_md)

            # 3.3 Примечания и дисклеймер
            st.markdown(f"**{t['notes_title']}**")
            notes_list = p3.get("notes", [])
            for idx, note in enumerate(notes_list, start=1):
                st.markdown(f"{idx}. *{note}*")
            
            # Дисклеймер про станционные расходы
            st.markdown(f"**Qeyd:** *{t['disclaimer']}*")

        except Exception as e:
            train_holder.empty()
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption(f"ADY Tarif Kalkulyatoru | AGT CARGO | ({selected_year}) [{selected_lang}]")

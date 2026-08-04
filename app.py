import json
import os
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

# 3. Полные переводы интерфейса и примечаний на всех 3 языках
UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt ili",
        "year_select": "Fraxt ili:",
        "lang_select": "Dil / Language:",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": (
            "Nümunə:\nMarşrut: Yalama - Abşeron\nYük: Kağız və ya karton"
            " tullantıları (GNG 4707), 35 ton\nVəziyyət: SPS örtülü vaqon"
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
        "note_sps": "Özəl vaqonlar (SPS) üçün 0.85 güzəşt əmsalı tətbiq olunmuşdur.",
        "note_import_dist": "İdxal rejimində faktiki məsafə normadan az olduğu üçün minimal 151 km tarif məsafəsi tətbiq olunmuşdur.",
        "note_export_dist": "İxrac rejimində faktiki məsafə normadan az olduğu üçün minimal 101 km tarif məsafəsi tətbiq olunmuşdur.",
        "note_express": "ADY Express xidməti üçün +2% əlavə əmsal tətbiq olunmuşdur.",
        "note_timber_metal": "İdxal rejimində meşə materialları və qara metallar üçün 1.04 əmsalı tətbiq edilmişdir.",
        "note_coef_1015": "Tətbiq olunan əlavə əmsal: 1.015.",
        "note_min_weight": "Faktiki çəki minimal tarif normasından aşağı olduğu üçün hesablama minimal norma üzrə aparılmışdır.",
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
        "input_placeholder": (
            "Пример:\nМаршрут: Ялама - Апшерон\nГруз: Отходы бумаги (ГНГ 4707),"
            " 35 тонн\nСостояние: СПС крытый вагон"
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
        "note_sps": "Применен скидочный коэффициент 0.85 для собственных вагонов (СПС).",
        "note_import_dist": "Так как фактическое расстояние меньше нормы, применен минимальный тарифный пробег 151 км (импорт).",
        "note_export_dist": "Так как фактическое расстояние меньше нормы, применен минимальный тарифный пробег 101 км (экспорт).",
        "note_express": "Применен дополнительный коэффициент +2% за сервис ADY Express.",
        "note_timber_metal": "В режиме импорта применен коэффициент 1.04 для лесных грузов и черных металлов.",
        "note_coef_1015": "Применен дополнительный коэффициент: 1.015.",
        "note_min_weight": "Так как фактический вес ниже минимальной нормы, расчет произведен по минимальной весовой норме.",
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
        "input_placeholder": (
            "Example:\nRoute: Yalama - Absheron\nCargo: Paper scrap (NHM 4707),"
            " 35 tons\nCondition: SPS covered wagon"
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
        "note_sps": "Discount coefficient 0.85 applied for private wagons (SPS).",
        "note_import_dist": "Since actual distance is below minimum norm, billable distance of 151 km applied (import).",
        "note_export_dist": "Since actual distance is below minimum norm, billable distance of 101 km applied (export).",
        "note_express": "Additional coefficient +2% applied for ADY Express service.",
        "note_timber_metal": "Coefficient 1.04 applied for import of timber and ferrous metals.",
        "note_coef_1015": "Additional coefficient applied: 1.015.",
        "note_min_weight": "Since actual weight is below minimum billable weight, calculation is based on minimum weight.",
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


# 7. Загрузка контекста
@st.cache_data(show_spinner=False)
def load_selective_context(user_query, year_label, lang):
    query_lower = user_query.lower()
    files_to_load = [
        "system_instruction.txt",
        "GNG_Column_Mapping.txt",
        "Security_Cargo_GNG.txt",
        "Currency_Exchange.txt",
    ]

    for dist_file in ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]:
        if os.path.exists(dist_file):
            files_to_load.append(dist_file)
            break

    if any(k in query_lower for k in ["tranzit", "транзит", "transit"]):
        for f_name in ["Table_4_Tariffs.txt", "Table4.txt", "Cədvəl4.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    elif any(
        k in query_lower
        for k in [
            "цистерн",
            "çən",
            "tank",
            "нефть",
            "neft",
            "газ",
            "qaz",
            "масло",
            "спирт",
            "2709",
            "2710",
        ]
    ):
        for f_name in [
            "Table_6_Tariffs.txt",
            "Table_6_Tanks.txt",
            "Table6.txt",
            "Cədvəl6.txt",
        ]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    elif any(
        k in query_lower
        for k in ["реф", "ref", "термос", "termos", "автовоз", "автопоезд"]
    ):
        for f_name in [
            "Table_5_Tariffs.txt",
            "Table_5_Reef.txt",
            "Table5.txt",
            "Cədvəl5.txt",
        ]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    elif any(
        k in query_lower
        for k in ["контейнер", "konteyner", "tank-container", "ref-container"]
    ):
        for f_name in [
            "Table_9_Tariffs.txt",
            "Table_10_Tariffs.txt",
            "Table9.txt",
            "Table10.txt",
        ]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
    else:
        for f_name in ["Table_3_Tariffs.txt", "Table3.txt", "Cədvəl3.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break

    loaded_rules = []
    for txt_file in set(files_to_load):
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                loaded_rules.append(f"--- BAZA SƏNƏDİ: {txt_file} ---\n" + f.read())

    rules_text = "\n\n".join(loaded_rules)

    system_instruction = (
        f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ ГОД!\n"
        f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU = Russian, EN = English).\n"
        f"ОБЯЗАННОСТЬ: Извлечь параметры и возвратить их в JSON. Все текстовые примечания строятся через логические флаги (is_min_weight_applied, is_min_distance_applied)!\n\n"
        + rules_text
    )
    return system_instruction


# 8. Вызов Gemini
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


# 9. ЧЕСТНЫЙ МАТЕМАТИЧЕСКИЙ ДВИЖОК В PYTHON
def compute_python_tariff(base_chf, exchange_rate, is_sps, is_import_timber_metal, is_loaded_1015):
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
    express_rate_str = f"{(current_val * 1.

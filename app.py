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

# 3. Переводы интерфейса
UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": (
            "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt ili"
        ),
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
        "note_sps": (
            "Özəl vaqonlar (SPS) üçün 0.85 güzəşt əmsalı tətbiq olunmuşdur."
        ),
        "note_import": (
            "İdxal rejimində minimal tarif məsafəsi norması 151 km-dir."
        ),
        "note_export": (
            "İxrac rejimində minimal tarif məsafəsi norması 101 km-dir."
        ),
        "note_express": (
            "ADY Express xidməti üçün +2% əlavə əmsal tətbiq olunmuşdur."
        ),
        "note_timber_metal": (
            "İdxal rejimində meşə materialları və qara metallar üçün 1.04"
            " əmsalı tətbiq edilmişdir."
        ),
        "note_coef_1015": "Tətbiq olunan əlavə əmsal: 1.015.",
    },
    "RU": {
        "title": "Тарифный калькулятор ADY",
        "subtitle": (
            "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год"
        ),
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
        "note_sps": (
            "Применен скидочный коэффициент 0.85 для собственных вагонов (СПС)."
        ),
        "note_import": (
            "В режиме импорта минимальное тарифное расстояние составляет 151"
            " км."
        ),
        "note_export": (
            "В режиме экспорта минимальное тарифное расстояние составляет 101"
            " км."
        ),
        "note_express": (
            "Применен дополнительный коэффициент +2% за сервис ADY Express."
        ),
        "note_timber_metal": (
            "В режиме импорта применен коэффициент 1.04 для лесных грузов и"
            " черных металлов."
        ),
        "note_coef_1015": "Применен дополнительный коэффициент: 1.015.",
    },
    "EN": {
        "title": "ADY Tariff Calculator",
        "subtitle": (
            "Railway freight tariff calculator for Azerbaijan — {} freight year"
        ),
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
        "note_sps": (
            "Discount coefficient 0.85 applied for private wagons (SPS)."
        ),
        "note_import": "Minimum tariff distance for import is 151 km.",
        "note_export": "Minimum tariff distance for export is 101 km.",
        "note_express": (
            "Additional coefficient +2% applied for ADY Express service."
        ),
        "note_timber_metal": (
            "Coefficient 1.04 applied for import of timber and ferrous metals."
        ),
        "note_coef_1015": "Additional coefficient applied: 1.015.",
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


# 7. Загрузка динамического контекста
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

    if any(
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
        for f_name in [
            "Table_3_Tariffs.txt",
            "Table_4_Tariffs.txt",
            "Table_12_Tariffs.txt",
            "Table3.txt",
            "Table4.txt",
        ]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)

    loaded_rules = []
    for txt_file in set(files_to_load):
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                loaded_rules.append(f"--- BAZA SƏNƏDİ: {txt_file} ---\n" + f.read())

    rules_text = "\n\n".join(loaded_rules)

    system_instruction = (
        f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ ГОД!\n"
        f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU = Russian, EN = English).\n"
        f"СТРОГИЕ ПРАВИЛА:\n"
        f"1. Для RU языка строго использовать 'СПС' (вместо SPS) и 'МПС' (вместо MPS).\n"
        f"2. МИН. РАСЧЕТНАЯ НОРМА ЧЕКИ: Если фактический вес < минимальной нормы (например, GNG 4707 = 45 т, GNG 4407 = 45 т), РАСЧЕТНЫЙ ВЕС СТРОГО ПРИНИМАЕТСЯ РАВНЫМ МИН. НОРМЕ (45 т) и колонка выбирается по 45 т!\n"
        f"3. МПС vs СПС: Для МПС берется 100% базовая ставка из таблицы. Для СПС применяется коэффициент k = 0.85 к базовой ставке таблицы.\n"
        f"4. СТАНЦИИ: Если станция пограничная (Yalama, Boyuk Kesik, Astara, Culfa, Alat), писать с припиской '-eksp.' (например, 'Yalama-eksp. - Abşeron').\n\n"
        + rules_text
    )
    return system_instruction


# 8. Вызов Gemini — СТРОГО gemini-3.6-flash И temperature=0.0
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


# 9. Интерфейс расчета
user_input = st.text_area(
    t["input_header"], height=150, placeholder=t["input_placeholder"]
)


def get_static_rules():
    rules_file = "prompt_rules.txt"
    rules_content = ""
    if os.path.exists(rules_file):
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_content = f.read()

    schema_dict = {
        "part1": {
            "route": "string",
            "shipment_type": "string",
            "distance": "string",
            "cargo_and_wagon": "string",
            "weight_info": "string",
            "period": "string",
        },
        "part2": {
            "exchange_rate": "string",
            "base_tariff": "string",
            "coefficients": [{"name": "string", "value": "string"}],
        },
        "part3": {
            "formula": "string",
            "net_ady_rate": "string",
            "express_rate": "string or null",
            "notes": [],
        },
    }

    return (
        rules_content
        + "\n\nOUTPUT FORMAT (MANDATORY JSON):\nReturn ONLY a valid JSON object"
        " matching exactly this structure:\n"
        + json.dumps(schema_dict, indent=2)
    )


if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    else:
        train_holder = st.empty()
        train_holder.markdown(
            f"""
            <div class="train-track">
                <div class="train-animation">═══ 🚃 🚃 🚃 🚂</div>
            </div>
            <center><span class="train-text"><b>{t["spinner_text"].format(selected_year)}</b></span></center>
            """,
            unsafe_allow_html=True,
        )

        try:
            dyn_instruction = load_selective_context(
                user_input, selected_year, selected_lang
            )

            prompt_header = (
                f"Make exact calculation for (Freight Year: {selected_year},"
                f" Language: {selected_lang}):\n{user_input}\n\nCRITICAL RULES (OUTPUT"
                f" LANGUAGE MUST BE STRICTLY: {selected_lang}):\n"
            )
            prompt_text = prompt_header + get_static_rules()

            data = call_gemini_json(client, prompt_text, dyn_instruction)

            train_holder.empty()

            st.success(t["success"].format(selected_year))
            st.markdown(f"### {t['result_title']}")

            # Раздел 1
            st.markdown(f"#### 📍 {t['sec1_title']}")
            p1 = data.get("part1", {})
            if isinstance(p1, list) and len(p1) > 0:
                p1 = p1[0]

            if isinstance(p1, dict):
                st.markdown(
                    f"| {t['col_param']} | {t['col_val']} |\n"
                    f"| :--- | :--- |\n"
                    f"| **{t['lbl_route']}** | {p1.get('route', '-')} |\n"
                    f"| **{t['lbl_type']}** | {p1.get('shipment_type', '-')} |\n"
                    f"| **{t['lbl_dist']}** | {p1.get('distance', '-')} |\n"
                    f"| **{t['lbl_cargo']}** | {p1.get('cargo_and_wagon', '-')} |\n"
                    f"| **{t['lbl_weight']}** | {p1.get('weight_info', '-')} |\n"
                    f"| **{t['lbl_period']}** | {p1.get('period', '-')} |\n"
                )

            # Раздел 2
            st.markdown(f"#### ⚙️ {t['sec2_title']}")
            p2 = data.get("part2", {})
            if isinstance(p2, list) and len(p2) > 0:
                p2 = p2[0]

            if isinstance(p2, dict):
                table2_rows = [
                    f"| **{t['lbl_exchange']}** | {p2.get('exchange_rate', '-')} |",
                    f"| **{t['lbl_base_rate']}** | {p2.get('base_tariff', '-')} |",
                ]

                coeffs = p2.get("coefficients", [])
                if isinstance(coeffs, list):
                    for coeff in coeffs:
                        if isinstance(coeff, dict):
                            table2_rows.append(
                                f"| **{coeff.get('name', '')}** |"
                                f" {coeff.get('value', '')} |"
                            )

                st.markdown(
                    f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n"
                    + "\n".join(table2_rows)
                )

            # Раздел 3
            st.markdown(f"#### 📐 {t['sec3_title']}")
            p3 = data.get("part3", {})
            if isinstance(p3, list) and len(p3) > 0:
                p3 = p3[0]

            if isinstance(p3, dict):
                st.markdown(f"**{t['formula_title']}**")
                st.code(p3.get("formula", "-"), language="text")

                st.markdown(f"**{t['rates_title']}**")
                table3_rows = [
                    f"| **{t['lbl_net_rate']}** | **{p3.get('net_ady_rate', '-')}** |"
                ]
                if p3.get("express_rate"):
                    table3_rows.append(
                        f"| **{t['lbl_express_rate']}** |"
                        f" **{p3.get('express_rate')}** |"
                    )

                st.markdown(
                    f"| {t['col_rate_type']} | {t['col_amount']} |\n| :--- | :--- |\n"
                    + "\n".join(table3_rows)
                )

                # Динамическая сборка примечаний силами Python
                auto_notes = []
                input_check = user_input.lower()
                
                if any(k in input_check for k in ["sps", "özəl", "спс", "собствен"]):
                    auto_notes.append(t["note_sps"])
                
                ship_type = str(p1.get("shipment_type", "")).lower()
                if any(k in ship_type for k in ["idxal", "импорт", "import"]):
                    auto_notes.append(t["note_import"])
                elif any(k in ship_type for k in ["ixrac", "экспорт", "export"]):
                    auto_notes.append(t["note_export"])

                # Проверка коэффициентов из ответа Gemini
                coeffs = p2.get("coefficients", []) if isinstance(p2, dict) else []
                coeff_values = [str(c.get("value", "")) for c in coeffs if isinstance(c, dict)]
                coeff_str = " ".join(coeff_values)

                if "1.04" in coeff_str:
                    auto_notes.append(t["note_timber_metal"])
                if "1.015" in coeff_str:
                    auto_notes.append(t["note_coef_1015"])

                if p3.get("express_rate"):
                    auto_notes.append(t["note_express"])

                if auto_notes:
                    st.markdown(f"**{t['notes_title']}**")
                    for idx, note in enumerate(auto_notes, start=1):
                        st.markdown(f"{idx}. *{note}*")

                st.markdown(f"**Qeyd:** *{t['disclaimer']}*")

        except Exception as e:
            train_holder.empty()
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption(
    f"ADY Tarif Kalkulyatoru | AGT CARGO | ({selected_year}) [{selected_lang}]"
)

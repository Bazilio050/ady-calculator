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

# 2. Скрытие системных элементов Streamlit + Оптимальная ширина элементов
st.markdown(
    """
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

    /* Мелкая анимация паровозика */
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
""",
    unsafe_allow_html=True,
)

# 3. Переводы интерфейса (AZ, RU, EN)
UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": (
            "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — {} fraxt"
            " ili"
        ),
        "year_select": "Fraxt ili:",
        "lang_select": "Dil / Language:",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": (
            "Nümunə:\nMarşrut: Yalama - Abşeron\nYük: Meşə materialları (GNG"
            " 4407), 35 ton\nVəziyyət: SPS örtülü vaqon"
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
            "Qeyd olunan tariflərə станция xərcləri (yükləmə-boşaltma, tərtibat,"
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
    },
    "RU": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": (
            "Расчет ж/д тарифов по Азербайджану на {} фрахтовый год"
        ),
        "year_select": "Фрахтовый год:",
        "lang_select": "Язык / Language:",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": (
            "Пример:\nМаршрут: Ялама - Апшерон\nГруз: Пиломатериалы (ГНГ 4407),"
            " 35 тонн\nСостояние: СПС крытый вагон"
        ),
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
        "lbl_net_rate": "Yekün ADY tarifi",
        "lbl_express_rate": "Yekun tarif (ADY Express +2% daxil)",
        "api_warning": "⚠️ Пожалуйста, добавьте GEMINI_API_KEY.",
        "api_label": "Введите Gemini API Key:",
    },
    "EN": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": (
            "Railway freight tariff calculator for Azerbaijan — {} freight year"
        ),
        "year_select": "Freight Year:",
        "lang_select": "Language:",
        "input_header": "Enter shipment details:",
        "input_placeholder": (
            "Example:\nRoute: Yalama - Absheron\nCargo: Timber (NHM 4407), 35"
            " tons\nCondition: SPS covered wagon"
        ),
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
        "lbl_net_rate": "Yekün ADY tarifi",
        "lbl_express_rate": "Yekun tarif (ADY Express +2% daxil)",
        "api_warning": "⚠️ Please provide GEMINI_API_KEY.",
        "api_label": "Enter Gemini API Key:",
    },
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

# 6. Заголовок и подзаголовок слева под селекторами
st.markdown(
    f'<div class="custom-title">{t["title"]}</div>', unsafe_allow_html=True
)
st.markdown(
    f'<div class="custom-subtitle">{t["subtitle"].format(selected_year)}</div>',
    unsafe_allow_html=True,
)

# 7. Проверка API ключа
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input(t["api_label"], type="password")

if not api_key:
    st.warning(t["api_warning"])
    st.stop()

client = genai.Client(api_key=api_key)


# 8. Динамическая подгрузка текстовой базы
@st.cache_data(show_spinner=False)
def load_selective_context(user_query, year_label, lang):
    query_lower = user_query.lower()
    files_to_load = [
        "system_instruction.txt",
        "Weight_Categories.txt",
        "GNG_Column_Mapping.txt",
        "Security_Cargo_GNG.txt",
    ]

    for dist_file in ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]:
        if os.path.exists(dist_file):
            files_to_load.append(dist_file)
            break

    for curr_file in ["Currency_Exchange.txt", "Exchange_Rates.txt", "Valyuta.txt"]:
        if os.path.exists(curr_file):
            files_to_load.append(curr_file)
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
            "Cadval_6.txt",
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
            "Cadval_5.txt",
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
    elif any(
        k in query_lower for k in ["двухъярусн", "avtovoz", "ikiyaruslı", "двухярусн"]
    ):
        for f_name in [
            "Table_8_Tariffs.txt",
            "Table_11_Tariffs.txt",
            "Table8.txt",
            "Table11.txt",
        ]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
    else:
        for f_name in [
            "Table_3_Tariffs.txt",
            "Table_4_Tariffs.txt",
            "Table_12_Tariffs.txt",
            "Table_3_4_Universal.txt",
            "Table3.txt",
            "Table4.txt",
        ]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)

    loaded_rules = []
    for txt_file in set(files_to_load):
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                loaded_rules.append(f"--- РАЗДЕЛ БАЗЫ: {txt_file} ---\n" + f.read())

    rules_text = "\n\n".join(loaded_rules)

    system_instruction = (
        f"ВНИМАНИЕ: Применяется Тарифная политика ADY на {year_label} ФРАХТОВЫЙ"
        " ГОД!\n"
        f"ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО НА ЯЗЫКЕ: {lang} (AZ = Azerbaijani, RU ="
        " Russian, EN = English).\nДЛЯ АЗЕРБАЙДЖАНСКОГО ЯЗЫКА (AZ) ИСПОЛЬЗОВАТЬ"
        " ОБОЗНАЧЕНИЯ SPS (ВМЕСТО XPS) И MPS (ВМЕСТО DDP)!\nСТРОГО ИСПОЛЬЗУЙ"
        " ТОЧНЫЕ РАССТОЯНИЯ ИЗ ФАЙЛА Distances.txt! НАПРИМЕР: YALAMA - BÖYÜK KƏSİK"
        " = СТРОГО 616 KM (KƏMƏР: 611-620 KM). ЗАПРЕЩЕНО РАССЧИТЫВАТЬ ИЛИ"
        " УГАДЫВАТЬ РАССТОЯНИЯ САМОСТОЯТЕЛЬНО!\nИСПОЛЬЗУЙ КУРСЫ ВАЛЮТ ИЗ"
        " СПРАВОЧНИКА КУРСОВ (Currency_Exchange.txt) ДЛЯ ПЕРЕСЧЕТА СТАВОК ИЗ CHF В"
        " USD!\n\n" + rules_text
    )
    return system_instruction


# 9. Вызов Gemini с моделью gemini-3.6-flash
def call_gemini_json(client, prompt, instruction):
    model_name = "gemini-3.6-flash"

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0.1,
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


# 10. Поле ввода текста и кнопка расчета
user_input = st.text_area(
    t["input_header"], height=150, placeholder=t["input_placeholder"]
)


# Функция для считывания внешних правил
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
            "notes": ["string"],
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

            # --- РАЗДЕЛ 1. Маршрут и условия перевозки ---
            st.markdown(f"#### 📍 {t['sec1_title']}")
            p1 = data.get("part1", {})
            if isinstance(p1, list) and len(p1) > 0:
                p1 = p1[0]

            if isinstance(p1, dict):
                table1_md = f"""
| {t['col_param']} | {t['col_val']} |
| :--- | :--- |
| **{t['lbl_route']}** | {p1.get('route', '-')} |
| **{t['lbl_type']}** | {p1.get('shipment_type', '-')} |
| **{t['lbl_dist']}** | {p1.get('distance', '-')} |
| **{t['lbl_cargo']}** | {p1.get('cargo_and_wagon', '-')} |
| **{t['lbl_weight']}** | {p1.get('weight_info', '-')} |
| **{t['lbl_period']}** | {p1.get('period', '-')} |
"""
                st.markdown(table1_md)

            # --- РАЗДЕЛ 2. Коэффициенты и курс валют ---
            st.markdown(f"#### ⚙️ {t['sec2_title']}")
            p2 = data.get("part2", {})

            if isinstance(p2, list) and len(p2) > 0:
                p2 = p2[0]

            if isinstance(p2, dict):
                exch_rate = p2.get("exchange_rate", "-")
                base_rate = p2.get("base_tariff", "-")

                table2_rows = [
                    f"| **{t['lbl_exchange']}** | {exch_rate} |",
                    f"| **{t['lbl_base_rate']}** | {base_rate} |",
                ]

                coeffs = p2.get("coefficients", [])
                if isinstance(coeffs, list):
                    for coeff in coeffs:
                        if isinstance(coeff, dict):
                            c_name = coeff.get("name", "")
                            c_val = coeff.get("value", "")
                            table2_rows.append(f"| **{c_name}** | {c_val} |")

                table2_md = (
                    f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n"
                    + "\n".join(table2_rows)
                )
                st.markdown(table2_md)

            # --- РАЗДЕЛ 3. Расчет тарифа ---
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

                table3_md = (
                    f"| {t['col_rate_type']} | {t['col_amount']} |\n| :--- | :--- |\n"
                    + "\n".join(table3_rows)
                )
                st.markdown(table3_md)

                st.markdown(f"**{t['notes_title']}**")
                notes_list = p3.get("notes", [])
                if isinstance(notes_list, list):
                    for idx, note in enumerate(notes_list, start=1):
                        st.markdown(f"{idx}. *{note}*")

                st.markdown(f"**Qeyd:** *{t['disclaimer']}*")

        except Exception as e:
            train_holder.empty()
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption(
    f"ADY Tarif Kalkulyatoru | AGT CARGO | ({selected_year}) [{selected_lang}]"
)

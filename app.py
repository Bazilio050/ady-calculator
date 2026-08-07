import json
import os
import re
import streamlit as st

# =========================================================
# 1. Page Config & CSS
# =========================================================
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
    
    .header-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 5px;
        margin-bottom: 2px;
    }
    .custom-title {
        font-size: 26px !important;
        font-weight: 700;
        margin: 0;
    }
    .stTextArea textarea {
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 2. Справочники и Переводы (UI_TEXT)
# =========================================================
BORDER_STATIONS = {
    "YALAMA": "Yalama (eksport)",
    "BEYUK KESIK": "Böyük Kəsik (eksport)",
    "BEYUK-KESIK": "Böyük Kəsik (eksport)",
    "BOYUK KESIK": "Böyük Kəsik (eksport)",
    "ASTARA": "Astara (eks.aşır)",
    "CULFA": "Culfa (eksport)",
    "ALAT": "Ələt eksport",
    "SAMUR": "Samur (eksport)"
}

UI_TEXT = {
    "AZ": {
        "title": "ADY Tarif Kalkulyatoru",
        "subtitle": "Azərbaycan üzrə dəmir yolu tariflərinin hesablanması — 2026-cı fraxt ili",
        "input_header": "Daşıma parametrlərini daxil edin:",
        "input_placeholder": "Nümunə:\nMarşrut: Yalama - Beyuk kasik\nYük: Qara metallar (GNG 72), 35 ton\nVəziyyət: SPS örtülü vaqon",
        "calc_btn": "🚀 Tarifi hesabla",
        "warning_empty": "Xahiş olunur, hesablaşma şərtlərini daxil edin.",
        "sec1_title": "1. Marşrut və daşıma şərtləri",
        "col_param": "Parametr",
        "col_val": "Qiymət / Həcm",
        "lbl_route": "Marşrut",
        "lbl_mode": "Daşıma növü",
        "lbl_dist": "Məsafə",
        "lbl_cargo": "Yük / Vəziyyət",
        "lbl_weight": "Faktiki / Hesablaşma çəkisi",
        "lbl_period": "Dövr",
        "mode_transit": "Tranzit daşınması",
        "mode_import": "İdxal daşınması",
        "mode_export": "İxrac daşınması",
        "period_val": "2026-cı fraxt ili"
    },
    "RU": {
        "title": "Тарифный калькулятор ADY",
        "subtitle": "Расчет ж/д тарифов по Азербайджану на 2026 фрахтовый год",
        "input_header": "Введите данные по перевозке:",
        "input_placeholder": "Пример:\nМаршрут: Ялама - Беюк Касик\nГруз: Черные металлы (ГНГ 72), 35 тонн\nСостояние: СПС крытый вагон",
        "calc_btn": "🚀 Рассчитать тариф",
        "warning_empty": "Пожалуйста, введите условия расчета.",
        "sec1_title": "1. Маршрут и условия перевозки",
        "col_param": "Параметр",
        "col_val": "Значение / Объем",
        "lbl_route": "Маршрут",
        "lbl_mode": "Вид перевозки",
        "lbl_dist": "Расстояние",
        "lbl_cargo": "Груз / Состояние",
        "lbl_weight": "Фактический / Расчетный вес",
        "lbl_period": "Период",
        "mode_transit": "Транзитная перевозка",
        "mode_import": "Импортная перевозка",
        "mode_export": "Экспортная перевозка",
        "period_val": "2026 фрахтовый год"
    }
}

# =========================================================
# 3. Вспомогательные функции
# =========================================================
@st.cache_data
def load_config():
    if os.path.exists("rules_config.json"):
        with open("rules_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def is_border_station(station_name: str) -> bool:
    name_clean = station_name.upper().replace("-EKSP.", "").replace("EKSP.", "").strip()
    return any(border in name_clean for border in BORDER_STATIONS.keys())

def format_station_names(st_from: str, st_to: str) -> tuple:
    """Если обе станции пограничные — у обеих гарантируется -eksp."""
    c_from = st_from.strip()
    c_to = st_to.strip()
    
    both_border = is_border_station(c_from) and is_border_station(c_to)
    
    if both_border:
        if not c_from.lower().endswith("-eksp."):
            c_from = f"{c_from}-eksp."
        if not c_to.lower().endswith("-eksp."):
            c_to = f"{c_to}-eksp."
            
    return c_from, c_to, both_border

def calculate_billable_weight(fact_weight: float, gng_code: str, rules_config: dict) -> float:
    gng_str = str(gng_code).strip()
    
    # Минималка для ГНГ 72 (Черные металлы) = 60 тонн
    if gng_str.startswith("72") or gng_str == "72":
        return max(fact_weight, 60.0)
        
    min_norms = rules_config.get("minimal_weight_norms_gng", {}).get("rules", [])
    for rule in min_norms:
        prefixes = rule.get("gng_prefixes", [])
        if any(gng_str.startswith(p) for p in prefixes):
            return max(fact_weight, float(rule.get("norm_tons", 10)))
            
    return max(fact_weight, 10.0)

def parse_input_text(text: str):
    st_from, st_to = "Yalama", "Böyük Kəsik"
    gng_code = "72"
    fact_weight = 35.0
    wagon_type = "universal"
    
    weight_match = re.search(r'(\d+[\.,]?\d*)\s*(т|тонн|ton|t)', text, re.IGNORECASE)
    if weight_match:
        fact_weight = float(weight_match.group(1).replace(',', '.'))
        
    gng_match = re.search(r'(гнг|gng|yhn)\s*(\d+)', text, re.IGNORECASE)
    if gng_match:
        gng_code = gng_match.group(2)
        
    route_match = re.search(r'([А-Яа-яA-Za-z\s-]+)\s*[-—–]\s*([А-Яа-яA-Za-z\s-]+)', text)
    if route_match:
        st_from = route_match.group(1).strip()
        st_to = route_match.group(2).strip()

    return st_from, st_to, gng_code, fact_weight, wagon_type

# =========================================================
# 4. Основной блок Streamlit UI
# =========================================================
def main():
    config = load_config()

    # --- Переключатель языка на верхней панели ---
    col_lang1, col_lang2 = st.columns([5, 1])
    with col_lang2:
        lang = st.selectbox("Dil / Language:", ["AZ", "RU"], index=0)
    
    txt = UI_TEXT[lang]

    # --- Шапка с логотипом ---
    st.markdown(
        f"""
        <div class="header-container">
            <span style="font-size: 32px;">🚂</span>
            <span class="custom-title">{txt['title']}</span>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.caption(txt["subtitle"])
    st.divider()

    # --- Поле ввода запроса ---
    st.subheader(txt["input_header"])
    user_query = st.text_area(
        label="Query Input",
        label_visibility="collapsed",
        placeholder=txt["input_placeholder"],
        height=120
    )

    calc_clicked = st.button(txt["calc_btn"], type="primary", use_container_width=True)

    if calc_clicked or user_query:
        if not user_query.strip():
            st.warning(txt["warning_empty"])
            return

        st_from_raw, st_to_raw, gng_code, fact_weight, wagon_type = parse_input_text(user_query)

        # 1. Авто-определение типа перевозки
        disp_from, disp_to, is_both_border = format_station_names(st_from_raw, st_to_raw)
        
        if is_both_border or "транзит" in user_query.lower() or "tranzit" in user_query.lower():
            mode_str = txt["mode_transit"]
        elif is_border_station(st_from_raw):
            mode_str = txt["mode_import"]
        else:
            mode_str = txt["mode_export"]

        # 2. Вес и ГНГ
        billable_weight = calculate_billable_weight(fact_weight, gng_code, config)
        
        gng_display = f"GNG {gng_code}"
        if gng_code.startswith("72"):
            gng_display = f"GNG {gng_code} (Qara metallar)" if lang == "AZ" else f"ГНГ {gng_code} (Черные металлы)"

        # 3. Расстояние
        distance_km = 512.0  

        st.divider()
        st.subheader(txt["sec1_title"])

        # Вывод полной таблицы со строкой Dövr
        st.table([
            {txt["col_param"]: txt["lbl_route"], txt["col_val"]: f"{disp_from} - {disp_to}"},
            {txt["col_param"]: txt["lbl_mode"], txt["col_val"]: mode_str},
            {txt["col_param"]: txt["lbl_dist"], txt["col_val"]: f"{distance_km:.0f} km"},
            {txt["col_param"]: txt["lbl_cargo"], txt["col_val"]: f"{gng_display}, Universal vaqon (SPS)"},
            {txt["col_param"]: txt["lbl_weight"], txt["col_val"]: f"{fact_weight} t / {billable_weight} t"},
            {txt["col_param"]: txt["lbl_period"], txt["col_val"]: txt["period_val"]}
        ])

if __name__ == "__main__":
    main()

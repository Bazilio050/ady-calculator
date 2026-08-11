import streamlit as st
import json
from engine import process_full_calculation

# Импорт функции NLU-парсерa Gemini
# Убедитесь, что имя файла совпадает с вашим NLU-модулем (например, nlu_parser.py)
try:
    from nlu_parser import parse_user_input_with_gemini
except ImportError:
    # Заглушка, если модуль называется иначе
    def parse_user_input_with_gemini(user_input: str) -> dict:
        return {}

# ==============================================================================
# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="ADY Express - Dəmiryol Tarif Kalkulyatoru",
    page_icon="🚂",
    layout="wide"
)

# ==============================================================================
# 2. СЛОВАРЬ ЛОКАЛИЗАЦИИ ИНТЕРФЕЙСА (UI_TRANSLATIONS)
# ==============================================================================
UI_TRANSLATIONS = {
    "AZ": {
        "title": "🚂 ADY Express - Dəmiryol Tarif Kalkulyatoru",
        "input_label": "Daşıma sorğusunu daxil edin (marşrut, yük, çəki, vaqon tipi):",
        "input_placeholder": "Məsələn: Yalama – Böyük Kəsik, GNG 4407 taxta-şalban, 35 ton, universal vaqon...",
        "calc_button": "Tarifi Hesabla",
        "type_import": "İdxal daşınması",
        "type_export": "İxrac daşınması",
        "type_transit": "Tranzit daşınması",
        "type_local": "Daxili daşınma",
        "unit_ton": "USD/t",
        "unit_wagon": "USD/vaqon",
        "note_sps": "SPS vaqonları üçün 0.85 güzəşt əmsalı tətbiq olunmuşdur.",
        "note_coef_1015": "Yüklü vaqonlar üçün 1.015 indeksasiya əmsalı tətbiq olunmuşdur.",
        "note_import": "İdxal daşımaları üçün minimum tarif məsafəsi 151 km qəbul edilir.",
        "note_export": "İxrac daşımaları üçün minimum tarif məsafəsi 101 km qəbul edilir.",
        "note_min_weight": "Yükün faktiki çəkisi vaqonun minimal yükləmə normasından az olduğu üçün hesablaşma minimal norma ilə aparılmışdır.",
        "note_express": "ADY Express tərəfindən 2% ekspeditor əlavəsi (surcharge) tətbiq edilir."
    },
    "RU": {
        "title": "🚂 ADY Express - Железнодорожный тарифный калькулятор",
        "input_label": "Введите запрос на перевозку (маршрут, груз, вес, тип вагона):",
        "input_placeholder": "Например: Ялама – Беюк Кесик, ГНГ 4407 пиломатериалы, 35 тонн, универсальный вагон...",
        "calc_button": "Рассчитать тариф",
        "type_import": "Импортная перевозка",
        "type_export": "Экспортная перевозка",
        "type_transit": "Транзитная перевозка",
        "type_local": "Внутренняя перевозка",
        "unit_ton": "USD/т",
        "unit_wagon": "USD/вагон",
        "note_sps": "Применена скидка СПС 0.85 для собственных/арендованных вагонов.",
        "note_coef_1015": "Применён индексационный коэффициент 1.015 для гружёных вагонов.",
        "note_import": "Для импортных перевозок минимальное тарифное плечо составляет 151 км.",
        "note_export": "Для экспортных перевозок минимальное тарифное плечо составляет 101 км.",
        "note_min_weight": "Расчёт произведён по минимальной норме загрузки вагона, так как фактический вес ниже нормы.",
        "note_express": "Применена экспедиторская надбавка ADY Express в размере 2%."
    },
    "EN": {
        "title": "🚂 ADY Express - Railway Tariff Calculator",
        "input_label": "Enter shipment query (route, cargo, weight, wagon type):",
        "input_placeholder": "e.g., Yalama – Boyuk Kesik, NHM 4407 timber, 35 tons, universal wagon...",
        "calc_button": "Calculate Tariff",
        "type_import": "Import shipment",
        "type_export": "Export shipment",
        "type_transit": "Transit shipment",
        "type_local": "Domestic shipment",
        "unit_ton": "USD/t",
        "unit_wagon": "USD/wagon",
        "note_sps": "SPS discount coefficient 0.85 applied.",
        "note_coef_1015": "Loaded wagon indexation coefficient 1.015 applied.",
        "note_import": "Minimum tariff distance for import shipments is 151 km.",
        "note_export": "Minimum tariff distance for export shipments is 101 km.",
        "note_min_weight": "Calculation made by minimum load capacity, as actual weight is below the threshold.",
        "note_express": "ADY Express 2% forwarding fee surcharge applied."
    }
}

# ==============================================================================
# 3. БОКОВАЯ ПАНЕЛЬ НАСТРОЕК (SIDEBAR)
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Параметры / Settings")
    lang = st.selectbox("Mühit dili / Язык / Language", options=["AZ", "RU", "EN"], index=0)
    year = st.selectbox("İl / Фрахтовый год / Freight year", options=["2026", "2025", "2024"], index=0)
    st.markdown("---")
    st.info("💡 **ADY Express Tariff Engine v3.0**\n\nРасчет железнодорожных тарифных ставок в соответствии со спецификациями Tarif Razılaşması.")

ui_t = UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS["AZ"])

st.title(ui_t["title"])

# ==============================================================================
# 4. ФОРМА ВВОДА ЗАПРОСА
# ==============================================================================
user_input_raw = st.text_area(
    ui_t["input_label"],
    placeholder=ui_t["input_placeholder"],
    height=120
)

# ==============================================================================
# 5. ОБРАБОТКА И РАСЧЕТ С ТЕКУЩИМ NLU (МГНОВЕННО С 1-ГО КЛИКА)
# ==============================================================================
if st.button(ui_t["calc_button"], type="primary", use_container_width=True) and user_input_raw.strip():
    
    with st.spinner("Анализ данных и расчет стоимости..." if lang == "RU" else "Məlumatlar təhlil edilir..."):
        
        # Шаг A: Распознаем свежие данные прямо из текстового запроса
        fresh_nlu_data = parse_user_input_with_gemini(user_input_raw)
        
        # Шаг B: Сохраняем в session_state для системной истории
        st.session_state["nlu_data"] = fresh_nlu_data
        
        # Шаг C: Передаем СВЕЖИЙ fresh_nlu_data напрямую в engine.py
        calc_result = process_full_calculation(
            nlu_data=fresh_nlu_data,  # <-- Главный секрет работы с 1-го раза!
            user_input_raw=user_input_raw,
            lang=lang,
            year=year,
            ui_t=ui_t
        )

    st.markdown("---")
    st.subheader("📋 Итоговый отчёт / Yekun Hesabat" if lang == "RU" else "📋 Yekun Hesabat")

    # --- 1. Маршрут и условия ---
    part1 = calc_result.get("part1", {})
    st.markdown("### 1. Marşrut və daşıma şərtləri" if lang == "AZ" else ("### 1. Маршрут и условия перевозки" if lang == "RU" else "### 1. Route & Conditions"))
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Маршрут / Marşrut", part1.get("route", "-"))
        st.metric("Груз и вагон / Yük və vaqon", part1.get("cargo_and_wagon", "-"))
    with c2:
        st.metric("Вид перевозки / Daşıma növü", part1.get("shipment_type", "-"))
        st.metric("Расчетный вес / Çəki", part1.get("weight_info", "-"))
    with c3:
        st.metric("Расстояние / Məsafə", part1.get("distance", "-"))
        st.metric("Период / Dövr", part1.get("period", "-"))

    st.markdown("---")

    # --- 2. Базовый тариф и коэффициенты ---
    part2 = calc_result.get("part2", {})
    st.markdown("### 2. Базовая ставка и коэффициенты" if lang == "RU" else "### 2. Baza tarifi və əmsallar")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Курс валюты / Valyuta məzənnəsi:** {part2.get('exchange_rate', '-')}")
        st.write(f"**Базовый тариф / Baza tarifi:** {part2.get('base_tariff', '-')}")
    with c2:
        st.write("**Коэффициенты / Əmsallar:**")
        coeffs = part2.get("coefficients", [])
        if coeffs:
            for c in coeffs:
                st.write(f"• {c.get('name')}: `{c.get('value')}`")
        else:
            st.write("• *Нет дополнительных коэффициентов*")

    st.markdown("---")

    # --- 3. Итоговые расчётные ставки ---
    part3 = calc_result.get("part3", {})
    st.markdown("### 3. Итоговая калькуляция ставки" if lang == "RU" else "### 3. Yekun qiymətləndirmə")

    st.code(f"Формула расчета: {part3.get('formula', '-')}", language="text")

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.success(f"**Ставка АЗЖД (Net ADY):**\n### {part3.get('net_ady_rate', '-')}")
    with res_col2:
        st.info(f"**Ставка ADY Express (+2% Surcharge):**\n### {part3.get('express_rate', '-')}")

    # --- Примечания и правила ---
    notes = part3.get("notes", [])
    if notes:
        st.markdown("**Примечания и правила / Qeydlər:**")
        for note in notes:
            st.warning(f"📌 {note}")

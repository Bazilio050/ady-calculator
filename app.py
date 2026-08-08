import os
import streamlit as st
from google import genai
from utils import load_rules_config
from nlu import call_gemini_nlu, validate_nlu_input
from engine import process_full_calculation

# Настройка страницы
st.set_page_config(
    page_title="ADY Express — Tariff Calculator", 
    page_icon="🚆", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Стили для компактного баннера и футера
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #0e2a47 0%, #1a4a75 100%);
        padding: 12px 20px; /* Уменьшен отступ, баннер стал ниже по высоте */
        border-radius: 10px;
        color: white;
        margin-top: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 1.8rem; /* Чуть более компактный заголовок */
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .main-header p {
        color: #b0c4de !important;
        margin: 4px 0 0 0;
        font-size: 0.95rem;
    }
    .agt-footer {
        margin-top: 50px;
        padding: 20px;
        background-color: #f8f9fa;
        border-top: 3px solid #ff5500;
        border-radius: 8px;
        text-align: center;
        color: #333333;
    }
    .agt-footer p {
        margin: 2px 0;
        font-size: 0.95rem;
    }
    .agt-slogan {
        font-size: 0.85rem;
        letter-spacing: 2px;
        color: #555555;
        text-transform: uppercase;
        margin-top: 5px !important;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

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
        "disclaimer": "Qeyd olunan tariflərə stansiya xərcləri və əlavə yığımlar daxil deyildir.",
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
        "note_import_base_150": "İdxal/İxrac rejimində 1.50 baza əmsalı tətbiq olunmuşdur.",
        "note_express": "ADY Express xidməti üçün +2% əlavə əmsal tətbiq olunmuşdur.", 
        "note_timber_metal": "İdxal rejimində meşə materialları və qara metallar üçün 1.04 əmsalı tətbiq edilmişdir.",
        "note_ref_transit_120": "Tranzit rejimində izotermik vaqonlar üçün 1.20 əmsalı tətbiq olunmuşdur.", 
        "note_coef_1015": "Tətbiq olunan əlavə əmsal: 1.015.",
        "note_min_weight": "Hesablama minimal norma üzrə aparılmışdır.", 
        "note_ref_composition": "Refseksiyanın vaqon tərkibinə uyğun müvafiq əmsal tətbiq edilmişdir.",
        "unit_ton": "USD/t", 
        "unit_wagon": "USD/vaqon", 
        "table_name": "Cədvəl", 
        "missing_title": "⚠️ Hesablama üçün aşağıdakı məlumatlar çatışmır:",
        "footer_owner": "Bu layihə **AGT Cargo** şirkətinə məxsusdur."
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
        "disclaimer": "Ставки приведены без учета станционных расходов и дополнительных сборов.",
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
        "api_label": "Gemini API Key:",
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
        "note_min_weight": "Расчет произведен по минимальной весовой норме.", 
        "note_ref_composition": "Применен соответствующий коэффициент согласно составу рефсекции.",
        "unit_ton": "USD/т", 
        "unit_wagon": "USD/вагон", 
        "table_name": "Таблица", 
        "missing_title": "⚠️ Для точного расчета не хватает следующих данных:",
        "footer_owner": "Данный проект принадлежит компании **AGT Cargo**."
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
        "disclaimer": "Rates are quoted excluding station charges and additional fees.",
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
        "api_label": "Gemini API Key:",
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
        "note_min_weight": "Calculation is based on minimum weight.", 
        "note_ref_composition": "Coefficient applied according to refrigerated section composition.",
        "unit_ton": "USD/t", 
        "unit_wagon": "USD/wagon", 
        "table_name": "Table", 
        "missing_title": "⚠️ Required parameters missing:",
        "footer_owner": "This project belongs to **AGT Cargo**."
    }
}

logo_path = "Logo.png" if os.path.exists("Logo.png") else ("logo.png" if os.path.exists("logo.png") else None)

# --- ВЕРХНЯЯ ШАПКА: СЛЕВА ЛОГОТИП, СПРАВА В ОДНУ КОЛОНКУ ДРУГ ПОД ДРУГОМ (DIL, ZAMAY) ---
top_col1, top_col2 = st.columns([3, 2])
with top_col1:
    if logo_path:
        st.image(logo_path, width=220)
with top_col2:
    selected_lang = st.selectbox(f"🌐 {UI_TEXT['AZ']['lang_select']}", options=["AZ", "RU", "EN"], index=0)
    t = UI_TEXT[selected_lang]
    selected_year = st.selectbox(f"⚙️ {t['year_select']}", options=["2026", "2027"], index=0)

# --- НИЗКИЙ И КОМПАКТНЫЙ СИНИЙ БАННЕР ---
st.markdown(f"""
    <div class="main-header">
        <h1>🚆 {t['title']}</h1>
        <p>{t['subtitle'].format(selected_year)}</p>
    </div>
""", unsafe_allow_html=True)

# --- ПОЛЕ ВВОДА ---
user_input = st.text_area(t["input_header"], height=130, placeholder=t["input_placeholder"])
user_api_key = os.environ.get("GEMINI_API_KEY", "")

if st.button(t["calc_btn"], type="primary"):
    if not user_input.strip():
        st.warning(t["warning_empty"])
    else:
        client = genai.Client(api_key=user_api_key.strip())
        try:
            nlu_res = call_gemini_nlu(client, user_input, selected_lang)
            
            with st.expander("🔍 Gemini NLU JSON (Для проверки распознавания)"):
                st.json(nlu_res)

            missing = validate_nlu_input(nlu_res, selected_lang)
            if missing:
                st.warning(t["missing_title"])
                for m in missing:
                    st.markdown(f"* {m}")
            else:
                data = process_full_calculation(nlu_res, user_input, selected_lang, selected_year, t)
                st.success(t["success"].format(selected_year))
                
                p1, p2, p3 = data["part1"], data["part2"], data["part3"]
                
                st.markdown(f"#### 📍 {t['sec1_title']}")
                st.markdown(f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n| **{t['lbl_route']}** | {p1['route']} |\n| **{t['lbl_type']}** | {p1['shipment_type']} |\n| **{t['lbl_dist']}** | {p1['distance']} |\n| **{t['lbl_cargo']}** | {p1['cargo_and_wagon']} |\n| **{t['lbl_weight']}** | {p1['weight_info']} |\n| **{t['lbl_period']}** | {p1['period']} |")

                st.markdown(f"#### ⚙️ {t['sec2_title']}")
                t2_rows = [f"| **{t['lbl_exchange']}** | {p2['exchange_rate']} |", f"| **{t['lbl_base_rate']}** | {p2['base_tariff']} |"]
                for coeff in p2["coefficients"]:
                    t2_rows.append(f"| **{coeff['name']}** | {coeff['value']} |")
                st.markdown(f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n" + "\n".join(t2_rows))

                st.markdown(f"#### 📐 {t['sec3_title']}")
                st.code(p3["formula"], language="text")
                st.markdown(f"| {t['col_rate_type']} | {t['col_amount']} |\n| :--- | :--- |\n| **{t['lbl_net_rate']}** | **{p3['net_ady_rate']}** |\n| **{t['lbl_express_rate']}** | **{p3['express_rate']}** |")

                if p3["notes"]:
                    st.markdown(f"**{t['notes_title']}**")
                    for idx, note in enumerate(p3["notes"], start=1):
                        st.markdown(f"{idx}. *{note}*")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# --- ПОДВАЛ ПО ЦЕНТРУ В САМОМ КОНЦЕ СТРАНИЦЫ ---
st.markdown(f"""
    <div class="agt-footer">
        <p>{t['footer_owner']}</p>
        <p class="agt-slogan">BE GLOBAL CONNECTED</p>
    </div>
""", unsafe_allow_html=True)

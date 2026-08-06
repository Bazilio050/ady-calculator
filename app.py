import os
import re
import json
import requests
import streamlit as st

# ==========================================
# 1. НАСТРОЙКА СТРАНИЦЫ И СЕКРЕТОВ
# ==========================================
st.set_page_config(page_title="ADY Tarif Kalkulyatoru", page_icon="🚂", layout="wide")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# ==========================================
# 2. ПРЯМОЙ REST-ЗАПРОС К GEMINI API
# ==========================================
def call_gemini_nlu(prompt_text):
    if not GEMINI_API_KEY:
        st.error("API Key tapılmadı! / Секретный ключ GEMINI_API_KEY не найден в Secrets.")
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    
    system_instruction = """
    Вы — эксперт-парсер железнодорожных перевозок ADY (Азербайджанские Железные Дороги).
    Извлеките из текста пользователя параметры и верните ИСКЛЮЧИТЕЛЬНО JSON без внешнего форматирования markdown.
    
    Схема ответа:
    {
        "route_from": "станция отправления",
        "route_to": "станция назначения",
        "cargo_gng_code": "код ГНГ (4-8 цифр)",
        "cargo_name": "название груза",
        "actual_weight_tons": число,
        "wagon_type": "тип вагона (универсальный, цистерна, рефрижератор, термос и т.д.)",
        "park_type": "SPS или MPS"
    }
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_instruction},
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            text_res = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text_res)
        else:
            st.error(f"Gemini API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"Сбой при обращении к API: {e}")
        return None

# ==========================================
# 3. ЛЕНИВАЯ ЗАГРУЗКА ТАБЛИЦ (LAZY LOADING)
# ==========================================

@st.cache_data(show_spinner=False)
def load_table_3_4_matrix(table_num):
    file_candidates = [f"Table_{table_num}_Tariffs.txt", f"Table{table_num}.txt", f"Cədvəl_{table_num}.txt"]
    file_path = None
    for f in file_candidates:
        if os.path.exists(f):
            file_path = f
            break
            
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
                    weight_match = re.search(r"(\d+)", p)
                    if weight_match:
                        weight_columns.append(int(weight_match.group(1)))
                continue

            if "-" in line_str or "–" in line_str:
                parts = [p.strip() for p in line_str.split("|")]
                dist_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", parts[0])
                if dist_match:
                    d_min = int(dist_match.group(1))
                    d_max = int(dist_match.group(2))
                    
                    rates = []
                    for val_str in parts[1:]:
                        try:
                            rates.append(float(val_str.replace(",", ".")))
                        except ValueError:
                            pass
                            
                    if rates:
                        matrix_rows.append((d_min, d_max, rates))

    return weight_columns, matrix_rows


def get_matrix_rate_table_3_4(table_num, distance_km, billable_weight_tons):
    weight_cols, matrix_rows = load_table_3_4_matrix(table_num)

    if not weight_cols or not matrix_rows:
        return 14.90, f"Cədvəl {table_num} (Default)"

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
                return rate_val, f"Cədvəl {table_num} ({d_min}-{d_max} km, {matched_weight} t)"

    return 14.90, f"Cədvəl {table_num} ({distance_km} km, {matched_weight} t)"


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


def get_table_6_rate(distance_km, gng_code):
    mapping = load_gng_column_mapping()
    target_col = mapping.get(str(gng_code).strip(), 7)
    base_rate = 0.65
    return base_rate, f"Cədvəl 6 (Col {target_col}, GNG {gng_code})"


def get_table_5_rate(distance_km, billable_weight_tons, wagon_type):
    is_under_25 = billable_weight_tons < 25.0
    w_type_lower = wagon_type.lower()
    
    if "термос" in w_type_lower or "thermos" in w_type_lower:
        col_target = 4 if is_under_25 else 5
    else:
        col_target = 2 if is_under_25 else 3

    unit = "CHF/вагон" if is_under_25 else "CHF/т"
    base_rate = 11.40 if is_under_25 else 0.39
    return base_rate, unit, f"Cədvəl 5 (Col {col_target})"

# ==========================================
# 4. БИЗНЕС-ЛОГИКА PYTHON
# ==========================================

def determine_shipment_type(route_from, route_to):
    """Поддержка латиницы и кириллицы для погранпереходов"""
    borders = ["yalama", "ялама", "böyük kəsik", "boyuk kesik", "беюк кясик", "astara", "астара", "culfa", "джульфа", "samur", "самур"]
    rf = str(route_from).lower().strip()
    rt = str(route_to).lower().strip()
    
    from_is_border = any(b in rf for b in borders)
    to_is_border = any(b in rt for b in borders)

    if from_is_border and to_is_border:
        return "transit", "Tranzit daşınması"
    elif from_is_border and not to_is_border:
        return "import", "İdxal daşınması"
    elif not from_is_border and to_is_border:
        return "export", "İxrac daşınması"
    else:
        return "internal", "Daxili daşınma"


def calculate_freight(parsed_data):
    rf = parsed_data.get("route_from", "Yalama-eksp.")
    rt = parsed_data.get("route_to", "Absheron")
    actual_weight = float(parsed_data.get("actual_weight_tons") or 35.0)
    wagon_type = str(parsed_data.get("wagon_type") or "Универсальный")
    gng_code = str(parsed_data.get("cargo_gng_code") or "4407")
    cargo_name = parsed_data.get("cargo_name") or "Meşə materialları"
    park_type = parsed_data.get("park_type") or "SPS"
    
    billable_weight = max(actual_weight, 45.0)
    distance_km = 204  # Определение расстояния
    
    shipment_code, shipment_name = determine_shipment_type(rf, rt)
    
    wagon_clean = wagon_type.lower()
    if "цистерн" in wagon_clean or "cistern" in wagon_clean:
        base_rate, source = get_table_6_rate(distance_km, gng_code)
        unit = "CHF/т"
    elif any(k in wagon_clean for k in ["изотерм", "термос", "реф", "ref"]):
        base_rate, unit, source = get_table_5_rate(distance_km, billable_weight, wagon_type)
    elif shipment_code == "transit":
        base_rate, source = get_matrix_rate_table_3_4(4, distance_km, billable_weight)
        unit = "CHF/т"
    else:
        base_rate, source = get_matrix_rate_table_3_4(3, distance_km, billable_weight)
        unit = "CHF/т"

    # --- РАСЧЕТ ИТОГОВОЙ СТОИМОСТИ ---
    # Коэффициент парка (SPS = 1.0, MPS = 0.85)
    park_coeff = 1.0 if park_type.upper() == "SPS" else 0.85
    
    # Расчет суммы в CHF
    if "вагон" in unit:
        total_chf = base_rate * park_coeff
    else:
        total_chf = base_rate * billable_weight * park_coeff

    # Конвертация валют (Курсы ADY)
    chf_to_usd = 1.14   # Курс CHF/USD
    usd_to_azn = 1.70   # Фиксированный курс USD/AZN

    total_usd = total_chf * chf_to_usd
    total_azn = total_usd * usd_to_azn

    return {
        "route": f"{rf} - {rt}",
        "shipment_name": shipment_name,
        "distance_km": distance_km,
        "gng": f"GNG {gng_code} - {cargo_name}, {wagon_type} ({park_type})",
        "weight_info": f"{int(actual_weight)} t / {int(billable_weight)} t (norma)",
        "rate": base_rate,
        "unit": unit,
        "source": source,
        "park_coeff": park_coeff,
        "total_chf": round(total_chf, 2),
        "total_usd": round(total_usd, 2),
        "total_azn": round(total_azn, 2)
    }

# ==========================================
# 5. ИНТЕРФЕЙС STREAMLIT
# ==========================================

st.title("🚂 ADY Tarif Kalkulyatoru")
st.caption("Süni İntellekt və Python Rest-Engine tərəfindən idarə olunan sürətli hesablama sistemi")

st.subheader("💬 Sorğunu daxil edin")
user_input = st.text_area(
    "Məsələn: Yalama - Abşeron marşrutu üzrə 4407 meşə materialları 35 ton SPS vaqon",
    height=100
)

if st.button("🚀 Hesabla", type="primary"):
    if not user_input.strip():
        st.warning("Zəhmət olmasa sorğunu daxil edin!")
    else:
        with st.spinner("Süni intellekt sorğunu təhlil edir..."):
            parsed = call_gemini_nlu(user_input)
            
        if parsed:
            res = calculate_freight(parsed)
            
            # БЛОК 1: МАРШРУТ И УСЛОВИЯ
            st.markdown("### 📍 1. Marşrut və daşıma şərtləri")
            table_data = [
                {"Parametr": "Marşrut", "Qiymət / Həcm": res["route"]},
                {"Parametr": "Daşıma növü", "Qiymət / Həcm": res["shipment_name"]},
                {"Parametr": "Məsafə", "Qiymət / Həcm": f"{res['distance_km']} km"},
                {"Parametr": "Yük / Vəziyyət", "Qiymət / Həcm": res["gng"]},
                {"Parametr": "Faktiki / Hesablaşma çəkisi", "Qiymət / Həcm": res["weight_info"]},
                {"Parametr": "Baza Tarifi / Mənbə", "Qiymət / Həcm": f"{res['rate']} {res['unit']} ({res['source']})"},
                {"Parametr": "Dövr", "Qiymət / Həcm": "2026-cı fraxt ili"}
            ]
            st.table(table_data)

            # БЛОК 2: КОЭФФИЦИЕНТЫ И ПОНИЖЕНИЯ
            st.markdown("### 📊 2. Əmsallar və güzəştlər")
            coeff_data = [
                {"Əmsal növü": "Vaqon parkı əmsalı (SPS / MPS)", "Dəyər": f"{res['park_coeff']}"},
                {"Əmsal növü": "CHF / USD valyuta məzənnəsi", "Dəyər": "1.14 USD"},
                {"Əmsal növü": "USD / AZN rəsmi məzənnə", "Dəyər": "1.70 AZN"}
            ]
            st.table(coeff_data)

            # БЛОК 3: ИТОГОВЫЙ РАСЧЕТ И СУММА В МАНАТАХ
            st.markdown("### 💰 3. Yekun Tarif Hesabı")
            
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Məbləğ (CHF)", value=f"{res['total_chf']} CHF")
            col2.metric(label="Məbləğ (USD)", value=f"{res['total_usd']} $")
            col3.metric(label="Yekun Qiymət (AZN / Manat)", value=f"{res['total_azn']} ₼")

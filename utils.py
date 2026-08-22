import os
import re
from datetime import datetime

# ==============================================================================
# 1. РЕЕСТР ПОГРАНИЧНЫХ СТАНЦИЙ И ЕСР-КОДОВ
# ==============================================================================

BORDER_ESR_CODES = {
    "545006", "547508", "545307", "545107",
    "558631", "558701", "558504", "558400",
    "554109", "554503", "553905",
    "550004", "550108", "550803",
    "550502", "550409",
    "549204", "553002", "548803", "547302", "547406", "547209", "548502", "548703"
}

BORDER_COLUMN_MAP = {
    "545006": 3, "547508": 3, "545307": 3, "545107": 3,
    "554109": 4, "554503": 4, "553905": 4,
    "558701": 5, "558631": 5, "558504": 5, "558400": 5,
    "550004": 6, "550108": 6, "550803": 6,
    "549204": 7, "553002": 7, "548803": 7, "547302": 7, 
    "547406": 7, "547209": 7, "548502": 7, "548703": 7
}

BORDER_STATION_ESR_OVERRIDE = {
    "boyuk kesik": "558701",
    "yalama": "547508",
    "astara": "554109",
    "culfa": "550004",
    "serur": "550409",
    "alet": "548502",
    "elet": "548502",
    "алят": "548502"
}

def is_border_esr(esr_code: str) -> bool:
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    return clean_esr in BORDER_ESR_CODES

def format_station_display_name(raw_name: str, esr_code: str, site_lang: str = "AZ") -> str:
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    st_name = str(raw_name or "").strip()

    if is_border_esr(clean_esr):
        lang_upper = str(site_lang or "AZ").upper()
        suffix = "-эксп." if lang_upper == "RU" else ("-exp." if lang_upper == "EN" else "-eksp.")
        if not st_name.endswith(suffix):
            st_name = f"{st_name}{suffix}"

    return f"{st_name} ({clean_esr})" if clean_esr else st_name

# ==============================================================================
# 2. ПОИСК И АВТО-РЕЗОЛВ ЕСР ПО НАЗВАНИЮ И КИЛОМЕТРАЖУ
# ==============================================================================

def resolve_esr_by_station_name(station_name: str, user_input_raw: str = "") -> str:
    if not station_name:
        return ""

    clean = re.sub(r'-(eksp|эксп|exp)\b', '', str(station_name), flags=re.IGNORECASE).strip().lower()
    clean_norm = clean.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')

    for b_name, b_esr in BORDER_STATION_ESR_OVERRIDE.items():
        if b_name in clean_norm or clean_norm in b_name:
            return b_esr

    possible_paths = ["Distances.txt", "tariff_data/Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = next((p for p in possible_paths if os.path.exists(p)), None)

    if dist_file:
        try:
            with open(dist_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" not in line or ":---" in line or "Stansiyanın" in line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) < 3:
                        continue
                    file_st_name = parts[1].replace("*", "").strip().lower()
                    file_st_name = file_st_name.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
                    file_esr = re.sub(r'\D', '', parts[2])
                    if clean_norm and file_st_name and (clean_norm in file_st_name or file_st_name in clean_norm):
                        return file_esr
        except Exception as e:
            print(f"Error resolving ESR: {e}")

    return ""

def get_distance_by_esr(esr_from: str, esr_to: str) -> int:
    if not esr_from or not esr_to:
        return None

    c_from = re.sub(r'\D', '', str(esr_from))
    c_to = re.sub(r'\D', '', str(esr_to))

    if not c_from or not c_to:
        return None

    if c_from == c_to or c_from[:5] == c_to[:5]:
        return 0

    col_idx = BORDER_COLUMN_MAP.get(c_to)
    target_row_esr = c_from

    if col_idx is None:
        col_idx = BORDER_COLUMN_MAP.get(c_from)
        target_row_esr = c_to

    if col_idx is None:
        col_idx = 3

    possible_paths = ["Distances.txt", "tariff_data/Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = next((p for p in possible_paths if os.path.exists(p)), None)

    if not dist_file:
        return None

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            for line in f:
                if "|" not in line or ":---" in line or "Stansiyanın" in line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) <= col_idx:
                    continue
                row_esr_code = re.sub(r'\D', '', parts[2])
                if row_esr_code and (row_esr_code[:5] in target_row_esr or target_row_esr[:5] in row_esr_code):
                    val_str = re.sub(r'\D', '', parts[col_idx])
                    if val_str and val_str.isdigit():
                        return int(val_str)
    except Exception as e:
        print(f"Error reading Distances.txt: {e}")

    return None

def get_calculation_distance(distance_km: int, shipment_type: str) -> int:
    st_lower = str(shipment_type or "").lower()
    if any(k in st_lower for k in ["ixrac", "export", "экспорт"]):
        return max(distance_km, 101)
    if any(k in st_lower for k in ["idxal", "import", "импорт"]):
        return max(distance_km, 151)
    return distance_km

# ==============================================================================
# 3. ВЕСОВЫЕ НОРМЫ И КОЭФФИЦИЕНТЫ
# ==============================================================================

def extract_gng_digits(gng_code, kwargs=None) -> str:
    kwargs = kwargs or {}
    candidates = [gng_code, kwargs.get("gng_code"), kwargs.get("gng"), kwargs.get("cargo_code")]
    for c in candidates:
        if c:
            m = re.search(r"\d+", str(c))
            if m:
                return m.group(0)
    return ""

def get_min_weight_by_gng(gng_code: str, actual_weight_tons: float) -> float:
    g = extract_gng_digits(gng_code)
    w = float(actual_weight_tons or 0)
    if not g:
        return w
    if g.startswith("4403") or g.startswith("4404") or g.startswith("4407"):
        return max(w, 45.0)
    if g.startswith("72") or g.startswith("1001") or g.startswith("1701"):
        return max(w, 60.0)
    if g.startswith("5201") or g.startswith("5202"):
        return max(w, 50.0)
    return max(w, 10.0)

def is_non_ferrous_metal_gng(gng_code: str) -> bool:
    clean_gng = extract_gng_digits(gng_code)
    if not clean_gng: return False
    return clean_gng.startswith("78") or clean_gng.startswith("74") or clean_gng.startswith("75") or clean_gng.startswith("76")

def is_alat_boyuk_kesik_route(origin_esr: str, dest_esr: str, shipment_type: str) -> bool:
    st_lower = str(shipment_type or "").lower()
    if "tranzit" not in st_lower and "transit" not in st_lower and "транзит" not in st_lower:
        return False
    o_esr = re.sub(r'\D', '', str(origin_esr or ""))
    d_esr = re.sub(r'\D', '', str(dest_esr or ""))
    alat_codes = ["549204", "553002", "548803", "547302", "547406", "547209", "548502", "548703"]
    bk_codes = ["558631", "558701", "558504", "558400"]
    return (o_esr in alat_codes and d_esr in bk_codes) or (o_esr in bk_codes and d_esr in alat_codes)

def get_global_coefficients(shipment_type: str, gng_code: str, origin_esr: str = None, dest_esr: str = None, lang: str = "AZ") -> tuple:
    coeffs, notes = [], []
    if is_non_ferrous_metal_gng(gng_code):
        coeffs.append(("Əlvan metal 1.20", 1.20))
    if is_alat_boyuk_kesik_route(origin_esr, dest_esr, shipment_type):
        coeffs.append(("Ələt - B.Kəsik marşrutu 1.20", 1.20))
    return coeffs, notes

def load_rules_config(filepath: str = "RULES.md") -> str:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

CURRENCY_RATES_TABLE = [
    ("01.01.2026", "31.12.2026", 0.79)
]

def parse_date_from_string(text: str):
    return datetime.now()

def get_exchange_rate_for_date(target_date=None) -> tuple:
    return 0.79, "01.01.2026 - 31.12.2026"

def should_apply_150_coeff(shipment_type_code: str, table_num: int, gng_code: str, wagon_type: str, park_type: str = "SPS") -> bool:
    st = str(shipment_type_code or "").lower()
    if not any(k in st for k in ["import", "export", "idxal", "ixrac"]):
        return False
    if table_num in [3, 3.22, 3.71, 3.72, 3.78, 3.9]:
        return False
    return True

def get_transporter_min_weight(axle_count: int, actual_weight: float) -> float:
    if axle_count in [4, 6, 8]:
        return max(actual_weight, axle_count * 5.0)
    return actual_weight

def is_long_platform_scep(raw_text: str, wagon_type: str = "") -> bool:
    text_lower = (str(raw_text or "") + " " + str(wagon_type or "")).lower()
    return any(re.search(p, text_lower) for p in [r'19\s*m', r'19\s*м', r'>\s*19', r'сцеп', r'scep', r'qoşqu'])

import os
import json
import re


def load_table_5_config():
    config_path = "tables/table_5_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_table_5_rates():
    possible_files = [
        "Table_5_Tariffs.txt",
        "Table5.txt",
        "tables/Table_5_Tariffs.txt",
        "tables/Table5.txt",
        "tariff_data/Table_5_Tariffs.txt",
        "tariff_data/Table5.txt"
    ]

    t_file = None
    for pf in possible_files:
        if os.path.exists(pf):
            t_file = pf
            break

    rates = []
    if t_file and os.path.exists(t_file):
        with open(t_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("#") or line_str.startswith("="):
                    continue

                r_match = re.search(r"^(\d+)\s*[-–]\s*(\d+)", line_str)
                if r_match:
                    d_min, d_max = int(r_match.group(1)), int(r_match.group(2))
                    parts = line_str.split("|")
                    if len(parts) > 1:
                        vals = [float(p.strip().replace(",", ".")) for p in parts[1:] if p.strip()]
                        rates.append((d_min, d_max, vals))
                    else:
                        numbers = re.findall(r"(\d+[\.,]\d+|\d+)", line_str)
                        if len(numbers) >= 2:
                            vals = [float(x.replace(",", ".")) for x in numbers[2:]]
                            rates.append((d_min, d_max, vals))
    return rates


def parse_ref_composition(user_input_str):
    """
    Парсинг ж/д нотации состава рефсекции: 5+1, 1+5, 6+1, 3+1 и т.д.
    Возвращает количество грузовых вагонов.
    """
    if not user_input_str:
        return None

    st = str(user_input_str).lower().replace(" ", "")
    m = re.search(r"(\d+)\+(\d+)", st)
    if m:
        num1, num2 = int(m.group(1)), int(m.group(2))
        # Обычная логика: 1 — это дизель-генератор, большая цифра — грузовые вагоны
        if num1 == 1:
            return num2
        elif num2 == 1:
            return num1
        else:
            return max(num1, num2)

    m_single = re.search(r"(\d+)\s*(?:ваг|vaq|wag)", st)
    if m_single:
        return int(m_single.group(1))

    return None


def calculate_table_5_base(distance_km, billable_weight_tons, wagon_type, *args, lang="AZ", **kwargs):
    """
    Расчёт базовой ставки Таблицы 5.
    Возвращает: (base_chf, details_str, is_per_wagon)
    """
    w_type_lower = str(wagon_type or "").lower()
    
    col_idx = 0
    is_per_wagon = True

    # 1. Определение колонки и типа ставки (за вагон / за тонну)
    if any(k in w_type_lower for k in ["thermos", "термос", "lednik", "ледник"]):
        if billable_weight_tons < 25.0:
            col_idx = 2  # Col 4: Термос < 25t (per wagon)
            is_per_wagon = True
        else:
            col_idx = 3  # Col 5: Термос >= 25t (per ton)
            is_per_wagon = False

    elif any(k in w_type_lower for k in ["auto", "авто"]):
        col_idx = 4      # Col 6: Автомобилевоз (per ton, min 10t)
        is_per_wagon = False

    elif "inv" in w_type_lower or "anv" in w_type_lower:
        if "boş" in w_type_lower or "empty" in w_type_lower or "порожн" in w_type_lower:
            col_idx = 6  # Col 8: İNV/ANV порожний (per wagon)
        else:
            col_idx = 5  # Col 7: İNV/ANV гружёный (per wagon)
        is_per_wagon = True

    else:
        # По умолчанию — Рефрижератор / АРВ
        if billable_weight_tons < 25.0:
            col_idx = 0  # Col 2: Реф < 25t (per wagon)
            is_per_wagon = True
        else:
            col_idx = 1  # Col 3: Реф >= 25t (per ton)
            is_per_wagon = False

    rates = load_table_5_rates()
    tbl_name = "Cədvəl 5" if lang == "AZ" else ("Таблица 5" if lang == "RU" else "Table 5")

    if not rates:
        return None, f"{tbl_name} faylı tapılmadı", True

    base_chf = None
    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            if col_idx < len(vals):
                base_chf = vals[col_idx]
            elif len(vals) > 0:
                base_chf = vals[-1]
            break

    if base_chf is None:
        return None, f"{tbl_name}, {distance_km} km", is_per_wagon

    details_str = f"{tbl_name} ({distance_km} km)"
    return base_chf, details_str, is_per_wagon


def get_table_5_coefficients(shipment_type_code=None, wagon_type=None, gng_code=None, 
                           ref_wagons_cnt=None, is_2tier_platform=False, 
                           is_fruit_veg_discount=False, lang="AZ", *args, **kwargs):
    """
    Возвращает специфические коэффициенты Таблицы 5.
    """
    coeffs = []
    notes = []

    # 1. Состав рефсекции (парсинг 5+1, 1+5 и т.д.)
    parsed_cnt = parse_ref_composition(ref_wagons_cnt or kwargs.get("composition") or kwargs.get("prompt"))
    if parsed_cnt is not None:
        w_cnt = parsed_cnt
        c_val = None
        if w_cnt >= 5:
            c_val = 0.85
        elif w_cnt == 3:
            c_val = 1.10
        elif w_cnt == 2:
            c_val = 1.40
        elif w_cnt == 1:
            c_val = 1.70

        if c_val and c_val != 1.0:
            lbl = f"Ref {w_cnt}+1 vaqon ({c_val})" if lang == "AZ" else f"Реф {w_cnt}+1 вагон ({c_val})"
            coeffs.append((lbl, c_val))
            notes.append(f"Cədvəl 5: Refseksiyanın vaqon tərkibinə ({w_cnt}+1) uyğun {c_val} əmsalı tətbiq olunmuşdur.")

    # 2. Автомобилевозы на двухэтажных платформах (0.80)
    w_type_lower = str(wagon_type or "").lower()
    if ("auto" in w_type_lower or "авто" in w_type_lower) and (is_2tier_platform or "platform" in w_type_lower or "платформ" in w_type_lower):
        lbl = "İkimərtəbəli platforma 0.80" if lang == "AZ" else "Двухэтажная платформа 0.80"
        coeffs.append((lbl, 0.80))
        notes.append("Cədvəl 5: Avtomobil daşıyan ikimərtəbəli platforma üçün 0.80 əmsalı tətbiq olunmuşdur.")

    # 3. Плодоовощная скидка (0.60) — ТОЛЬКО если запрошено пользователем
    if is_fruit_veg_discount or kwargs.get("fruit_veg_requested"):
        lbl = "Meyvə-tərəvəz güzəşti 0.60" if lang == "AZ" else "Скидка плодоовощная 0.60"
        coeffs.append((lbl, 0.60))
        notes.append("Cədvəl 5: Tarif Razılaşması iştirakçısı olan ölkələrin meyvə-tərəvəz yükünə 0.60 güzəşt əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

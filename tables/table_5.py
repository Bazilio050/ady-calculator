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
    Расчёт базовой ставки Таблицы 5 (Спецплатформы, İNV/ANV, Рефрижераторы).
    Раздел 3.3 (п. 3.3.1 и 3.3.2)
    Возвращает: (base_chf, details_str, is_per_wagon)
    """
    w_type_lower = str(wagon_type or "").lower()
    raw_input = str(kwargs.get("user_input_raw") or kwargs.get("raw_text") or kwargs.get("cargo_name") or "").lower()
    full_type_str = f"{w_type_lower} {raw_input}"
    
    col_idx = 0
    is_per_wagon = True

    # Проверка на порожнее состояние
    is_empty_flag = kwargs.get("is_empty", False) or any(k in full_type_str for k in ["boş", "empty", "порожн"])

    # 1. Раздел 3.3: Автопоезда, прицепы, полуприцепы, кузова и İNV/ANV
    road_train_keywords = ["avtoqatar", "автопоезд", "qoşqu", "прицеп", "semitrailer", "yarımqoşqu", "kuzov", "кузов", "inv", "anv"]
    is_road_train = any(k in full_type_str for k in road_train_keywords)

    clause_info = ""
    if is_road_train:
        if is_empty_flag:
            col_idx = 6  # Col 8: İNV/ANV / спецплатформы порожний (per wagon)
            if any(k in full_type_str for k in ["kuzov", "кузов"]):
                clause_info = "boş kuzov 5t - bənd 3.3.2" if lang == "AZ" else ("порожний кузов 5т - п. 3.3.2" if lang == "RU" else "empty body 5t - cl. 3.3.2")
            else:
                clause_info = "boş avtoqatar/qoşqu 7t - bənd 3.3.2" if lang == "AZ" else ("порожний автопоезд/прицеп 7т - п. 3.3.2" if lang == "RU" else "empty road train/trailer 7t - cl. 3.3.2")
        else:
            col_idx = 5  # Col 7: İNV/ANV / спецплатформы гружёный (per wagon)
            clause_info = "yüklü İNV/ANV min 10t - bənd 3.3.1" if lang == "AZ" else ("гружёный İNV/ANV мин 10т - п. 3.3.1" if lang == "RU" else "loaded İNV/ANV min 10t - cl. 3.3.1")
        
        is_per_wagon = True

    # 2. Термосы и ледники
    elif any(k in w_type_lower for k in ["thermos", "термос", "lednik", "ледник"]):
        if billable_weight_tons < 25.0:
            col_idx = 2  # Col 4: Термос < 25t (per wagon)
            is_per_wagon = True
        else:
            col_idx = 3  # Col 5: Термос >= 25t (per ton)
            is_per_wagon = False

    # 3. Автомобилевозы
    elif any(k in w_type_lower for k in ["auto", "авто"]):
        col_idx = 4      # Col 6: Автомобилевоз (per ton, min 10t)
        is_per_wagon = False

    # 4. По умолчанию — Рефрижераторы / АРВ
    else:
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

    if clause_info:
        details_str = f"{tbl_name} ({distance_km} km, sütun {col_idx + 2}, {clause_info})"
    else:
        details_str = f"{tbl_name} ({distance_km} km, sütun {col_idx + 2})"

    return base_chf, details_str, is_per_wagon


def get_table_5_coefficients(shipment_type_code=None, wagon_type=None, gng_code=None, 
                           ref_wagons_cnt=None, is_2tier_platform=False, 
                           is_fruit_veg_discount=False, lang="AZ", *args, **kwargs):
    coeffs = []
    notes = []

    # Собираем весь доступный текст для парсинга комбинаций
    full_text_search = " ".join([
        str(ref_wagons_cnt or ""),
        str(kwargs.get("ref_wagons_cnt") or ""),
        str(kwargs.get("composition") or ""),
        str(kwargs.get("prompt") or ""),
        str(kwargs.get("user_input_raw") or ""),
        str(kwargs.get("user_input") or ""),
        str(kwargs.get("raw_text") or "")
    ])

    # 1. Состав рефсекции (парсинг 5+1, 1+5, 6+1, 3+1 и т.д.)
    if isinstance(ref_wagons_cnt, int):
        parsed_cnt = ref_wagons_cnt
    else:
        parsed_cnt = parse_ref_composition(full_text_search)

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
            lbl = "Refseksiya tərkibi" if lang == "AZ" else ("Состав рефсекции" if lang == "RU" else "Ref section composition")
            coeffs.append((lbl, c_val))
            notes.append(f"Cədvəl 5: Refseksiyanın vaqon tərkibinə ({w_cnt}+1) uyğun {c_val} əmsalı tətbiq olunmuşdur.")

    # 2. Автомобилевозы на двухэтажных платформах (0.80)
    w_type_lower = str(wagon_type or "").lower()
    if ("auto" in w_type_lower or "авто" in w_type_lower) and (is_2tier_platform or "platform" in w_type_lower or "платформ" in w_type_lower):
        lbl = "İkimərtəbəli platforma" if lang == "AZ" else ("Двухэтажная платформа" if lang == "RU" else "Double-deck platform")
        coeffs.append((lbl, 0.80))
        notes.append("Cədvəl 5: Avtomobil daşıyan ikimərtəbəli platforma üçün 0.80 əmsalı tətbiq olunmuşdur.")

    # 3. Плодоовощная скидка (0.60) — ТОЛЬКО если запрошено пользователем
    if is_fruit_veg_discount or kwargs.get("fruit_veg_requested"):
        lbl = "Meyvə-tərəvəz güzəşti" if lang == "AZ" else ("Скидка плодоовощная" if lang == "RU" else "Fruit & Veg discount")
        coeffs.append((lbl, 0.60))
        notes.append("Cədvəl 5: Tarif Razılaşması iştirakçısı olan ölkələrin meyvə-tərəvəz yükünə 0.60 güzəşt əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

import os
import re

# ==============================================================================
# 1. РЕЕСТР ПОГРАНИЧНЫХ СТАНЦИЙ И ЕСР-КОДОВ (RULES.md -> Раздел 2)
# ==============================================================================

BORDER_ESR_CODES = {
    # Ялама
    "545006", "547508",
    # Беюк Кясик
    "558631", "558701",
    # Астара
    "554109", "554503",
    # Джульфа
    "550004", "550108",
    # Шарур
    "550502", "550409",
    # Алят (Паром / Бакинский Порт)
    "549204", "553002", "548803", "547302", "547406", "547209"
}


def is_border_esr(esr_code: str) -> bool:
    """
    Проверяет, является ли код ЕСР пограничным переходом.
    """
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    return clean_esr in BORDER_ESR_CODES


def format_station_display_name(raw_name: str, esr_code: str, site_lang: str = "AZ") -> str:
    """
    Форматирует название станции для итогового отчёта:
    Прибавляет суффикс погранперехода (-eksp. / -эксп. / -exp.), если ЕСР пограничный.
    """
    clean_esr = re.sub(r'\D', '', str(esr_code or ""))
    st_name = str(raw_name or "").strip()

    if is_border_esr(clean_esr):
        lang_upper = str(site_lang or "AZ").upper()
        if lang_upper == "RU":
            suffix = "-эксп."
        elif lang_upper == "EN":
            suffix = "-exp."
        else:
            suffix = "-eksp."

        if not st_name.endswith(suffix):
            st_name = f"{st_name}{suffix}"

    return f"{st_name} ({clean_esr})" if clean_esr else st_name


# ==============================================================================
# 2. ПОИСК КИЛОМЕТРАЖА ПО ЕСР-КОДАМ (Distances.txt)
# ==============================================================================

def get_distance_by_esr(esr_from: str, esr_to: str) -> int:
    """
    Точный поиск километража в матрице Distances.txt по 6-значным кодам ЕСР.
    """
    clean_from = re.sub(r'\D', '', str(esr_from or ""))
    clean_to = re.sub(r'\D', '', str(esr_to or ""))

    if not clean_from or not clean_to:
        return None

    possible_paths = ["Distances.txt", "data/Distances.txt", "tables/Distances.txt", "tariff_data/Distances.txt"]
    dist_file = None
    for p in possible_paths:
        if os.path.exists(p):
            dist_file = p
            break

    if not dist_file:
        return None

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        header_esr_codes = []
        header_idx = -1

        for idx, line in enumerate(lines):
            if "|" in line:
                codes = [re.sub(r'\D', '', cell) for cell in line.split("|")]
                if any(len(c) >= 5 for c in codes if c):
                    header_esr_codes = codes
                    header_idx = idx
                    break

        if header_idx == -1:
            return None

        for line in lines[header_idx + 1:]:
            if "|" not in line or ":---" in line:
                continue

            row_cells = [c.strip() for c in line.split("|")]
            if len(row_cells) < 3:
                continue

            row_esr = re.sub(r'\D', '', row_cells[1])

            target_col_esr = None
            if clean_from in row_esr or row_esr in clean_from:
                target_col_esr = clean_to
            elif clean_to in row_esr or row_esr in clean_to:
                target_col_esr = clean_from

            if target_col_esr:
                for col_idx, col_esr in enumerate(header_esr_codes):
                    # Проверяем только колонки со значениями расстояний (пропуская служебные колонки с именем и ЕСР)
                    if col_esr and (target_col_esr in col_esr or col_esr in target_col_esr):
                        if col_idx < len(row_cells):
                            val_str = re.sub(r'\D', '', row_cells[col_idx])
                            if val_str:
                                dist_val = int(val_str)
                                # Если прочитанное расстояние совпало с ЕСР-кодом (ошибка колонки) — пропускаем
                                if dist_val != int(target_col_esr) and dist_val != int(row_esr):
                                    return dist_val

    except Exception as e:
        print(f"Ошибка чтения расстояний из {dist_file}: {e}")

    return None


def get_calculation_distance(distance_km: int, shipment_type: str) -> int:
    """
    Применяет минимальные ограничения по расстоянию (RULES.md -> Раздел 4):
    - İxrac (Экспорт): минимум 101 км
    - İdxal (Импорт): минимум 151 км
    """
    st_lower = str(shipment_type or "").lower()

    if any(k in st_lower for k in ["ixrac", "export", "экспорт"]):
        return max(distance_km, 101)

    if any(k in st_lower for k in ["idxal", "import", "импорт"]):
        return max(distance_km, 151)

    return distance_km


# ==============================================================================
# 3. ВЕСОВАЯ СЕТКА (Cədvəl 1) И МИНИМАЛЬНЫЕ НОРМЫ ГНГ (RULES.md -> Раздел 5)
# ==============================================================================

def get_weight_column_index(billable_weight_tons: float) -> int:
    """
    Сопоставление расчётного веса с 11 колонками Cədvəl 1:
    0: 10t (0-12t),  1: 15t (13-16t), 2: 20t (17-23t), 3: 25t (24-26t),
    4: 30t (27-31t), 5: 35t (32-36t), 6: 40t (37-40t), 7: 45t (41-46t),
    8: 50t (47-51t), 9: 55t (52-55t), 10: 60t+ (56t+)
    """
    w = float(billable_weight_tons or 0)
    if w <= 12: return 0
    elif w <= 16: return 1
    elif w <= 23: return 2
    elif w <= 26: return 3
    elif w <= 31: return 4
    elif w <= 36: return 5
    elif w <= 40: return 6
    elif w <= 46: return 7
    elif w <= 51: return 8
    elif w <= 55: return 9
    else: return 10


def extract_gng_digits(gng_code, kwargs=None) -> str:
    """Извлекает численный код ГНГ."""
    kwargs = kwargs or {}
    candidates = [gng_code, kwargs.get("gng_code"), kwargs.get("gng"), kwargs.get("cargo_code")]
    for c in candidates:
        if c:
            m = re.search(r"\d+", str(c))
            if m:
                return m.group(0)
    return ""


def get_min_weight_by_gng(gng_code: str, actual_weight_tons: float) -> float:
    """
    Полный реестр проверки минимальных норм загрузки по ГНГ (60т, 50т, 40т, 30т).
    """
    g = extract_gng_digits(gng_code)
    w = float(actual_weight_tons or 0)
    if not g:
        return w

    # --- 1. НОРМА 60 ТОНН ---
    if g in ["28182000", "7201", "1701", "1107"] or g.startswith("2701") or g.startswith("2702") or g.startswith("10"):
        return max(w, 60.0)
    if g.startswith("26") and not (2618 <= int(g[:4]) <= 2621):
        return max(w, 60.0)
    if g.startswith("31") and not g.startswith("3101"):
        return max(w, 60.0)
    if len(g) >= 4 and 1101 <= int(g[:4]) <= 1103:
        return max(w, 60.0)
    if g.startswith("72") and not g.startswith("7204"):
        return max(w, 60.0)
    
    # Цветмет 60т спец-позиции
    gng_60_non_ferrous = ["28045000", "28045090", "28049", "28053", "28054", "28054010", "28054090", "7106", "7107", "7108", "7109", "7111", "7112", "7402", "7403", "7405", "7406", "7502", "7504", "7601", "7603", "7801", "78042", "7901", "79039", "8001", "81011", "810194", "810199", "81021", "810294", "810299", "81039", "81039090", "810411", "810419", "81049", "81060010", "81072", "81082", "81092", "81101", "81110011", "81121200", "811221", "81122110", "81122190", "81123020", "81124100", "81125100", "81129291", "81129200", "81129210", "81129231", "81129281", "81129289", "81130020"]
    if any(g.startswith(p) for p in gng_60_non_ferrous):
        return max(w, 60.0)

    # --- 2. НОРМА 50 ТОНН ---
    if g.startswith("4403") or g.startswith("4404") or (len(g) >= 4 and 4407 <= int(g[:4]) <= 4413):
        return max(w, 50.0)
    if g.startswith("14042") or (len(g) >= 4 and 5201 <= int(g[:4]) <= 5203):
        return max(w, 50.0)
    if g.startswith("7204") and not g.startswith("72045"):
        return max(w, 50.0)

    gng_50_non_ferrous = ["32121", "71101910", "7407", "7408", "7409", "7410", "7413", "7505", "7506", "7604", "7605", "7606", "7607", "76149", "7804", "78060080", "7904", "7905", "8003", "80070010", "80070080", "81019600", "81029500", "81029600", "81032", "81039010", "81089030", "81089050"]
    if any(g.startswith(p) for p in gng_50_non_ferrous):
        return max(w, 50.0)

    # --- 3. НОРМА 40 ТОНН ---
    gng_40_non_ferrous = ["7404", "7503", "7602", "7802", "7902", "7903", "8002", "81019700", "81029700", "81033000", "81042", "81043", "81053", "81073", "81083", "81093", "81102", "81110019", "81121300", "81122200", "81124110", "81125200", "81130040", "85481", "85493", "85499", "85492000"]
    if any(g.startswith(p) for p in gng_40_non_ferrous):
        return max(w, 40.0)

    # --- 4. НОРМА 30 ТОНН ---
    gng_30_non_ferrous = ["71159", "7411", "7412", "7415", "7419", "7507", "7508", "7608", "7609", "7610", "7611", "7612", "7613", "76152", "7616", "7806", "7907", "8007", "81059", "81060090", "81079", "81089", "81099", "81109", "81110090", "811219", "81122900", "81129920", "81129970", "811259", "81129900", "81129930", "81130090", "8302", "83061", "83079", "8309", "8311", "8481", "8482", "84831", "84832", "84833", "8484"]
    if any(g.startswith(p) for p in gng_30_non_ferrous):
        return max(w, 30.0)

    return w


# ==============================================================================
# 4. ОБЩИЕ КОЭФФИЦИЕНТЫ 1.20 (RULES.md -> Раздел 7)
# ==============================================================================

def is_non_ferrous_metal_gng(gng_code, kwargs=None) -> bool:
    """
    Проверка на Цветные и Драгоценные металлы (Коэффициент 1.20).
    """
    g = extract_gng_digits(gng_code, kwargs)
    if not g:
        return False

    exact_prefixes = ["28045090", "28049", "28054", "32121", "7115", "8302", "83079", "8309", "8311", "85481"]
    if any(g.startswith(p) for p in exact_prefixes):
        return True

    if len(g) >= 4 and 7106 <= int(g[:4]) <= 7112:
        return True

    if g.startswith("74"):
        return not (g.startswith("7401") or g.startswith("7418"))

    if g.startswith("75"):
        return not g.startswith("7501")

    if g.startswith("76"):
        return not g.startswith("7615")

    if g.startswith("78") or g.startswith("79") or g.startswith("80"):
        return True

    if g.startswith("81"):
        return not g.startswith("81052")

    return False


def is_alat_boyuk_kesik_route(origin_esr: str, dest_esr: str, shipment_type: str) -> bool:
    """
    Коэффициент 1.20 для транзитных перевозок по маршруту Ələt - Böyük Kəsik - Ələt.
    """
    st_lower = str(shipment_type or "").lower()
    if not any(k in st_lower for k in ["tranzit", "transit", "транзит"]):
        return False

    o_esr = re.sub(r'\D', '', str(origin_esr or ""))
    d_esr = re.sub(r'\D', '', str(dest_esr or ""))

    alat_codes = ["549204", "553002", "548803", "547302", "547406", "547209", "548502"]
    boyuk_kesik_codes = ["558631", "558701"]

    is_alat_to_bk = any(o_esr == c for c in alat_codes) and any(d_esr == c for c in boyuk_kesik_codes)
    is_bk_to_alat = any(o_esr == c for c in boyuk_kesik_codes) and any(d_esr == c for c in alat_codes)

    return is_alat_to_bk or is_bk_to_alat


def get_global_coefficients(shipment_type: str, gng_code: str, origin_esr: str = None, dest_esr: str = None, lang: str = "AZ") -> tuple:
    """
    Собирает общие коэффициенты, действующие независимо от конкретной таблицы.
    """
    coeffs = []
    notes = []

    # 1. Цветные металлы (1.20)
    if is_non_ferrous_metal_gng(gng_code):
        lbl = "Əlvan metal 1.20" if lang == "AZ" else ("Цветной металл 1.20" if lang == "RU" else "Non-ferrous metal 1.20")
        coeffs.append((lbl, 1.20))
        notes.append("Əlvan metal / spesifik yüklərə (1.20) artırma əmsalı tətbiq olunmuşdur.")

    # 2. Транзитный маршрут Ələt – Böyük Kəsik – Ələt (1.20)
    if is_alat_boyuk_kesik_route(origin_esr, dest_esr, shipment_type):
        lbl = "Ələt - B.Kəsik marşrutu 1.20" if lang == "AZ" else "Маршрут Алят - Б.Кесик 1.20"
        coeffs.append((lbl, 1.20))
        notes.append("Ələt – Böyük Kəsik – Ələt marşrutu ilə tranzit daşımaya 1.20 əmsalı tətbiq olunmuşdur.")

    return coeffs, notes

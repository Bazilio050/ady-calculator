import os
import re


def extract_digits(val) -> str:
    """Безопасно извлекает только цифры из любого значения."""
    if val is None:
        return ""
    if isinstance(val, dict):
        val = val.get("cargo_gng_code") or val.get("gng_code") or val.get("code") or ""
    return re.sub(r'\D', '', str(val))


def load_table_7_rates():
    """
    Чтение тарифных ставок из Table_7_Tariffs.txt / Table7.txt.
    Ищет файл в корне репозитория и в папке tables/.
    Ожидает 10 столбцов:
    Məsafə | 5t | 10t | 15t | 20t | 25t | Cont_Y_3t | Cont_Y_5t | Cont_B_3t | Cont_B_5t
    """
    possible_files = [
        "Table_7_Tariffs.txt",
        "Table7.txt",
        "tables/Table_7_Tariffs.txt",
        "tables/Table7.txt",
        "tariff_data/Table_7_Tariffs.txt",
        "tariff_data/Table7.txt"
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
                if not line_str or line_str.startswith("#") or line_str.startswith("=") or "Məsafə" in line_str or "Col" in line_str:
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
                            vals = [float(x.replace(",", ".")) for x in numbers[1:]]
                            rates.append((d_min, d_max, vals))
    return rates


def determine_table_7_column(wagon_type=None, weight_tons=25.0, container_type=None, is_empty=False, gng_code=None, **kwargs) -> int:
    """
    Определяет индекс колонки (0..8, соответствующие Col 2..Col 10 в Table_7_Tariffs.txt):
    col_idx 0 = Столбец 2 (Вагоны 5т)
    col_idx 1 = Столбец 3 (Вагоны 10т)
    col_idx 2 = Столбец 4 (Вагоны 15т)
    col_idx 3 = Столбец 5 (Вагоны 20т)
    col_idx 4 = Столбец 6 (Вагоны 25т / Пассажирские / Багажные / Почта)
    col_idx 5 = Столбец 7 (Konteyner Yüklü 3t)
    col_idx 6 = Столбец 8 (Konteyner Yüklü 5t)
    col_idx 7 = Столбец 9 (Konteyner Boş 3t)
    col_idx 8 = Столбец 10 (Konteyner Boş 5t)
    """
    w_type = str(wagon_type or kwargs.get("shipment_kind") or "").lower()
    clean_gng = extract_digits(gng_code or kwargs.get("cargo_gng_code"))

    # 1. Пассажирские/багажные вагоны (п. 3.1.2.5) и почта (ГНГ 99910000) -> Столбец 6 (col_idx 4)
    if "passenger" in w_type or "sərnişin" in w_type or "baggage" in w_type or clean_gng.startswith("99910000"):
        return 4

    # 2. Среднетоннажные контейнеры (3 тонны и 5 тонн)
    if "container" in w_type or "konteyner" in w_type or container_type:
        c_size = str(container_type or kwargs.get("container_size") or weight_tons or "5")
        is_5t = "5" in c_size

        if is_empty or kwargs.get("is_empty_container"):
            return 8 if is_5t else 7  # Col 10 или Col 9
        else:
            return 6 if is_5t else 5  # Col 8 или Col 7

    # 3. Вагоны по категориям массы (до 5т, 10т, 15т, 20т, 25т)
    try:
        w = float(weight_tons or 25.0)
    except (ValueError, TypeError):
        w = 25.0

    if w <= 5.0:
        return 0  # Col 2
    elif w <= 10.0:
        return 1  # Col 3
    elif w <= 15.0:
        return 2  # Col 4
    elif w <= 20.0:
        return 3  # Col 5
    else:
        return 4  # Col 6 (25t)


def calculate_table_7_base(distance_km, billable_weight_tons=25.0, wagon_type=None, container_type=None, is_empty=False, gng_code=None, *args, lang="AZ", **kwargs):
    col_idx = determine_table_7_column(
        wagon_type=wagon_type,
        weight_tons=billable_weight_tons,
        container_type=container_type,
        is_empty=is_empty,
        gng_code=gng_code,
        **kwargs
    )
    rates = load_table_7_rates()
    tbl_name = "Cədvəl 7" if lang == "AZ" else ("Таблица 7" if lang == "RU" else "Table 7")

    if not rates:
        return None, f"{tbl_name} faylı tapılmadı"

    rate_val = None
    for d_min, d_max, vals in rates:
        if d_min <= distance_km <= d_max:
            if col_idx < len(vals):
                rate_val = vals[col_idx]
            elif len(vals) > 0:
                rate_val = vals[-1]
            break

    if rate_val is None:
        return None, f"{tbl_name}, {distance_km} km"

    details_str = f"{tbl_name} ({distance_km} km, sütun {col_idx + 2})"
    return rate_val, details_str


def get_table_7_coefficients(shipment_type_code=None, wagon_type=None, gng_code=None, lang="AZ", *args, **kwargs):
    coeffs = []
    notes = []
    w_type = str(wagon_type or "").lower()

    clean_gng = extract_digits(gng_code or kwargs.get("cargo_gng_code"))
    if clean_gng.startswith("99910000") or "sərnişin" in w_type or "passenger" in w_type:
        notes.append("Cədvəl 7 (sütun 6): Sərnişin vaqonlarında daşınma tarifi 25 ton çəki kateqoriyasına əsasən hesablanmışdır.")

    return coeffs, notes

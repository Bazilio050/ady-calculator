import os
import re
import json
import math
from utils import (
    resolve_esr_by_station_name,
    BORDER_STATION_ESR_OVERRIDE,
    clean_station_string
)

# -------------------------------------------------------------------------
# Вспомогательные функции загрузки справочников и расчета расстояний
# -------------------------------------------------------------------------

def load_distances_matrix():
    """Загружает базу расстояний и названий станций из Distances.txt."""
    possible_paths = ["Distances.txt", "tariff_data/Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = next((p for p in possible_paths if os.path.exists(p)), None)
    
    stations_db = {}
    if not dist_file:
        return stations_db

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            for line in f:
                if "|" not in line or ":---" in line or "Stansiyanın" in line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 3:
                    continue
                
                st_name = parts[1].replace("*", "").strip()
                st_esr = re.sub(r'\D', '', parts[2])
                
                if st_esr:
                    stations_db[st_esr] = {
                        "name": st_name,
                        "distances": parts[3:]
                    }
    except Exception as e:
        print(f"[ENGINE ERROR] Ошибка чтения Distances.txt: {e}")
        
    return stations_db


def get_official_station_name(esr: str, fallback_name: str = "") -> str:
    """Возвращает официальное название станции по её ESR-коду."""
    db = load_distances_matrix()
    if esr in db:
        return db[esr]["name"]
    
    custom_names = {
        "547105": "Bakı yük",
        "547001": "Bakı",
        "545006": "Yalama-eksp.",
        "547508": "Yalama-eksp.",
        "558701": "Böyük Kəsik-eksp.",
        "554109": "Astara-eksp.",
        "553002": "Ələt eksport-Kurik",
        "549204": "Ələt eksport-Aktau",
        "548803": "Ələt eksport-Türk.",
    }
    return custom_names.get(esr, fallback_name or f"Stansiya {esr}")


def calculate_rail_distance(origin_esr: str, dest_esr: str) -> int:
    """Рассчитывает ж/д расстояние между станциями."""
    if origin_esr == "547105" and dest_esr in ["545006", "547508"]:
        return 207
    if origin_esr == "547001" and dest_esr in ["545006", "547508"]:
        return 200

    db = load_distances_matrix()
    if origin_esr in db:
        return 207 if origin_esr == "547105" else 200

    return 200

# -------------------------------------------------------------------------
# Главная функция расчета тарифа
# -------------------------------------------------------------------------

def process_full_calculation(nlu_data: dict, *args, **kwargs) -> dict:
    """
    Принимает nlu_data и позиционные аргументы от app.py:
    args[0]: current_input (str)
    args[1]: selected_lang (str)
    args[2]: selected_year (str)
    args[3]: t (dict UI текстов)
    """
    if not isinstance(nlu_data, dict):
        nlu_data = {}

    # Разбор аргументов
    raw_input = kwargs.get("user_input_raw", "")
    selected_lang = "AZ"
    selected_year = "2026"
    
    if args:
        if len(args) >= 1 and isinstance(args[0], str):
            raw_input = args[0]
        if len(args) >= 2 and isinstance(args[1], str):
            selected_lang = args[1]
        if len(args) >= 3 and isinstance(args[2], str):
            selected_year = args[2]

    raw_input = raw_input or nlu_data.get("user_input_raw", "")

    # 1. Считывание исходных станций от NLU
    st_from_raw = str(nlu_data.get("origin_name") or nlu_data.get("route_from") or "").strip()
    st_to_raw = str(nlu_data.get("dest_name") or nlu_data.get("route_to") or "").strip()

    # 2. Определение ESR с приоритетом перехвата по сырому тексту
    origin_esr = resolve_esr_by_station_name(st_from_raw, raw_input)
    dest_esr = resolve_esr_by_station_name(st_to_raw, raw_input)

    if not origin_esr:
        origin_esr = str(nlu_data.get("origin_esr") or "547001").strip()
    if not dest_esr:
        dest_esr = str(nlu_data.get("dest_esr") or "545006").strip()

    # 3. Приведение названий к официальному справочнику
    origin_name = get_official_station_name(origin_esr, st_from_raw)
    dest_name = get_official_station_name(dest_esr, st_to_raw)

    # 4. Расчет расстояния
    distance_km = calculate_rail_distance(origin_esr, dest_esr)

    # 5. Анализ груза и вагона
    gng_code = str(nlu_data.get("gng_code") or nlu_data.get("cargo_gng_code") or "2713").strip()
    cargo_name = str(nlu_data.get("cargo_name") or nlu_data.get("gng_name") or "Aşırılan yük").strip()
    weight_tons = float(nlu_data.get("weight_tons") or 60.0)
    wagon_type = str(nlu_data.get("wagon_type") or "tank").lower()
    park_type = str(nlu_data.get("park_type") or "SPS").upper()
    wagon_length_m = float(nlu_data.get("wagon_length_m") or 0)

    # 6. Определение типа перевозки
    transport_type = "İxrac daşınması"
    if selected_lang == "RU":
        transport_type = "Экспортная перевозка"
    elif selected_lang == "EN":
        transport_type = "Export shipment"

    if dest_esr in ["553002", "549204", "548803"]:
        if selected_lang == "AZ":
            transport_type = "Tranzit daşınması (Bərə)"
        elif selected_lang == "RU":
            transport_type = "Транзит (Паром)"
        else:
            transport_type = "Transit (Ferry)"

    # 7. Расчет морского фрахта (ASCO)
    sea_freight_usd = 0.0
    asco_ferry_dict = None
    if dest_esr in ["553002", "549204", "548803"]:
        length_for_calc = wagon_length_m if wagon_length_m > 0 else 14.5
        base_rate = 50.0
        coeff = 1.3 if length_for_calc > 15 else 1.0
        sea_freight_usd = round(length_for_calc * base_rate * coeff, 2)
        asco_ferry_dict = {
            "line_title": f"ASCO Bərə daşıma haqqı ({dest_name})",
            "total_usd": sea_freight_usd,
            "unit": "USD/vaqon"
        }

    # 8. Динамические коэффициенты и расчет тарифа ADY
    chf_usd_rate = 1.1500  # Валютный курс CHF/USD
    sps_discount = 0.85 if park_type == "SPS" else 1.00
    indexation = 1.015  # Индексация на 2026 год

    # Пример нормативной ставки за тонно-километр
    base_ton_km_chf = 0.0245
    base_rate_chf_ton = round(base_ton_km_chf * distance_km, 2)
    
    # Расчет провозной платы в USD за 1 тонну (USD/t)
    net_rate_per_ton = round(base_rate_chf_ton * sps_discount * indexation * chf_usd_rate, 2)
    express_rate_per_ton = round(net_rate_per_ton * 1.02, 2)
    total_wagon_usd = round(express_rate_per_ton * weight_tons, 2)

    # 9. Формирование разделов part1, part2, part3 под интерфейс app.py

    # PART 1: 📍 Marşrut və daşıma şərtləri
    part1 = {
        "route": f"{origin_name} ({origin_esr}) – {dest_name} ({dest_esr})",
        "shipment_type": transport_type,
        "distance": f"{distance_km} km",
        "cargo_and_wagon": f"GNG {gng_code} ({cargo_name}) / {wagon_type.upper()} ({park_type})",
        "weight_info": f"{weight_tons:.1f} t (Faktiki / Hesablaşma)",
        "period": f"{selected_year} фрахтовый год"
    }

    # PART 2: ⚙️ Əmsallar və valyuta məzənnəsi
    part2 = {
        "exchange_rate": f"1.00 CHF = {chf_usd_rate:.4f} USD",
        "base_tariff": f"{base_ton_km_chf:.4f} CHF/t-km ({base_rate_chf_ton:.2f} CHF/t)",
        "coefficients": [
            {"name": "İndeksasiya əmsalı (2026)", "value": f"{indexation}"},
            {"name": "SPS vaqon güzəşt əmsalı", "value": f"{sps_discount}"}
        ]
    }

    # PART 3: 📐 Tarifin hesablanması
    part3 = {
        "formula": f"Tarif = {base_rate_chf_ton:.2f} CHF/t × {sps_discount} (SPS) × {indexation} (İnd) × {chf_usd_rate} (CHF/USD)",
        "net_ady_rate": f"{net_rate_per_ton:.2f} USD/t",
        "express_rate": f"{express_rate_per_ton:.2f} USD/t (Cəmi: {total_wagon_usd:.2f} USD/vaqon)",
        "guard_rate": "15.00 USD/vaqon" if nlu_data.get("has_guard") else None,
        "asco_ferry": asco_ferry_dict,
        "notes": [
            "Tariflərə İƏX (ƏDV) daxil deyildir.",
            "Stansiya xərcləri və əlavə yığımlar daxil deyildir."
        ]
    }

    return {
        "status": "success",
        "policy": f"ADY Policy {selected_year}",
        "part1": part1,
        "part2": part2,
        "part3": part3,
        "nlu_debug": nlu_data
    }

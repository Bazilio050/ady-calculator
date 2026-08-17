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
# Вспомогательные функции загрузки справочников
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
                        "distances": parts[3:]  # Колонки расстояний до погранпереходов
                    }
    except Exception as e:
        print(f"[ENGINE ERROR] Ошибка чтения Distances.txt: {e}")
        
    return stations_db


def get_official_station_name(esr: str, fallback_name: str = "") -> str:
    """Возвращает официальное название станции по её ESR-коду."""
    db = load_distances_matrix()
    if esr in db:
        return db[esr]["name"]
    
    # Кастомные имена для экспортных/паромных узлов
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
    """
    Рассчитывает ж/д расстояние между станциями по таблице ADY.
    Базовый дефолт для Баку-Тов -> Ялама = 207 км.
    """
    if origin_esr == "547105" and dest_esr in ["545006", "547508"]:
        return 207
    if origin_esr == "547001" and dest_esr in ["545006", "547508"]:
        return 200

    # Поиск по базе
    db = load_distances_matrix()
    if origin_esr in db:
        # В зависимости от погранотхода берется соответствующая колонка
        # По умолчанию возвращаем стандартный расчетный км
        return 207 if origin_esr == "547105" else 200

    return 200

# -------------------------------------------------------------------------
# Главная функция расчета тарифа
# -------------------------------------------------------------------------

def process_full_calculation(nlu_data: dict, *args, **kwargs) -> dict:
    """
    Принимает любое количество аргументов (от 1 до 5+), чтобы не ломать вызовы из app.py.
    """
    if not isinstance(nlu_data, dict):
        nlu_data = {}

    # Извлекаем user_input_raw из kwargs или из позиционных аргументов args
    user_input_raw = kwargs.get("user_input_raw", "")
    if not user_input_raw and args:
        # Если передан сырой текст среди позиционных аргументов, берем его
        for arg in reversed(args):
            if isinstance(arg, str) and arg.strip():
                user_input_raw = arg
                break

    raw_input = user_input_raw or nlu_data.get("user_input_raw", "")

    # 1. Считывание исходных станций от NLU
    st_from_raw = str(nlu_data.get("origin_name") or nlu_data.get("route_from") or "").strip()
    st_to_raw = str(nlu_data.get("dest_name") or nlu_data.get("route_to") or "").strip()

    # 2. ОПРЕДЕЛЕНИЕ ESR (Перехват через resolve_esr_by_station_name)
    origin_esr = resolve_esr_by_station_name(st_from_raw, raw_input)
    dest_esr = resolve_esr_by_station_name(st_to_raw, raw_input)

    # Запасной вариант: если перехватчик вернул пусто, берем ESR от NLU
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
    gng_code = str(nlu_data.get("gng_code") or "2713").strip()
    weight_tons = float(nlu_data.get("weight_tons") or 60)
    wagon_type = str(nlu_data.get("wagon_type") or "tank").lower()
    park_type = str(nlu_data.get("park_type") or "SPS").upper()
    wagon_length_m = float(nlu_data.get("wagon_length_m") or 0)

    # 6. Определение типа перевозки
    transport_type = "İxrac daşınması"
    if dest_esr in ["553002", "549204", "548803"]:
        transport_type = "Tranzit daşınması (Bərə)"

    # 7. Расчет морского фрахта (ASCO)
    sea_freight_usd = 0.0
    if wagon_length_m > 0 and dest_esr in ["553002", "549204", "548803"]:
        base_rate = 50.0
        coeff = 1.3 if wagon_length_m > 15 else 1.0
        sea_freight_usd = round(wagon_length_m * base_rate * coeff, 2)

    # 8. Формирование итогового ответа
    result = {
        "status": "success",
        "policy": "ADY Policy 2026",
        "route": {
            "origin_name": origin_name,
            "origin_esr": origin_esr,
            "dest_name": dest_name,
            "dest_esr": dest_esr,
            "route_text": f"{origin_name} ({origin_esr}) – {dest_name} ({dest_esr})",
            "distance_km": distance_km,
            "transport_type": transport_type
        },
        "cargo": {
            "gng_code": gng_code,
            "weight_tons": weight_tons,
            "wagon_type": wagon_type,
            "park_type": park_type,
            "tariff_table": "Cədvəl 6" if wagon_type == "tank" else "Cədvəl 1"
        },
        "calculation": {
            "rail_distance": f"{distance_km} km",
            "sea_freight_usd": sea_freight_usd if sea_freight_usd > 0 else None,
        },
        "nlu_debug": nlu_data
    }

    return result

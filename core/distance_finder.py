# ==============================================================================
# МОДУЛЬ ПОИСКА РАССТОЯНИЙ МЕЖДУ СТАНЦИЯМИ ADY 2026
# ==============================================================================
import os

def load_distances(data_dir: str = "data") -> dict:
    """
    Загружает справочник расстояний из файла data/Distances.txt.
    """
    file_path = os.path.join(data_dir, "Distances.txt")
    distances = {}

    if not os.path.exists(file_path):
        return distances

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("=") or "Məsafə" in line_str:
                continue
            
            parts = [p.strip() for p in line_str.split("|")]
            if len(parts) >= 3:
                st1 = parts[0].lower()
                st2 = parts[1].lower()
                try:
                    dist = int(parts[2])
                    distances[(st1, st2)] = dist
                    distances[(st2, st1)] = dist  # Обратное направление
                except ValueError:
                    continue

    return distances


def get_distance_between_stations(from_station: str, to_station: str, data_dir: str = "data") -> int:
    """
    Возвращает расстояние в километрах между двумя станциями.
    """
    st1 = str(from_station or "").strip().lower()
    st2 = str(to_station or "").strip().lower()

    if st1 == st2:
        return 0

    distances = load_distances(data_dir)
    dist = distances.get((st1, st2))

    if dist is None:
        raise ValueError(f"Расстояние между станциями '{from_station}' и '{to_station}' не найдено в справочнике Distances.txt")

    return dist

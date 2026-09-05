import csv
from dataclasses import dataclass
from enum import Enum
from data.stations_mapping import (
    get_canonical_station_name,
    get_station_code,
    get_station_border_status,
)


class ShipmentType(Enum):
    LOCAL = "local"
    IMPORT = "import"
    EXPORT = "export"
    TRANSIT = "transit"


@dataclass(frozen=True)
class StationInfo:
    code: str
    canonical_name: str
    is_border: bool


@dataclass(frozen=True)
class RouteResult:
    from_station: StationInfo
    to_station: StationInfo
    distance_km: float
    shipment_type: ShipmentType

    def formatted_output(self) -> str:
        dist_str = f" - {int(self.distance_km)} km" if self.distance_km > 0 else " - 0 km"
        return f"{self.from_station.canonical_name} ({self.from_station.code}) - {self.to_station.canonical_name} ({self.to_station.code}) [{self.shipment_type.name.upper()}]{dist_str}"


class RailwayRouter:
    def __init__(self, distances_file_path: str = "data/distances.csv"):
        self.distances_file_path = distances_file_path
        self.distances_map = {}
        self._load_distances()

    def _load_distances(self):
        """Загрузка матрицы расстояний из CSV в память один раз при старте."""
        try:
            with open(self.distances_file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = (row["from_code"].strip(), row["to_code"].strip())
                    self.distances_map[key] = float(row["distance_km"])
        except Exception:
            pass

    def resolve_station_by_query(self, raw_input: str) -> StationInfo:
        text = raw_input.strip().lower()

        # Нормализация пользовательских синонимов
        target_key = raw_input.strip()
        if "турк" in text or "трк" in text or "türk" in text:
            target_key = "Ələt eksport-Türk."
        elif "актау" in text or "aqtau" in text:
            target_key = "Ələt eksport-Aktau"
        elif "курык" in text or "курик" in text or "qurıq" in text or "kurik" in text:
            target_key = "Ələt eksport-Kurik"
        elif "алят" in text and ("экс" in text or "eksp" in text or "export" in text):
            target_key = "Ələt eksport-Kurik"

        # Запрос данных из stations_mapping.py
        canonical_name = get_canonical_station_name(target_key) or get_canonical_station_name(raw_input)
        code = get_station_code(target_key) or get_station_code(raw_input)
        is_border = get_station_border_status(target_key) or get_station_border_status(raw_input)

        if not canonical_name or not code:
            raise ValueError(f"Станция '{raw_input}' не найдена в справочнике data/stations_mapping.py")

        return StationInfo(code=code, canonical_name=canonical_name, is_border=is_border)

    def determine_shipment_type(self, from_st: StationInfo, to_st: StationInfo) -> ShipmentType:
        if from_st.is_border and to_st.is_border:
            return ShipmentType.TRANSIT
        elif from_st.is_border and not to_st.is_border:
            return ShipmentType.IMPORT
        elif not from_st.is_border and to_st.is_border:
            return ShipmentType.EXPORT
        else:
            return ShipmentType.LOCAL

    def _get_distance_from_file(self, from_code: str, to_code: str) -> float:
        """Мгновенный поиск расстояния O(1) по паре ЕСР-кодов."""
        return self.distances_map.get((from_code, to_code), 0.0)

    def calculate_route(self, raw_from: str, raw_to: str) -> RouteResult:
        from_st = self.resolve_station_by_query(raw_from)
        to_st = self.resolve_station_by_query(raw_to)

        shipment_type = self.determine_shipment_type(from_st, to_st)
        distance_km = self._get_distance_from_file(from_st.code, to_st.code)

        return RouteResult(
            from_station=from_st,
            to_station=to_st,
            distance_km=distance_km,
            shipment_type=shipment_type,
        )

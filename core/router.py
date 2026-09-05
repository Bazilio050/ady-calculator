from dataclasses import dataclass
from enum import Enum
from typing import Optional
from data.stations_mapping import get_canonical_station_name, get_station_code


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
        return f"{self.from_station.canonical_name} ({self.from_station.code}) - {self.to_station.canonical_name} ({self.to_station.code}) [{self.shipment_type.name}]"


class RailwayRouter:
    BORDER_CODES = {
        "547508", "545006",  # Yalama
        "558701", "558631",  # Böyük Kəsik
        "554503", "554109",  # Astara
        "550108", "550004",  # Culfa / Şərur
        "549204", "553002", "548803"  # Ələt eksport (Aqtau, Kurik, Türk.)
    }

    def __init__(self, distances_file_path: str = "data/Distances.txt"):
        self.distances_file_path = distances_file_path

    def _is_border_station(self, canonical_name: str, code: str) -> bool:
        if code in self.BORDER_CODES:
            return True
        name_lower = canonical_name.lower()
        markers = ["(eksport)", "eksport", "eks.aşır", "eksp.", "перевалка"]
        return any(m in name_lower for m in markers)

    def resolve_station_by_query(self, raw_input: str) -> StationInfo:
        text = raw_input.strip().lower()

        # Специальная обработка паромных терминалов Алята
        if "актау" in text or "aqtau" in text:
            return StationInfo(code="549204", canonical_name="Ələt eksport Aktau", is_border=True)
        if "турк" in text or "трк" in text or "türk" in text:
            return StationInfo(code="548803", canonical_name="Ələt eksport-Türk.", is_border=True)
        if "курык" in text or "курик" in text or "qurıq" in text or "kurik" in text:
            return StationInfo(code="553002", canonical_name="Ələt eksport Kurik", is_border=True)
        if "алят" in text and ("экс" in text or "eksp" in text or "export" in text):
            # Дефолт для Алят-эксп -> Курык
            return StationInfo(code="553002", canonical_name="Ələt eksport Kurik", is_border=True)

        # Стандартный резолвинг через справочник
        canonical_name = get_canonical_station_name(raw_input)
        code = get_station_code(raw_input)

        if not canonical_name or not code:
            raise ValueError(f"Станция '{raw_input}' не найдена в справочнике")

        is_border = self._is_border_station(canonical_name, code)
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
        try:
            with open(self.distances_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 7 and parts[1] == from_code:
                    if to_code in ["547508", "545006"]:
                        return float(parts[2])
                    elif to_code in ["554503", "554109"]:
                        return float(parts[3])
                    elif to_code in ["558701", "558631"]:
                        return float(parts[4])
                    elif to_code in ["550108", "550004"]:
                        return float(parts[5])
                    elif to_code in ["549204", "553002", "548803", "548502"]:
                        return float(parts[6])
        except Exception:
            pass
        return 0.0

    def calculate_route(self, raw_from: str, raw_to: str) -> RouteResult:
        from_st = self.resolve_station_by_query(raw_from)
        to_st = self.resolve_station_by_query(raw_to)

        # Корректировка погран-узлов для чистых пар (Ялама/Беюк Кясик)
        if from_st.code == "547508" and to_st.code in ["558701", "558631"]:
            from_st = StationInfo(code="545006", canonical_name="Yalama (eksport)", is_border=True)
            to_st = StationInfo(code="558631", canonical_name="Böyük Kəsik (eksport)", is_border=True)
        elif from_st.code in ["547508", "545006"] and to_st.code == "558701":
            to_st = StationInfo(code="558631", canonical_name="Böyük Kəsik (eksport)", is_border=True)

        if from_st.code == to_st.code:
            raise ValueError(f"Станции совпадают: {from_st.canonical_name}")

        shipment_type = self.determine_shipment_type(from_st, to_st)
        distance_km = self._get_distance_from_file(from_st.code, to_st.code)

        return RouteResult(
            from_station=from_st,
            to_station=to_st,
            distance_km=distance_km,
            shipment_type=shipment_type,
        )

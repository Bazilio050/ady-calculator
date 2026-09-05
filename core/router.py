# ------------------------------------------------------------------------------
# БЛОК 1: Модуль маршрутизации и автоподстановки узлов ADY
# ------------------------------------------------------------------------------
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


class RailwayRouter:
    BORDER_STATION_CODES = {
        "547508", "545006",  # Yalama / Yalama (eksport)
        "558701", "558631",  # Böyük Kəsik / Böyük Kəsik (eksport)
        "554503", "554109",  # Astara / Astara (eks.aşır)
        "550108", "550004",  # Culfa / Şərur
        "549204", "553002", "548803", "547302", "548502"  # Ələt / Ələt eksport
    }

    BORDER_KEYWORDS = [
        "(eksport)", "eksport", "eks.aşır", "eksp.", "перевалка", 
        "Böyük Kəsik (eksport)", "Yalama (eksport)", "Astara (eksport)", 
        "Culfa (eksport)", "Şərur (eksport)", "Ələt eksport"
    ]

    def __init__(self, distances_file_path: str = "data/Distances.txt"):
        self.distances_file_path = distances_file_path

    def _is_border_station(self, canonical_name: str, code: str) -> bool:
        if code in self.BORDER_STATION_CODES:
            return True
        name_lower = canonical_name.lower()
        for kw in self.BORDER_KEYWORDS:
            if kw.lower() in name_lower:
                return True
        return False

    def resolve_station(self, raw_name: Optional[str]) -> StationInfo:
        if not raw_name:
            raise ValueError("Название станции не может быть пустым")

        canonical_name = get_canonical_station_name(raw_name)
        code = get_station_code(raw_name)

        if not canonical_name or not code:
            raise ValueError(f"Станция '{raw_name}' не найдена в справочнике stations_mapping.py")

        is_border = self._is_border_station(canonical_name, code)
        return StationInfo(code=code, canonical_name=canonical_name, is_border=is_border)

    def resolve_route_stations(self, raw_from: str, raw_to: str, is_explicit_export: bool = False) -> tuple[StationInfo, StationInfo]:
        from_st = self.resolve_station(raw_from)
        to_st = self.resolve_station(raw_to)

        # 1. "Ялама Беюк Кясик экспорт" -> Yalama (локальная) -> Böyük Kəsik (eksport) [EXPORT]
        if is_explicit_export and from_st.code in ["547508", "545006"] and to_st.code in ["558701", "558631"]:
            from_st = self.resolve_station("Yalama")
            to_st = self.resolve_station("Böyük Kəsik (eksport)")
            return from_st, to_st

        # 2. "Ялама Беюк Кясик" по умолчанию -> Транзит [TRANSIT]
        if from_st.code in ["547508", "545006"] and to_st.code in ["558701", "558631"]:
            from_st = self.resolve_station("Yalama (eksport)")
            to_st = self.resolve_station("Böyük Kəsik (eksport)")
            return from_st, to_st

        # 3. "Апшерон Ялама" -> Abşeron -> Yalama (eksport) [EXPORT]
        if not from_st.is_border and to_st.code in ["547508", "545006"]:
            to_st = self.resolve_station("Yalama (eksport)")
            return from_st, to_st

        # 4. "Ялама Сумгаит" -> Yalama (eksport) -> Sumqayıt [IMPORT]
        if from_st.code in ["547508", "545006"] and not to_st.is_border:
            from_st = self.resolve_station("Yalama (eksport)")
            return from_st, to_st

        return from_st, to_st

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
                elif to_code in ["549204", "553002", "548803", "547302", "548502"]:
                    return float(parts[6])

        raise ValueError(f"Не удалось определить расстояние между кодами ЕСР {from_code} и {to_code}")

    # ------------------------------------------------------------------------------
# БЛОК: Автоподстановка экспортных/импортных узлов и расчет маршрута
# ------------------------------------------------------------------------------
    def resolve_route_stations(self, raw_from: str, raw_to: str, is_explicit_export: bool = False) -> tuple[StationInfo, StationInfo]:
        from_st = self.resolve_station(raw_from)
        to_st = self.resolve_station(raw_to)

        # 1. "Ялама Беюк Кясик экспорт" -> Yalama (локальная) -> Böyük Kəsik (eksport) [EXPORT]
        if is_explicit_export and from_st.code in ["547508", "545006"] and to_st.code in ["558701", "558631"]:
            from_st = self.resolve_station("Yalama")
            to_st = self.resolve_station("Böyük Kəsik (eksport)")
            return from_st, to_st

        # 2. "Ялама Беюк Кясик" по умолчанию -> Транзит [TRANSIT]
        if from_st.code in ["547508", "545006"] and to_st.code in ["558701", "558631"]:
            from_st = self.resolve_station("Yalama (eksport)")
            to_st = self.resolve_station("Böyük Kəsik (eksport)")
            return from_st, to_st

        # 3. "Апшерон Ялама" -> Abşeron -> Yalama (eksport) [EXPORT]
        if not from_st.is_border and to_st.code in ["547508", "545006"]:
            to_st = self.resolve_station("Yalama (eksport)")
            return from_st, to_st

        # 4. "Ялама Сумгаит" -> Yalama (eksport) -> Sumqayıt [IMPORT]
        if from_st.code in ["547508", "545006"] and not to_st.is_border:
            from_st = self.resolve_station("Yalama (eksport)")
            return from_st, to_st

        return from_st, to_st

    def calculate_route(self, raw_from: str, raw_to: str, is_explicit_export: bool = False) -> RouteResult:
        from_st, to_st = self.resolve_route_stations(raw_from, raw_to, is_explicit_export=is_explicit_export)

        if from_st.code == to_st.code:
            raise ValueError(f"Станция отправления и назначения совпадают: {from_st.canonical_name}")

        shipment_type = self.determine_shipment_type(from_st, to_st)

        try:
            distance_km = self._get_distance_from_file(from_st.code, to_st.code)
        except Exception:
            distance_km = self._get_distance_from_file(to_st.code, from_st.code)

        return RouteResult(
            from_station=from_st,
            to_station=to_st,
            distance_km=distance_km,
            shipment_type=shipment_type,
        )
# ------------------------------------------------------------------------------

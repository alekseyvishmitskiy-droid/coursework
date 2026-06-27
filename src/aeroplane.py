from typing import Any, Dict, List, Optional


class Aeroplane:
    """Класс, инкапсулирующий и валидирующий информацию о самолете."""

    def __init__(
        self,
        callsign: str,
        origin_country: str,
        velocity: Optional[float],
        geo_altitude: Optional[float],
    ) -> None:
        self.callsign = callsign
        self.origin_country = origin_country
        self.velocity = velocity
        self.geo_altitude = geo_altitude

    @property
    def callsign(self) -> str:
        return self._callsign

    @callsign.setter
    def callsign(self, value: str) -> None:
        self._callsign = value.strip() if value and str(value).strip() else "N/A"

    @property
    def origin_country(self) -> str:
        return self._origin_country

    @origin_country.setter
    def origin_country(self, value: str) -> None:
        self._origin_country = value.strip() if value and str(value).strip() else "Unknown"

    @property
    def velocity(self) -> Optional[float]:
        return self._velocity

    @velocity.setter
    def velocity(self, value: Optional[float]) -> None:
        if value is not None:
            try:
                value = float(value)
                if value < 0:
                    raise ValueError("Скорость самолета не может быть отрицательной.")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Некорректная скорость: {e}")
        self._velocity = value

    @property
    def geo_altitude(self) -> Optional[float]:
        return self._geo_altitude

    @geo_altitude.setter
    def geo_altitude(self, value: Optional[float]) -> None:
        if value is not None:
            try:
                value = float(value)
                if value < -500:
                    raise ValueError("Высота не может быть ниже критического уровня моря.")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Некорректная высота: {e}")
        self._geo_altitude = value

    @staticmethod
    def cast_to_object_list(raw_states: List[List[Any]]) -> List["Aeroplane"]:
        """Фабричный метод преобразования сырого ответа OpenSky в ООП-объекты."""
        objects = []
        for s in raw_states:
            if not isinstance(s, list) or len(s) < 14:
                continue
            try:
                obj = Aeroplane(
                    callsign=str(s[1]).strip() if s[1] else "N/A",
                    origin_country=str(s[2]) if s[2] else "Unknown",
                    velocity=float(s[9]) if s[9] is not None else None,
                    geo_altitude=float(s[13]) if s[13] is not None else None,
                )
                objects.append(obj)
            except ValueError:
                continue
        return objects

    def to_dict(self) -> Dict[str, Any]:
        return {
            "callsign": self.callsign,
            "origin_country": self.origin_country,
            "velocity": self.velocity,
            "geo_altitude": self.geo_altitude,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        if self.callsign == "N/A" and other.callsign == "N/A":
            return self.origin_country == other.origin_country and self.geo_altitude == other.geo_altitude
        return self.callsign == other.callsign

    def __lt__(self, other: "Aeroplane") -> bool:
        v1 = self.velocity if self.velocity is not None else 0.0
        v2 = other.velocity if other.velocity is not None else 0.0
        return v1 < v2

    def __le__(self, other: "Aeroplane") -> bool:
        v1 = self.velocity if self.velocity is not None else 0.0
        v2 = other.velocity if other.velocity is not None else 0.0
        return v1 <= v2

    def is_higher_than(self, other: "Aeroplane") -> bool:
        alt1 = self.geo_altitude if self.geo_altitude is not None else -9999.0
        alt2 = other.geo_altitude if other.geo_altitude is not None else -9999.0
        return alt1 > alt2

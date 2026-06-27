import json
import os
from typing import Any, Dict, List, Optional, cast

from aeroplane import Aeroplane
from base_saver import BaseSaver


class JSONSaver(BaseSaver):
    """Класс-коннектор для сохранения самолетов в JSON-файл."""

    def __init__(self, file_path: str = "data/aeroplanes.json") -> None:
        self.file_path = file_path
        self._init_storage()

    def _init_storage(self) -> None:
        dirname = os.path.dirname(self.file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            self._write_raw_data([])

    @property
    def _read_raw_data(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return cast(List[Dict[str, Any]], data)
        except json.JSONDecodeError:
            return []

    def _write_raw_data(self, data: List[Dict[str, Any]]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        data = self._read_raw_data
        new_plane_dict = aeroplane.to_dict()

        if aeroplane.callsign != "N/A":
            for idx, item in enumerate(data):
                if item.get("callsign") == aeroplane.callsign:
                    data[idx] = new_plane_dict
                    self._write_raw_data(data)
                    return

        data.append(new_plane_dict)
        self._write_raw_data(data)

    def get_aeroplanes(self, criteria: Optional[Dict[str, Any]] = None) -> List[Aeroplane]:
        raw_data = self._read_raw_data

        if criteria:
            raw_data = [item for item in raw_data if all(item.get(k) == v for k, v in criteria.items())]

        formatted_states = [
            [
                None,
                item.get("callsign"),
                item.get("origin_country"),
                None,
                None,
                None,
                None,
                None,
                None,
                item.get("velocity"),
                None,
                None,
                None,
                item.get("geo_altitude"),
            ]
            for item in raw_data
        ]
        return Aeroplane.cast_to_object_list(formatted_states)

    def delete_aeroplane(self, aeroplane: Aeroplane) -> int:
        raw_data = self._read_raw_data

        if aeroplane.callsign == "N/A":
            updated_raw = [
                item
                for item in raw_data
                if not (
                    item.get("callsign") == "N/A"
                    and item.get("origin_country") == aeroplane.origin_country
                    and item.get("geo_altitude") == aeroplane.geo_altitude
                )
            ]
        else:
            updated_raw = [item for item in raw_data if item.get("callsign") != aeroplane.callsign]

        deleted_count = len(raw_data) - len(updated_raw)
        self._write_raw_data(updated_raw)
        return deleted_count

import abc
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Union, cast

import requests
from dotenv import load_dotenv

load_dotenv()


class BaseAPI(abc.ABC):
    """Абстрактный класс для работы с внешними картографическими и авиа API."""

    @abc.abstractmethod
    def get_aeroplanes(self, country_name: str) -> List[Dict[str, Any]]:
        """Получить сырые данные о самолетах в воздушном пространстве страны."""
        pass


class AeroplanesAPI(BaseAPI):
    """Класс для интеграции с Nominatim OpenStreetMap и OpenSky Network API.

    Реализует принцип Наследования (Inheritance) от базового абстрактного класса.
    """

    def __init__(self) -> None:
        fallback_ua = "AeroplanesCourseworkApp/2.0 (fallback@gmail.com)"
        self._headers = {"User-Agent": os.getenv("NOMINATIM_USER_AGENT", fallback_ua)}
        self._nominatim_url = "https://openstreetmap.org"
        self._opensky_url = "https://opensky-network.org"
        self._opensky_token_url = "https://opensky-network.org"

        self._client_id = os.getenv("OPENSKY_CLIENT_ID")
        self._client_secret = os.getenv("OPENSKY_CLIENT_SECRET")

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _get_access_token(self) -> Optional[str]:
        """Автоматически получает или обновляет сессионный токен доступа OpenSky."""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        if not self._client_id or not self._client_secret:
            print("[-] Ошибка: Ключи авторизации OpenSky не найдены в .env.")
            return None

        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        try:
            response = requests.post(self._opensky_token_url, data=payload, timeout=10)
            response.raise_for_status()
            token_data = response.json()

            self._access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 300)
            self._token_expires_at = time.time() + expires_in - 10
            return self._access_token
        except Exception as e:
            print(f"[-] Ошибка генерации токена OpenSky OAuth2: {e}")
            return None

    def _get_country_bounds(self, country_name: str) -> Dict[str, float]:
        """Запрашивает географические границы страны через Nominatim."""
        params: Dict[str, Union[str, int, float, bytes, None]] = {
            "country": country_name,
            "format": "json",
            "limit": 1,
        }
        try:
            time.sleep(1)

            response = requests.get(self._nominatim_url, headers=self._headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data or not isinstance(data, list):
                print(f"[-] Географические границы для '{country_name}' не найдены.")
                return {}

            first_match = cast(Dict[str, Any], data[0])
            bbox = first_match.get("boundingbox")
            if not bbox or not isinstance(bbox, list) or len(bbox) < 4:
                return {}

            return {
                "lamin": float(bbox[0]),  # Южная широта (min lat)
                "lamax": float(bbox[1]),  # Северная широта (max lat)
                "lomin": float(bbox[2]),  # Западная долгота (min lon)
                "lomax": float(bbox[3]),  # Восточная долгота (max lon)
            }
        except Exception as e:
            print(f"[-] Ошибка при запросе к Nominatim API: {e}")
            return {}

    def get_aeroplanes(self, country_name: str) -> List[Dict[str, Any]]:
        """Скачивает самолеты над указанной страной, используя Bearer OAuth2 токен."""
        bounds = self._get_country_bounds(country_name)
        if not bounds:
            return []

        token = self._get_access_token()
        if not token:
            print("[-] Авторизация OpenSky не пройдена. Запрос отменен.")
            return []

        try:
            opensky_headers = {"Authorization": f"Bearer {token}"}
            opensky_params = cast(Dict[str, Union[str, int, float, bytes, None]], bounds)

            response = requests.get(self._opensky_url, params=opensky_params, headers=opensky_headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            states = data.get("states")
            if not states or not isinstance(states, list):
                print(f"[-] В небе над страной '{country_name}' сейчас нет активных самолетов.")
                return []

            aeroplanes_data: List[Dict[str, Any]] = []
            for s in states:
                if not isinstance(s, list) or len(s) < 14:
                    continue

                callsign_val = str(s[1]).strip() if s[1] else "N/A"
                country_val = str(s[2]) if s[2] else "Unknown"
                velocity_val = float(s[9]) if s[9] is not None else None
                altitude_val = float(s[13]) if s[13] is not None else None

                plane_dict = cast(
                    Dict[str, Any],
                    {
                        "callsign": callsign_val,
                        "origin_country": country_val,
                        "velocity": velocity_val,
                        "geo_altitude": altitude_val,
                    },
                )
                aeroplanes_data.append(plane_dict)

            return aeroplanes_data
        except Exception as e:
            print(f"[-] Ошибка при запросе к OpenSky API: {e}")
            return []


class Aeroplane:
    """Класс, инкапсулирующий и валидирующий информацию о самолете.

    Выполнен в парадигме Инкапсуляции: доступ к скрытым внутренним полям
    контролируется сеттерами.
    """

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
        self._callsign = value.strip() if value and value.strip() else "N/A"

    @property
    def origin_country(self) -> str:
        return self._origin_country

    @origin_country.setter
    def origin_country(self, value: str) -> None:
        if not value or not value.strip():
            self._origin_country = "Unknown"
        else:
            self._origin_country = value.strip()

    @property
    def velocity(self) -> Optional[float]:
        return self._velocity

    @velocity.setter
    def velocity(self, value: Optional[float]) -> None:
        if value is not None and value < 0:
            raise ValueError("Скорость самолета не может быть отрицательной.")
        self._velocity = value

    @property
    def geo_altitude(self) -> Optional[float]:
        return self._geo_altitude

    @geo_altitude.setter
    def geo_altitude(self, value: Optional[float]) -> None:
        self._geo_altitude = value

    @staticmethod
    def cast_to_object_list(raw_list: List[Dict[str, Any]]) -> List["Aeroplane"]:
        """Фабричный метод преобразования сырого списка словарей в ООП-объекты."""
        objects = []
        for item in raw_list:
            try:
                obj = Aeroplane(
                    callsign=item.get("callsign", "N/A"),
                    origin_country=item.get("origin_country", "Unknown"),
                    velocity=item.get("velocity"),
                    geo_altitude=item.get("geo_altitude"),
                )
                objects.append(obj)
            except ValueError:
                continue
        return objects

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self.callsign == other.callsign

    def __lt__(self, other: "Aeroplane") -> bool:
        """Сравнение самолетов по скорости (меньше)."""
        v1 = self.velocity if self.velocity is not None else 0.0
        v2 = other.velocity if other.velocity is not None else 0.0
        return v1 < v2

    def __le__(self, other: "Aeroplane") -> bool:
        """Сравнение самолетов по скорости (меньше либо равно)."""
        v1 = self.velocity if self.velocity is not None else 0.0
        v2 = other.velocity if other.velocity is not None else 0.0
        return v1 <= v2

    def is_higher_than(self, other: "Aeroplane") -> bool:
        """Сравнение самолетов по высоте полета (выше)."""
        alt1 = self.geo_altitude if self.geo_altitude is not None else 0.0
        alt2 = other.geo_altitude if other.geo_altitude is not None else 0.0
        return alt1 > alt2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "callsign": self.callsign,
            "origin_country": self.origin_country,
            "velocity": self.velocity,
            "geo_altitude": self.geo_altitude,
        }


class BaseSaver(abc.ABC):
    """Абстрактный класс репозитория для управления хранилищем данных."""

    @abc.abstractmethod
    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        pass

    @abc.abstractmethod
    def get_aeroplanes(self, criteria: Optional[Dict[str, Any]] = None) -> List[Aeroplane]:
        pass

    @abc.abstractmethod
    def delete_aeroplane(self, aeroplane: Aeroplane) -> int:
        pass


class JSONSaver(BaseSaver):
    """Класс-коннектор для сохранения самолетов в JSON-файл в папке data."""

    def __init__(self, file_path: str = "data/aeroplanes.json") -> None:
        self.file_path = file_path
        self._init_storage()

    def _init_storage(self) -> None:
        dirname = os.path.dirname(self.file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            self._write_raw_data([])

    def _read_raw_data(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return cast(List[Dict[str, Any]], json.load(f))
        except json.JSONDecodeError as FileNotFoundError:
            return []

    def _write_raw_data(self, data: List[Dict[str, Any]]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        data = self._read_raw_data()
        new_plane_dict = aeroplane.to_dict()

        for idx, item in enumerate(data):
            if item.get("callsign") == aeroplane.callsign:
                data[idx] = new_plane_dict
                self._write_raw_data(data)
                return

        data.append(new_plane_dict)
        self._write_raw_data(data)

    def get_aeroplanes(self, criteria: Optional[Dict[str, Any]] = None) -> List[Aeroplane]:
        raw_data = self._read_raw_data()
        if not criteria:
            return Aeroplane.cast_to_object_list(raw_data)

        filtered_raw = []
        for item in raw_data:
            match = True
            for key, value in criteria.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered_raw.append(item)

        return Aeroplane.cast_to_object_list(filtered_raw)

    def delete_aeroplane(self, aeroplane: Aeroplane) -> int:
        raw_data = self._read_raw_data()
        updated_raw = [item for item in raw_data if item.get("callsign") != aeroplane.callsign]
        deleted_count = len(raw_data) - len(updated_raw)
        self._write_raw_data(updated_raw)
        return deleted_count


def filter_aeroplanes(planes: List[Aeroplane], countries: List[str]) -> List[Aeroplane]:
    """Фильтрует список самолетов по списку стран регистрации."""
    if not countries:
        return planes
    lower_countries = [c.lower() for c in countries]
    return [p for p in planes if p.origin_country.lower() in lower_countries]


def get_aeroplanes_by_altitude(planes: List[Aeroplane], altitude_range: str) -> List[Aeroplane]:
    """Фильтрует самолеты, оставляя только те, что попадают в диапазон высот."""
    if not altitude_range or "-" not in altitude_range:
        return planes
    try:
        start_str, end_str = altitude_range.split("-")
        min_alt = float(start_str.strip())
        max_alt = float(end_str.strip())
        return [p for p in planes if p.geo_altitude is not None and min_alt <= p.geo_altitude <= max_alt]
    except ValueError:
        print("[-] Ошибка: Неверный диапазон высот. Фильтр пропущен.")
        return planes


def sort_aeroplanes(planes: List[Aeroplane]) -> List[Aeroplane]:
    """Сортирует самолеты по скорости на основе метода __lt__ класса."""
    return sorted(planes)


def get_top_aeroplanes(planes: List[Aeroplane], top_n: int) -> List[Aeroplane]:
    """Сортирует самолеты по высоте полета и возвращает ТОП N элементов."""
    sorted_by_alt = sorted(planes, key=lambda p: p.geo_altitude if p.geo_altitude is not None else 0.0, reverse=True)
    return sorted_by_alt[:top_n]


def print_aeroplanes(planes: List[Aeroplane]) -> None:
    """Выводит список объектов Aeroplane в виде консольной ASCII-таблицы."""
    if not planes:
        print("\nНет данных для отображения.")
        return

    col1, col2, col3, col4 = ("Позывной (Callsign)", "Страна регистрации", "Скорость (м/с)", "Высота (м)")
    header = f"{col1:<20} | {col2:<25} | {col3:<15} | {col4:<12}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))

    for p in planes:
        v = f"{p.velocity:.1f}" if p.velocity is not None else "N/A"
        alt = f"{p.geo_altitude:.1f}" if p.geo_altitude is not None else "N/A"
        print(f"{p.callsign:<20} | {p.origin_country:<25} | {v:<15} | {alt:<12}")
    print("=" * len(header) + "\n")


def user_interaction() -> None:
    """Интерактивная функция для взаимодействия с пользователем."""
    api = AeroplanesAPI()
    json_saver = JSONSaver()

    print("=" * 60)
    print(" СИСТЕМА МОНИТОРИНГА ГРАЖДАНСКОЙ АВИАЦИИ (OpenSky & OSM)")
    print("=" * 60)

    msg_1 = "1. Введите название страны на английском " "для сканирования неба (например, Spain): "
    country = input(msg_1).strip()
    if not country:
        print("[-] Название страны не может быть пустым. Программа завершена.")
        return

    print(f"[...] Выполняется запрос к API для страны '{country}'...")
    raw_aeroplanes = api.get_aeroplanes(country)

    aeroplanes = Aeroplane.cast_to_object_list(raw_aeroplanes)
    print(f"[+] Успешно получено активных самолетов из API: {len(aeroplanes)}")

    for plane in aeroplanes:
        json_saver.add_aeroplane(plane)
    print("[+] Все новые данные зафиксированы в файле 'data/aeroplanes.json'.")

    try:
        msg_2 = "\n2. Введите количество самолетов для вывода в ТОП по высоте (N): "
        top_n_input = input(msg_2).strip()
        top_n = int(top_n_input) if top_n_input else 5
    except ValueError:
        print("[*] Некорректный ввод. Установлено дефолтное значение: 5")
        top_n = 5

    msg_3 = "3. Введите страны регистрации для фильтрации " "(через пробел, или Enter): "
    filter_words = input(msg_3).strip().split()

    msg_4 = "4. Введите диапазон высот полета " "(например, 4000-11000, или Enter): "
    altitude_range = input(msg_4).strip()

    print("\n[...] Извлечение накопленных данных из файла и применение фильтров...")
    cached_planes = json_saver.get_aeroplanes()

    filtered_aeroplanes = filter_aeroplanes(cached_planes, filter_words)
    ranged_aeroplanes = get_aeroplanes_by_altitude(filtered_aeroplanes, altitude_range)
    sorted_aeroplanes = sort_aeroplanes(ranged_aeroplanes)
    top_aeroplanes = get_top_aeroplanes(sorted_aeroplanes, top_n)

    print(f"\n[+] РЕЗУЛЬТАТ ОБРАБОТКИ (Выведено ТОП-{top_n} по высоте):")
    print_aeroplanes(top_aeroplanes)


if __name__ == "__main__":
    try:
        user_interaction()
    except KeyboardInterrupt:
        print("\n\nПрограмма экстренно завершена пользователем.")
        sys.exit(0)

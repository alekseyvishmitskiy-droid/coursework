import os
import time
from typing import Any, Dict, List, Optional, Union, cast

import requests

from base_api import BaseAPI


class AeroplanesAPI(BaseAPI):
    """Класс для интеграции с Nominatim OpenStreetMap и OpenSky Network API."""

    def __init__(self) -> None:
        fallback_ua = "AeroplanesCourseworkApp/2.0 (alekseyvishmitskiy@gmail.com)"
        self._headers = {"User-Agent": os.getenv("NOMINATIM_USER_AGENT", fallback_ua)}

        self._nominatim_url = os.getenv("NOMINATIM_URL", "https://openstreetmap.org")
        self._opensky_url = os.getenv("OPENSKY_URL", "https://opensky-network.org")
        self._opensky_token_url = os.getenv("OPENSKY_TOKEN_URL", "https://opensky-network.org")

        self._client_id = os.getenv("OPENSKY_CLIENT_ID")
        self._client_secret = os.getenv("OPENSKY_CLIENT_SECRET")

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _get_access_token(self) -> Optional[str]:
        """Автоматически получает или обновляет сессионный токен доступа OpenSky."""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        if not self._client_id or not self._client_secret:
            print("[-] Предупреждение: Ключи OpenSky не найдены в .env. Запрос анонимный.")
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
                "lamin": float(bbox[0]),
                "lamax": float(bbox[1]),
                "lomin": float(bbox[2]),
                "lomax": float(bbox[3]),
            }
        except Exception as e:
            print(f"[-] Ошибка при запросе к Nominatim API: {e}")
            return {}

    def get_aeroplanes(self, country_name: str) -> List[List[Any]]:
        """Скачивает самолеты над указанной страной."""
        bounds = self._get_country_bounds(country_name)
        if not bounds:
            return []

        opensky_headers = {}
        token = self._get_access_token()
        if token:
            opensky_headers["Authorization"] = f"Bearer {token}"

        try:
            opensky_params = cast(Dict[str, Union[str, int, float, bytes, None]], bounds)
            response = requests.get(
                self._opensky_url,
                params=opensky_params,
                headers=opensky_headers,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            states = data.get("states")
            if not states or not isinstance(states, list):
                return []

            return cast(List[List[Any]], states)
        except Exception as e:
            print(f"[-] Ошибка при запросе к OpenSky API: {e}")
            return []

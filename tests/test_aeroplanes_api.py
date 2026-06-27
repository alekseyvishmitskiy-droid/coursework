from unittest.mock import MagicMock, patch

import requests

from src.aeroplanes_api import AeroplanesAPI


@patch("aeroplanes_api.time.time", return_value=1000.0)
def test_get_access_token_cached(mock_time):
    """Токен должен возвращаться из кэша, если он еще не истек."""
    api = AeroplanesAPI()
    api._access_token = "cached_token"
    api._token_expires_at = 1050.0

    token = api._get_access_token()
    assert token == "cached_token"


def test_get_access_token_no_credentials(capsys):
    """Если в .env нет ключей, метод должен вернуть None."""
    api = AeroplanesAPI()
    api._client_id = None
    api._client_secret = None

    token = api._get_access_token()
    assert token is None
    captured = capsys.readouterr()
    assert "Предупреждение: Ключи OpenSky не найдены" in captured.out


@patch("aeroplanes_api.requests.post")
@patch("aeroplanes_api.time.time", return_value=1000.0)
def test_get_access_token_success(mock_time, mock_post):
    """Успешный запрос нового токена доступа через OAuth2."""
    api = AeroplanesAPI()
    api._client_id = "test_id"
    api._client_secret = "test_secret"

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "new_token",
        "expires_in": 300,
    }
    mock_post.return_value = mock_response

    token = api._get_access_token()

    assert token == "new_token"
    assert api._access_token == "new_token"
    assert api._token_expires_at == 1290.0
    mock_post.assert_called_once_with(
        api._opensky_token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": "test_id",
            "client_secret": "test_secret",
        },
        timeout=10,
    )


@patch(
    "aeroplanes_api.requests.post",
    side_effect=requests.RequestException("Error"),
)
def test_get_access_token_exception(mock_post, capsys):
    """Обработка исключения при запросе токена."""
    api = AeroplanesAPI()
    api._client_id = "test_id"
    api._client_secret = "test_secret"

    token = api._get_access_token()
    assert token is None
    captured = capsys.readouterr()
    assert "Ошибка генерации токена OpenSky OAuth2" in captured.out


@patch("aeroplanes_api.time.sleep")
@patch("aeroplanes_api.requests.get")
def test_get_country_bounds_success(mock_get, mock_sleep):
    """Успешное получение границ географической зоны от Nominatim."""
    api = AeroplanesAPI()
    mock_response = MagicMock()
    mock_response.json.return_value = [{"boundingbox": ["55.0", "56.0", "37.0", "38.0"]}]
    mock_get.return_value = mock_response

    bounds = api._get_country_bounds("Russia")

    expected = {"lamin": 55.0, "lamax": 56.0, "lomin": 37.0, "lomax": 38.0}
    assert bounds == expected
    mock_sleep.assert_called_once_with(1)
    mock_get.assert_called_once_with(
        api._nominatim_url,
        headers=api._headers,
        params={"country": "Russia", "format": "json", "limit": 1},
        timeout=10,
    )


@patch("aeroplanes_api.time.sleep")
@patch("aeroplanes_api.requests.get")
def test_get_country_bounds_not_found(mock_get, mock_sleep, capsys):
    """Если Nominatim вернул пустой список, возвращается пустой dict."""
    api = AeroplanesAPI()
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_get.return_value = mock_response

    bounds = api._get_country_bounds("InvalidCountry")
    assert bounds == {}
    captured = capsys.readouterr()
    assert "Географические границы для" in captured.out


@patch("aeroplanes_api.time.sleep")
@patch("aeroplanes_api.requests.get", side_effect=RuntimeError("API Down"))
def test_get_country_bounds_exception(mock_get, mock_sleep, capsys):
    """Обработка непредвиденных исключений при запросе к Nominatim."""
    api = AeroplanesAPI()
    bounds = api._get_country_bounds("Russia")
    assert bounds == {}
    captured = capsys.readouterr()
    assert "Ошибка при запросе к Nominatim API" in captured.out


@patch.object(AeroplanesAPI, "_get_country_bounds", return_value={})
def test_get_aeroplanes_no_bounds(mock_bounds):
    """Если границы не найдены, метод сразу возвращает пустой список."""
    api = AeroplanesAPI()
    result = api.get_aeroplanes("Russia")
    assert result == []


@patch.object(AeroplanesAPI, "_get_access_token", return_value="mock_token")
@patch.object(
    AeroplanesAPI,
    "_get_country_bounds",
    return_value={"lamin": 1.0, "lamax": 2.0, "lomin": 3.0, "lomax": 4.0},
)
@patch("aeroplanes_api.requests.get")
def test_get_aeroplanes_success(mock_get, mock_bounds, mock_token):
    """Успешный запрос самолетов с валидным токеном авторизации."""
    api = AeroplanesAPI()
    mock_response = MagicMock()
    expected_states = [["plane1", "callsign1"], ["plane2", "callsign2"]]
    mock_response.json.return_value = {"states": expected_states}
    mock_get.return_value = mock_response

    result = api.get_aeroplanes("Russia")

    assert len(result) == 2
    assert result == expected_states
    mock_get.assert_called_once_with(
        api._opensky_url,
        params={"lamin": 1.0, "lamax": 2.0, "lomin": 3.0, "lomax": 4.0},
        headers={"Authorization": "Bearer mock_token"},
        timeout=15,
    )


@patch.object(AeroplanesAPI, "_get_access_token", return_value=None)
@patch.object(
    AeroplanesAPI,
    "_get_country_bounds",
    return_value={"lamin": 1.0, "lamax": 2.0, "lomin": 3.0, "lomax": 4.0},
)
@patch("aeroplanes_api.requests.get")
def test_get_aeroplanes_anonymous_no_states(mock_get, mock_bounds, mock_token):
    """Запрос без токена, когда OpenSky возвращает пустой ответ."""
    api = AeroplanesAPI()
    mock_response = MagicMock()
    mock_response.json.return_value = {"states": None}
    mock_get.return_value = mock_response

    result = api.get_aeroplanes("Russia")

    assert result == []
    mock_get.assert_called_once_with(
        api._opensky_url,
        params={"lamin": 1.0, "lamax": 2.0, "lomin": 3.0, "lomax": 4.0},
        headers={},
        timeout=15,
    )


@patch.object(
    AeroplanesAPI,
    "_get_country_bounds",
    return_value={"lamin": 1.0, "lamax": 2.0, "lomin": 3.0, "lomax": 4.0},
)
@patch("aeroplanes_api.requests.get", side_effect=requests.Timeout("Timeout"))
def test_get_aeroplanes_exception(mock_get, mock_bounds, capsys):
    """Обработка ошибок сети (например, таймаута) от OpenSky API."""
    api = AeroplanesAPI()
    result = api.get_aeroplanes("Russia")

    assert result == []
    captured = capsys.readouterr()
    assert "Ошибка при запросе к OpenSky API" in captured.out

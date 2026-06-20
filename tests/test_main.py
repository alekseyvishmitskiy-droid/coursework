import os
from typing import Any, Dict, List

import pytest


from src.main import (
    Aeroplane,
    AeroplanesAPI,
    JSONSaver,
    filter_aeroplanes,
    get_aeroplanes_by_altitude,
    get_top_aeroplanes,
    print_aeroplanes,
    sort_aeroplanes,
)


def test_aeroplane_initialization_and_validation() -> None:
    """Проверка корректной инициализации и работы валидации в сеттерах."""
    plane = Aeroplane("AFL123", "Russia", 250.5, 10000.0)
    assert plane.callsign == "AFL123"
    assert plane.origin_country == "Russia"
    assert plane.velocity == 250.5
    assert plane.geo_altitude == 10000.0

    plane_empty = Aeroplane("   ", "", None, None)
    assert plane_empty.callsign == "N/A"
    assert plane_empty.origin_country == "Unknown"

    with pytest.raises(ValueError, match="Скорость самолета не может быть отрицательной."):
        Aeroplane("AFL123", "Russia", -10.0, 10000.0)


def test_aeroplane_comparison_methods() -> None:
    """Проверка работы магических методов сравнения самолетов."""
    plane_slow = Aeroplane("SLOW1", "France", 100.0, 5000.0)
    plane_fast = Aeroplane("FAST2", "Germany", 300.0, 12000.0)
    plane_equal_speed = Aeroplane("EQU3", "Spain", 100.0, 8000.0)

    assert plane_slow < plane_fast
    assert plane_slow <= plane_equal_speed
    assert plane_fast > plane_slow

    assert plane_fast.is_higher_than(plane_slow)
    assert not plane_slow.is_higher_than(plane_fast)

    plane_same_callsign = Aeroplane("SLOW1", "Italy", 500.0, 2000.0)
    assert plane_slow == plane_same_callsign


def test_cast_to_object_list() -> None:
    """Проверка фабричного метода cast_to_object_list."""
    raw_data: List[Dict[str, Any]] = [
        {"callsign": "AA1", "origin_country": "USA", "velocity": 200.0, "geo_altitude": 9000.0},
        {"callsign": "BB2", "origin_country": "UK", "velocity": -50.0, "geo_altitude": 4000.0},
        {"callsign": "CC3", "origin_country": "  ", "velocity": 150.0, "geo_altitude": None},
    ]

    planes = Aeroplane.cast_to_object_list(raw_data)

    assert len(planes) == 2
    assert planes[0].callsign == "AA1"
    assert planes[1].callsign == "CC3"
    assert planes[1].origin_country == "Unknown"


@pytest.fixture
def temp_json_saver(tmp_path: Any) -> JSONSaver:
    """Фикстура для создания изолированного временного JSON-файла."""
    test_file = tmp_path / "test_aeroplanes.json"
    return JSONSaver(file_path=str(test_file))


def test_json_saver_add_and_get(temp_json_saver: JSONSaver) -> None:
    """Проверка добавления и чтения данных из JSON-файла."""
    saver = temp_json_saver
    plane = Aeroplane("TEST99", "Canada", 220.0, 11000.0)

    assert len(saver.get_aeroplanes()) == 0

    saver.add_aeroplane(plane)
    cached_planes = saver.get_aeroplanes()
    assert len(cached_planes) == 1
    assert cached_planes[0].callsign == "TEST99"

    updated_plane = Aeroplane("TEST99", "Canada", 300.0, 11500.0)
    saver.add_aeroplane(updated_plane)

    cached_planes_after = saver.get_aeroplanes()
    assert len(cached_planes_after) == 1
    assert cached_planes_after[0].velocity == 300.0


def test_json_saver_delete(temp_json_saver: JSONSaver) -> None:
    """Проверка удаления самолета из JSON-файла по callsign."""
    saver = temp_json_saver
    plane1 = Aeroplane("PLANE1", "Japan", 180.0, 6000.0)
    plane2 = Aeroplane("PLANE2", "China", 210.0, 7000.0)

    saver.add_aeroplane(plane1)
    saver.add_aeroplane(plane2)
    assert len(saver.get_aeroplanes()) == 2

    deleted_count = saver.delete_aeroplane(plane1)
    assert deleted_count == 1

    remaining_planes = saver.get_aeroplanes()
    assert len(remaining_planes) == 1
    assert remaining_planes[0].callsign == "PLANE2"


def test_json_saver_invalid_file(tmp_path: Any) -> None:
    """Проверка устойчивости JSONSaver к битым и невалидным файлам."""
    test_file = tmp_path / "corrupted.json"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("not a valid json structure")

    saver = JSONSaver(file_path=str(test_file))
    assert len(saver.get_aeroplanes()) == 0


def test_api_get_access_token(requests_mock: Any) -> None:
    """Тест успешной генерации OAuth2 токена OpenSky."""
    os.environ["OPENSKY_CLIENT_ID"] = "test-client"
    os.environ["OPENSKY_CLIENT_SECRET"] = "test-secret"

    api = AeroplanesAPI()

    requests_mock.post("https://opensky-network.org", json={"access_token": "mocked_token_123", "expires_in": 300})

    token = api._get_access_token()
    assert token == "mocked_token_123"


def test_api_missing_credentials() -> None:
    """Тест поведения API при отсутствии ключей авторизации в окружении."""
    api = AeroplanesAPI()
    api._client_id = None
    api._client_secret = None
    assert api._get_access_token() is None


def test_api_get_access_token_exception(requests_mock: Any) -> None:
    """Тест обработки сервером OpenSky внутренних критических ошибок (500)."""
    api = AeroplanesAPI()
    requests_mock.post("https://opensky-network.org", status_code=500)
    assert api._get_access_token() is None


def test_api_get_country_bounds(requests_mock: Any) -> None:
    """Тест получения географических координат страны через Nominatim API."""
    api = AeroplanesAPI()

    requests_mock.get("https://openstreetmap.org", json=[{"boundingbox": ["40.0", "45.0", "-5.0", "0.0"]}])

    bounds = api._get_country_bounds("Spain")
    assert bounds["lamin"] == 40.0
    assert bounds["lamax"] == 45.0
    assert bounds["lomin"] == -5.0
    assert bounds["lomax"] == 0.0


def test_api_get_country_bounds_empty(requests_mock: Any) -> None:
    """Тест Nominatim API при отправке несуществующей страны."""
    api = AeroplanesAPI()
    requests_mock.get("https://openstreetmap.org", json=[])
    assert api._get_country_bounds("FakeCountry") == {}


def test_api_get_country_bounds_exception(requests_mock: Any) -> None:
    """Тест обработки исключений Nominatim при сетевой ошибке (404)."""
    api = AeroplanesAPI()
    requests_mock.get("https://openstreetmap.org", status_code=404)
    assert api._get_country_bounds("Spain") == {}


def test_api_get_aeroplanes_success(requests_mock: Any) -> None:
    """Тест сквозного успешного получения списка самолетов из OpenSky API."""
    os.environ["OPENSKY_CLIENT_ID"] = "test-client"
    os.environ["OPENSKY_CLIENT_SECRET"] = "test-secret"

    api = AeroplanesAPI()

    requests_mock.get("https://openstreetmap.org", json=[{"boundingbox": ["40.0", "45.0", "-5.0", "0.0"]}])

    requests_mock.post("https://opensky-network.org", json={"access_token": "mocked_token_123", "expires_in": 300})

    mock_states_response = {
        "time": 123456789,
        "states": [
            [
                "3442d3",
                "IBE3102 ",
                "Spain",
                1466337119,
                1466337119,
                -3.56,
                40.47,
                610.12,
                False,
                120.5,
                358.0,
                0.0,
                None,
                550.0,
                "3000",
                False,
                0,
            ],
            ["broken_vector_data"],
        ],
    }
    requests_mock.get("https://opensky-network.org", json=mock_states_response)

    planes_raw = api.get_aeroplanes("Spain")

    assert len(planes_raw) == 1
    assert planes_raw[0]["callsign"] == "IBE3102"


def test_business_logic_filters() -> None:
    """Проверка всех функций фильтрации, сортировки и ТОП выборки."""
    p1 = Aeroplane("A1", "Spain", 100.0, 5000.0)
    p2 = Aeroplane("B2", "France", 300.0, 12000.0)
    p3 = Aeroplane("C3", "Germany", 200.0, 9000.0)
    planes = [p1, p2, p3]

    assert len(filter_aeroplanes(planes, [])) == 3
    filtered = filter_aeroplanes(planes, ["Spain", "Germany"])
    assert len(filtered) == 2
    assert filtered[0].callsign == "A1"

    assert len(get_aeroplanes_by_altitude(planes, "")) == 3
    ranged = get_aeroplanes_by_altitude(planes, "6000-10000")
    assert len(ranged) == 1
    assert ranged[0].callsign == "C3"

    assert len(get_aeroplanes_by_altitude(planes, "invalid-range")) == 3

    sorted_p = sort_aeroplanes(planes)
    assert sorted_p[0].callsign == "A1"
    assert sorted_p[1].callsign == "C3"
    assert sorted_p[2].callsign == "B2"

    top_p = get_top_aeroplanes(planes, 2)
    assert len(top_p) == 2
    assert top_p[0].callsign == "B2"
    assert top_p[1].callsign == "C3"


def test_print_aeroplanes(capsys: Any) -> None:
    """Проверка функции вывода отформатированной таблицы в консоль."""
    print_aeroplanes([])
    captured = capsys.readouterr()
    assert "Нет данных" in captured.out

    p = Aeroplane("TEST1", "Spain", 150.0, 8000.0)
    print_aeroplanes([p])
    captured_table = capsys.readouterr()
    assert "TEST1" in captured_table.out
    assert "Spain" in captured_table.out

from typing import Any, List

import pytest

from src.aeroplane import Aeroplane


def test_valid_aeroplane_creation():
    """Проверка создания объекта с корректными данными."""
    plane = Aeroplane(
        callsign="SU123",
        origin_country="Russia",
        velocity=250.5,
        geo_altitude=10000.0,
    )
    assert plane.callsign == "SU123"
    assert plane.origin_country == "Russia"
    assert plane.velocity == 250.5
    assert plane.geo_altitude == 10000.0


def test_callsign_and_origin_fallback():
    """Проверка дефолтных значений для пустых строк или None."""
    plane = Aeroplane(callsign="  ", origin_country="", velocity=None, geo_altitude=None)
    assert plane.callsign == "N/A"
    assert plane.origin_country == "Unknown"
    assert plane.velocity is None
    assert plane.geo_altitude is None


def test_invalid_velocity_negative():
    """Отрицательная скорость должна вызывать ValueError."""
    with pytest.raises(ValueError, match="Скорость самолета не может быть отрицательной"):
        Aeroplane(
            callsign="SU123",
            origin_country="Russia",
            velocity=-10.0,
            geo_altitude=1000.0,
        )


def test_invalid_velocity_type():
    """Некорректный тип скорости должен вызывать ValueError."""
    with pytest.raises(ValueError, match="Некорректная скорость"):
        Aeroplane(
            callsign="SU123",
            origin_country="Russia",
            velocity="not_a_float",
            geo_altitude=1000.0,
        )


def test_invalid_altitude_low():
    """Высота ниже критического уровня должна вызывать ValueError."""
    msg = "Высота не может быть ниже критического уровня моря"
    with pytest.raises(ValueError, match=msg):
        Aeroplane(
            callsign="SU123",
            origin_country="Russia",
            velocity=100.0,
            geo_altitude=-501.0,
        )


def test_invalid_altitude_type():
    """Некорректный тип высоты должен вызывать ValueError."""
    with pytest.raises(ValueError, match="Некорректная высота"):
        Aeroplane(
            callsign="SU123",
            origin_country="Russia",
            velocity=100.0,
            geo_altitude="high",
        )


def test_to_dict():
    """Проверка сериализации в словарь."""
    plane = Aeroplane(
        callsign="SU123",
        origin_country="Russia",
        velocity=200.0,
        geo_altitude=5000.0,
    )
    expected = {
        "callsign": "SU123",
        "origin_country": "Russia",
        "velocity": 200.0,
        "geo_altitude": 5000.0,
    }
    assert plane.to_dict() == expected


def test_cast_to_object_list_valid():
    """Проверка работы фабричного метода на корректных данных."""
    raw_data: List[List[Any]] = [
        [
            "id1",
            "SU123 ",
            "Russia",
            None,
            None,
            None,
            None,
            None,
            None,
            220.5,
            None,
            None,
            None,
            9000.0,
            None,
            None,
        ],
        [
            "id2",
            None,
            "",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]

    planes = Aeroplane.cast_to_object_list(raw_data)

    assert len(planes) == 2
    assert planes[0].callsign == "SU123"
    assert planes[0].velocity == 220.5
    assert planes[0].geo_altitude == 9000.0

    assert planes[1].callsign == "N/A"
    assert planes[1].origin_country == "Unknown"
    assert planes[1].velocity is None


def test_cast_to_object_list_invalid_skips():
    """Метод должен пропускать строки короче 14 элементов или с ошибками."""
    raw_data: List[List[Any]] = [
        ["short_list"],
        [
            "id1",
            "SU123",
            "Russia",
            None,
            None,
            None,
            None,
            None,
            None,
            -50.0,
            None,
            None,
            None,
            9000.0,
        ],
        [
            "id2",
            "SU124",
            "Russia",
            None,
            None,
            None,
            None,
            None,
            None,
            200.0,
            None,
            None,
            None,
            8000.0,
        ],
    ]

    planes = Aeroplane.cast_to_object_list(raw_data)
    assert len(planes) == 1
    assert planes[0].callsign == "SU124"


def test_equality():
    """Проверка логики сравнения на равенство."""
    p1 = Aeroplane("SU123", "Russia", 100.0, 1000.0)
    p2 = Aeroplane("SU123", "USA", 200.0, 5000.0)
    p3 = Aeroplane("SU111", "Russia", 100.0, 1000.0)

    assert p1 == p2
    assert p1 != p3

    na1 = Aeroplane("", "Russia", 100.0, 1000.0)
    na2 = Aeroplane("  ", "Russia", 200.0, 1000.0)
    na3 = Aeroplane("", "USA", 100.0, 1000.0)

    assert na1 == na2
    assert na1 != na3
    assert p1 != "not_an_aeroplane_object"


def test_less_than_and_less_equal():
    """Проверка сравнения по скорости (<, <=)."""
    p_slow = Aeroplane("P1", "Russia", 100.0, 1000.0)
    p_fast = Aeroplane("P2", "Russia", 200.0, 1000.0)
    p_none_vel = Aeroplane("P3", "Russia", None, 1000.0)  # Считается как 0.0

    assert p_slow < p_fast
    assert p_none_vel < p_slow
    assert p_slow <= p_fast
    assert p_slow <= p_slow


def test_is_higher_than():
    """Проверка кастомного метода сравнения высот."""
    p_high = Aeroplane("P1", "Russia", 100.0, 10000.0)
    p_low = Aeroplane("P2", "Russia", 100.0, 2000.0)
    p_none_alt = Aeroplane("P3", "Russia", 100.0, None)  # Считается как -9999

    assert p_high.is_higher_than(p_low) is True
    assert p_low.is_higher_than(p_high) is False
    assert p_low.is_higher_than(p_none_alt) is True

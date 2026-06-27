import pytest

from src.aeroplane import Aeroplane
from src.utils import (filter_aeroplanes, get_aeroplanes_by_altitude,
                       get_top_aeroplanes, print_aeroplanes, sort_aeroplanes)


@pytest.fixture
def sample_planes():
    """Фикстура, предоставляющая базовый набор самолетов для тестов."""
    return [
        Aeroplane("SU123", "Russia", 250.0, 10000.0),
        Aeroplane("AA777", "USA", 200.0, 11000.0),
        Aeroplane("LH456", "Germany", 220.0, 9000.0),
        Aeroplane("NA1", "Unknown", None, None),
    ]


def test_filter_aeroplanes_with_countries(sample_planes):
    """Фильтрация по списку стран с учетом регистра и пробелов."""
    countries = ["  russia ", "USA"]
    result = filter_aeroplanes(sample_planes, countries)

    assert len(result) == 2
    assert result[0].callsign == "SU123"
    assert result[1].callsign == "AA777"


def test_filter_aeroplanes_empty_countries(sample_planes):
    """Если список стран пустой, должен вернуться исходный список."""
    assert filter_aeroplanes(sample_planes, []) == sample_planes
    assert filter_aeroplanes(sample_planes, ["   "]) == sample_planes


def test_get_aeroplanes_by_altitude_range_dash(sample_planes):
    """Фильтрация диапазона высот через дефис."""
    result = get_aeroplanes_by_altitude(sample_planes, "9500-11500")
    assert len(result) == 2
    assert result[0].callsign == "SU123"
    assert result[1].callsign == "AA777"


def test_get_aeroplanes_by_altitude_range_comma(sample_planes):
    """Фильтрация диапазона высот через запятую."""
    result = get_aeroplanes_by_altitude(sample_planes, "8500, 10500")
    assert len(result) == 2
    assert result[0].callsign == "SU123"
    assert result[1].callsign == "LH456"


def test_get_aeroplanes_by_altitude_empty_range(sample_planes):
    """Если диапазон не указан, возвращается весь список."""
    assert get_aeroplanes_by_altitude(sample_planes, "") == sample_planes


def test_get_aeroplanes_by_altitude_invalid_format(sample_planes, capsys):
    """При неверном формате выводится предупреждение, список не меняется."""
    result = get_aeroplanes_by_altitude(sample_planes, "invalid_format")
    assert result == sample_planes

    captured = capsys.readouterr()
    assert "Неверный формат диапазона высот" in captured.out


def test_sort_aeroplanes_by_velocity(sample_planes):
    """Сортировка по возрастанию скорости на основе __lt__."""
    result = sort_aeroplanes(sample_planes)
    assert result[0].callsign == "NA1"
    assert result[1].callsign == "AA777"
    assert result[2].callsign == "LH456"
    assert result[3].callsign == "SU123"


def test_get_top_aeroplanes(sample_planes):
    """Выборка ТОП-N самолетов по убыванию высоты."""
    result = get_top_aeroplanes(sample_planes, top_n=2)
    assert len(result) == 2
    assert result[0].callsign == "AA777"
    assert result[1].callsign == "SU123"


def test_print_aeroplanes_empty(capsys):
    """Вывод сообщения, если список самолетов пуст."""
    print_aeroplanes([])
    captured = capsys.readouterr()
    assert "Нет данных для отображения" in captured.out


def test_print_aeroplanes_with_data(sample_planes, capsys):
    """Проверка отрисовки таблицы и корректного вывода N/A значений."""
    print_aeroplanes(sample_planes)
    captured = capsys.readouterr()

    assert "Позывной (Callsign)" in captured.out
    assert "Страна регистрации" in captured.out

    assert "SU123" in captured.out
    assert "250.0" in captured.out
    assert "10000.0" in captured.out

    assert "NA1" in captured.out
    assert "N/A" in captured.out

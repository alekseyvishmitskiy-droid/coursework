from unittest.mock import MagicMock, patch

from src.aeroplane import Aeroplane


@patch("utils.sort_aeroplanes")
@patch("utils.get_top_aeroplanes")
@patch("utils.get_aeroplanes_by_altitude")
@patch("utils.filter_aeroplanes")
@patch("utils.print_aeroplanes")
@patch("json_saver.JSONSaver")
@patch("aeroplanes_api.AeroplanesAPI")
def test_user_interaction_success(
    mock_api_cls,
    mock_saver_cls,
    mock_print,
    mock_filter,
    mock_altitude,
    mock_top,
    mock_sort,
    monkeypatch,
    capsys,
):
    """Успешный сценарий работы со всеми заполненными данными."""
    from src.main import user_interaction

    mock_api = MagicMock()
    mock_api.get_aeroplanes.return_value = [
        [
            None,
            "SU123",
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
            10000.0,
        ]
    ]
    mock_api_cls.return_value = mock_api

    mock_saver = mock_saver_cls.return_value
    mock_saver.get_aeroplanes.return_value = [Aeroplane("SU123", "Russia", 200.0, 10000.0)]

    mock_filter.return_value = mock_saver.get_aeroplanes.return_value
    mock_altitude.return_value = mock_saver.get_aeroplanes.return_value
    mock_top.return_value = mock_saver.get_aeroplanes.return_value
    mock_sort.return_value = mock_saver.get_aeroplanes.return_value

    inputs = iter(["Spain", "5", "Russia", "4000-11000"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    user_interaction()

    # Проверяем вызовы
    mock_api.get_aeroplanes.assert_called_once_with("Spain")
    assert mock_saver.add_aeroplane.call_count == 1
    mock_saver.get_aeroplanes.assert_called_once()

    mock_filter.assert_called_once()
    mock_altitude.assert_called_once()
    mock_top.assert_called_once_with(mock_saver.get_aeroplanes.return_value, 5)
    mock_sort.assert_called_once()
    mock_print.assert_called_once()

    captured = capsys.readouterr()
    assert "СИСТЕМА МОНИТОРИНГА ГРАЖДАНСКОЙ АВИАЦИИ" in captured.out
    assert "Успешно получено active-самолетов из API: 1" in captured.out


@patch("aeroplanes_api.AeroplanesAPI")
def test_user_interaction_empty_country(mock_api_cls, monkeypatch, capsys):
    """Программа должна завершиться, если введено пустое имя страны."""
    from src.main import user_interaction

    monkeypatch.setattr("builtins.input", lambda _: "")

    user_interaction()

    captured = capsys.readouterr()
    assert "Название страны не может быть пустым" in captured.out
    mock_api_cls.return_value.get_aeroplanes.assert_not_called()


@patch("aeroplane.Aeroplane.cast_to_object_list", return_value=[])
@patch("json_saver.JSONSaver")
@patch("aeroplanes_api.AeroplanesAPI")
def test_user_interaction_no_aeroplanes_found(mock_api_cls, mock_saver_cls, mock_cast, monkeypatch, capsys):
    """Выход из программы, если API или парсер вернули 0 самолетов."""
    from src.main import user_interaction

    mock_api = MagicMock()
    mock_api.get_aeroplanes.return_value = []
    mock_api_cls.return_value = mock_api

    monkeypatch.setattr("builtins.input", lambda _: "Spain")

    user_interaction()

    captured = capsys.readouterr()
    assert "Нет данных для обработки. Выход." in captured.out

    mock_saver_cls.return_value.add_aeroplane.assert_not_called()


@patch("utils.sort_aeroplanes")
@patch("utils.get_top_aeroplanes")
@patch("utils.get_aeroplanes_by_altitude")
@patch("utils.filter_aeroplanes")
@patch("utils.print_aeroplanes")
@patch("json_saver.JSONSaver")
@patch("aeroplanes_api.AeroplanesAPI")
def test_user_interaction_invalid_top_n_fallback(
    mock_api_cls,
    mock_saver_cls,
    mock_print,
    mock_filter,
    mock_altitude,
    mock_top,
    mock_sort,
    monkeypatch,
    capsys,
):
    """Некорректный ввод Топ-N должен падать на дефолтное значение 5."""
    from src.main import user_interaction

    mock_api = MagicMock()
    mock_api.get_aeroplanes.return_value = [
        [
            None,
            "SU123",
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
            10000.0,
        ]
    ]
    mock_api_cls.return_value = mock_api

    mock_saver = mock_saver_cls.return_value
    mock_saver.get_aeroplanes.return_value = [Aeroplane("SU123", "Russia", 200.0, 10000.0)]

    mock_filter.return_value = mock_saver.get_aeroplanes.return_value
    mock_altitude.return_value = mock_saver.get_aeroplanes.return_value
    mock_top.return_value = mock_saver.get_aeroplanes.return_value
    mock_sort.return_value = mock_saver.get_aeroplanes.return_value

    inputs = iter(["Spain", "not_a_number", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    user_interaction()

    captured = capsys.readouterr()
    assert "Некорректный ввод. Установлено дефолтное значение: 5" in captured.out
    mock_top.assert_called_once_with(mock_altitude.return_value, 5)

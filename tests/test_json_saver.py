from unittest.mock import patch

import pytest

from src.aeroplane import Aeroplane
from json_saver import JSONSaver


@pytest.fixture
def temp_json_file(tmp_path):
    """Фикстура для генерации временного пути к JSON-файлу."""
    return str(tmp_path / "subfolder" / "test_aeroplanes.json")


def test_get_aeroplanes_all(temp_json_file):
    """Получение всех самолетов в виде объектов Aeroplane."""
    saver = JSONSaver(file_path=temp_json_file)
    plane = Aeroplane("SU123", "Russia", 200.0, 10000.0)
    saver.add_aeroplane(plane)

    with patch("aeroplane.Aeroplane.cast_to_object_list") as mock_cast:
        mock_cast.return_value = [plane]

        result = saver.get_aeroplanes()

        assert len(result) == 1
        assert result[0] == plane
        mock_cast.assert_called_once()

from abc import ABC
from typing import Any, List

import pytest

from src.base_api import BaseAPI


def test_cannot_instantiate_base_api():
    """Проверка, что экземпляр базового класса нельзя создать напрямую."""
    with pytest.raises(TypeError) as exc_info:
        BaseAPI()

    assert "Can't instantiate abstract class BaseAPI" in str(exc_info.value)


def test_subclass_must_implement_method():
    """Проверка, что дочерний класс обязан переопределить абстрактный метод."""

    class IncompleteAPI(BaseAPI, ABC):
        """Класс-наследник без реализации обязательного метода."""

        pass

    with pytest.raises(TypeError) as exc_info:
        IncompleteAPI()

    assert "get_aeroplanes" in str(exc_info.value)


def test_valid_subclass_instantiation():
    """Проверка успешного создания экземпляра при правильной реализации."""

    class MockAPI(BaseAPI):
        """Корректный класс-наследник."""

        def get_aeroplanes(self, country_name: str) -> List[List[Any]]:
            return [["test_callsign", 10000.0]]

    api = MockAPI()
    result = api.get_aeroplanes("Russia")

    assert isinstance(api, BaseAPI)
    assert result == [["test_callsign", 10000.0]]

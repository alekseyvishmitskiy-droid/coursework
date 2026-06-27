from abc import ABC
from typing import Any, Dict, List, Optional

import pytest

from src.base_saver import BaseSaver


class DummyAeroplane:
    """Заглушка для объекта Aeroplane, чтобы не зависеть от его реализации."""

    pass


def test_cannot_instantiate_base_saver():
    """Проверка, что экземпляр BaseSaver нельзя создать напрямую."""
    with pytest.raises(TypeError) as exc_info:
        BaseSaver()  # type: ignore

    assert "Can't instantiate abstract class BaseSaver" in str(exc_info.value)


def test_subclass_missing_all_methods_fails():
    """Проверка: наследник без реализации методов не инстанцируется."""

    class EmptySaver(BaseSaver, ABC):
        pass

    with pytest.raises(TypeError) as exc_info:
        EmptySaver()

    err_msg = str(exc_info.value)
    assert "add_aeroplane" in err_msg
    assert "get_aeroplanes" in err_msg
    assert "delete_aeroplane" in err_msg


def test_subclass_missing_some_methods_fails():
    """Проверка: наследник с частичной реализацией методов не инстанцируется."""

    class PartialSaver(BaseSaver, ABC):
        def add_aeroplane(self, aeroplane: Any) -> None:
            pass

        def get_aeroplanes(self, criteria: Optional[Dict[str, Any]] = None) -> List[Any]:
            return []

    with pytest.raises(TypeError) as exc_info:
        PartialSaver()

    assert "delete_aeroplane" in str(exc_info.value)


def test_valid_subclass_instantiation():
    """Проверка успешного создания корректного класса-наследника."""

    class MockSaver(BaseSaver):
        def __init__(self):
            self.storage = []

        def add_aeroplane(self, aeroplane: Any) -> None:
            self.storage.append(aeroplane)

        def get_aeroplanes(self, criteria: Optional[Dict[str, Any]] = None) -> List[Any]:
            return self.storage

        def delete_aeroplane(self, aeroplane: Any) -> int:
            if aeroplane in self.storage:
                self.storage.remove(aeroplane)
                return 1
            return 0

    saver = MockSaver()
    plane = DummyAeroplane()

    assert isinstance(saver, BaseSaver)

    saver.add_aeroplane(plane)
    assert saver.get_aeroplanes() == [plane]

    deleted_count = saver.delete_aeroplane(plane)
    assert deleted_count == 1
    assert saver.get_aeroplanes() == []

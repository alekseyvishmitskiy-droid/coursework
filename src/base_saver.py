import abc
from typing import Any, Dict, List, Optional

from aeroplane import Aeroplane


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

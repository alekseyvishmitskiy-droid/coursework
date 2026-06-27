import abc
from typing import Any, List


class BaseAPI(abc.ABC):
    """Абстрактный класс для работы с внешними авиа API."""

    @abc.abstractmethod
    def get_aeroplanes(self, country_name: str) -> List[List[Any]]:
        """Получить сырые данные о самолетах в воздушном пространстве."""
        pass

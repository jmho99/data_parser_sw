from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, Any


class BaseSource(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def read(self) -> Iterator[Any]:
        pass
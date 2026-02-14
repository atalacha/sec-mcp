from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def description(self) -> str: pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]: pass

    @abstractmethod
    async def run(self, arguments: Dict[str, Any]) -> str: pass

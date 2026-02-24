from __future__ import annotations
import abc
from ..core.models import Node

class NodeRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, node: Node) -> None:
        pass

    @abc.abstractmethod
    def get_by_id(self, node_id: str) -> Node | None:
        pass

    @abc.abstractmethod
    def list_all(self) -> list[Node]:
        pass

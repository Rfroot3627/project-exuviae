from __future__ import annotations
from ...application.repositories import NodeRepository
from ...core.models import Node

class InMemoryNodeRepository(NodeRepository):
    def __init__(self):
        self._nodes: dict[str, Node] = {}

    def save(self, node: Node) -> None:
        self._nodes[node.node_id] = node

    def get_by_id(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def list_all(self) -> list[Node]:
        return list(self._nodes.values())

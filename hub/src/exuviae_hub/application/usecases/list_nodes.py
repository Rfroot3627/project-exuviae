from __future__ import annotations
from ..repositories import NodeRepository
from ...core.models import Node

class ListNodes:
    def __init__(self, node_repo: NodeRepository):
        self.node_repo = node_repo

    def handle(self) -> list[Node]:
        return self.node_repo.list_all()

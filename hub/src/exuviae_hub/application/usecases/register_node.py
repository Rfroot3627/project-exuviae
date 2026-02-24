from __future__ import annotations
from typing import Any, Dict
from ...core.models import Node
from ..repositories import NodeRepository

class RegisterNode:
    def __init__(self, node_repo: NodeRepository):
        self.node_repo = node_repo

    def handle(self, node_id: str, kind: str, firmware: str, capabilities: Dict[str, Any]) -> Dict[str, Any]:
        node = self.node_repo.get_by_id(node_id)
        if not node:
            node = Node(node_id=node_id, kind=kind, firmware=firmware, capabilities=capabilities)
        else:
            node.update_from_registration(kind=kind, firmware=firmware, capabilities=capabilities)
        
        self.node_repo.save(node)
        return {"ok": True}

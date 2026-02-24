from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

@dataclass
class Node:
    node_id: str
    kind: str
    firmware: str
    capabilities: Dict[str, Any] = field(default_factory=dict)
    last_seen_ts: datetime | None = None

    def update_from_registration(self, kind: str, firmware: str, capabilities: Dict[str, Any]):
        self.kind = kind
        self.firmware = firmware
        self.capabilities = capabilities
        self.last_seen_ts = datetime.utcnow()

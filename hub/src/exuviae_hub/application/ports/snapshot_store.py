from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class StoredSnapshot:
    image_path: str
    bytes_written: int


class ISnapshotStore(Protocol):
    def save_jpeg(self, node_id: str, snapshot_id: str, jpeg_bytes: bytes, now: datetime | None = None) -> StoredSnapshot:
        ...

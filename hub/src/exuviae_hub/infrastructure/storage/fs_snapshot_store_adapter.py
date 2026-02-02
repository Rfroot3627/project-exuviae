from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ...application.ports.snapshot_store import ISnapshotStore, StoredSnapshot
from .fs_snapshot_store import FsSnapshotStore


@dataclass
class FsSnapshotStoreAdapter(ISnapshotStore):
    repo_root: Path | None = None

    def __post_init__(self):
        self._impl = FsSnapshotStore(repo_root=self.repo_root)

    def save_jpeg(self, node_id: str, snapshot_id: str, jpeg_bytes: bytes, now: datetime | None = None) -> StoredSnapshot:
        stored = self._impl.save_jpeg(node_id=node_id, snapshot_id=snapshot_id, jpeg_bytes=jpeg_bytes, now=now)
        return StoredSnapshot(image_path=stored.image_path, bytes_written=stored.bytes_written)

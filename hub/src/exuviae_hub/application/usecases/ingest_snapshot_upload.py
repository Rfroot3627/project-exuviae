from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from ..ports.snapshot_store import ISnapshotStore
from ..ports.vision_describer import IVisionDescriber
from ..ports.log_writer import ILogWriter

TZ_TAIPEI = ZoneInfo("Asia/Taipei")


@dataclass
class IngestSnapshotUpload:
    snapshot_store: ISnapshotStore

    def handle(self, node_id: str, snapshot_id: str, jpeg_bytes: bytes) -> dict:
        now = datetime.now(TZ_TAIPEI)

        stored = self.snapshot_store.save_jpeg(node_id=node_id, snapshot_id=snapshot_id, jpeg_bytes=jpeg_bytes, now=now)

        return {
            "ok": True,
            "snapshot_id": snapshot_id,
            "image_path": stored.image_path,
        }

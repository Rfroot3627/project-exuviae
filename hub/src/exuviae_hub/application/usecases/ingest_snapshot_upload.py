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
    describer: IVisionDescriber
    log_writer: ILogWriter

    def handle(self, node_id: str, snapshot_id: str, jpeg_bytes: bytes) -> dict:
        now = datetime.now(TZ_TAIPEI)

        stored = self.snapshot_store.save_jpeg(node_id=node_id, snapshot_id=snapshot_id, jpeg_bytes=jpeg_bytes, now=now)
        desc, model = self.describer.describe_image_path(stored.image_path)

        line = {
            "ts": now.isoformat(),
            "node_id": node_id,
            "snapshot_id": snapshot_id,
            "image_path": stored.image_path,
            "desc": desc,
            "model": model,
            "latency_ms": 0
        }
        self.log_writer.append_vision_log_line(line)

        return {
            "ok": True,
            "image_path": stored.image_path,
        }

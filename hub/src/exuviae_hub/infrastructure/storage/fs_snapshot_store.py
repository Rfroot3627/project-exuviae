from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ...core.ids import is_valid_snapshot_id
from .. import config

TZ_TAIPEI = ZoneInfo("Asia/Taipei")


def _is_safe_node_id(node_id: str) -> bool:
    from ...core.patterns import validate_by_pattern
    return validate_by_pattern("node_id", node_id)


@dataclass(frozen=True)
class StoredSnapshot:
    image_path: str          # repo-relative path (e.g. data/snapshots/...)
    abs_path: Path           # absolute filesystem path
    bytes_written: int


class FsSnapshotStore:
    """
    v0.1 filesystem snapshot store.

    Layout:
      {DATA_ROOT}/{SNAPSHOT_SUBDIR}/{YYYY-MM-DD}/{node_id}/{snapshot_id}.jpg
    Example:
      data/snapshots/2026-02-02/cam-01/s-20260202-173012-4f2a9c10.jpg
    """

    def __init__(self, repo_root: Path | None = None):
        # repo_root allows tests to point to a temp directory.
        # In production, default to current working directory (repo root).
        self._repo_root = repo_root or Path.cwd()

    def build_relative_path(self, node_id: str, snapshot_id: str, now: datetime | None = None) -> str:
        if not _is_safe_node_id(node_id):
            raise ValueError(f"invalid node_id: {node_id!r}")
        if not is_valid_snapshot_id(snapshot_id):
            raise ValueError(f"invalid snapshot_id: {snapshot_id!r}")

        if now is None:
            now = datetime.now(TZ_TAIPEI)
        else:
            if now.tzinfo is None:
                now = now.replace(tzinfo=TZ_TAIPEI)
            else:
                now = now.astimezone(TZ_TAIPEI)

        date_bucket = now.strftime("%Y-%m-%d")
        # v0.1: jpeg only -> .jpg
        rel = f"{config.settings.DATA_ROOT}/{config.settings.SNAPSHOT_SUBDIR}/{date_bucket}/{node_id}/{snapshot_id}.jpg"
        return rel

    def save_jpeg(self, node_id: str, snapshot_id: str, jpeg_bytes: bytes, now: datetime | None = None) -> StoredSnapshot:
        rel = self.build_relative_path(node_id=node_id, snapshot_id=snapshot_id, now=now)
        
        # Validate against SSOT image_path pattern
        from ...core.patterns import validate_by_pattern
        if not validate_by_pattern("image_path", rel):
            raise ValueError(f"generated path {rel!r} does not match SSOT image_path pattern")

        abs_path = (self._repo_root / rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(jpeg_bytes)

        return StoredSnapshot(
            image_path=rel.replace("\\", "/"),
            abs_path=abs_path,
            bytes_written=len(jpeg_bytes),
        )

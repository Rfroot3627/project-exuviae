from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# v0.1 snapshot_id format:
#   s-YYYYMMDD-HHMMSS-<8hex>
# Example:
#   s-20260202-173012-4f2a9c10


def new_snapshot_id(now: datetime | None = None) -> str:
    """
    Generate a v0.1 snapshot_id.

    Constraints:
    - filename-safe characters only
    - includes local timestamp (Asia/Taipei) for traceability
    - randomized suffix to avoid collisions
    """
    if now is None:
        now = datetime.now(TZ_TAIPEI)
    else:
        # Normalize any provided datetime into Asia/Taipei
        if now.tzinfo is None:
            now = now.replace(tzinfo=TZ_TAIPEI)
        else:
            now = now.astimezone(TZ_TAIPEI)

    ts = now.strftime("%Y%m%d-%H%M%S")
    rnd = secrets.token_hex(4)  # 8 hex chars (32 bits)
    return f"s-{ts}-{rnd}"


def is_valid_snapshot_id(snapshot_id: str) -> bool:
    """
    Lightweight validation (no regex dependency).
    """
    if not snapshot_id.startswith("s-"):
        return False

    parts = snapshot_id.split("-")
    # Expected: ["s", "YYYYMMDD", "HHMMSS", "<8hex>"]
    if len(parts) != 4:
        return False

    _, ymd, hms, rnd = parts
    if len(ymd) != 8 or not ymd.isdigit():
        return False
    if len(hms) != 6 or not hms.isdigit():
        return False
    if len(rnd) != 8:
        return False
    # hex check
    try:
        int(rnd, 16)
    except ValueError:
        return False

    return True


@dataclass(frozen=True)
class SnapshotIds:
    """
    Convenience container if you later want multiple correlated ids.
    (v0.1 only uses snapshot_id, but this prevents future refactors.)
    """
    snapshot_id: str

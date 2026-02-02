from __future__ import annotations

def is_valid_snapshot_id(snapshot_id: str) -> bool:
    # Same rules as Hub v0.1
    if not snapshot_id.startswith("s-"):
        return False
    parts = snapshot_id.split("-")
    if len(parts) != 4:
        return False
    _, ymd, hms, rnd = parts
    if len(ymd) != 8 or not ymd.isdigit():
        return False
    if len(hms) != 6 or not hms.isdigit():
        return False
    if len(rnd) != 8:
        return False
    try:
        int(rnd, 16)
    except ValueError:
        return False
    return True

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .. import config

TZ_TAIPEI = ZoneInfo("Asia/Taipei")


@dataclass
class JsonlLogWriter:
    """
    v0.1: append JSONL lines.
    Default file: data/logs/vision.jsonl
    """
    repo_root: Path | None = None

    def _abs_log_path(self) -> Path:
        root = self.repo_root or Path.cwd()
        return (root / config.settings.DATA_ROOT / "logs" / "vision.jsonl").resolve()

    def append_vision_log_line(self, line: dict) -> None:
        # Ensure directory exists
        p = self._abs_log_path()
        p.parent.mkdir(parents=True, exist_ok=True)

        # Ensure ts exists
        if "ts" not in line:
            line["ts"] = datetime.now(TZ_TAIPEI).isoformat()

        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

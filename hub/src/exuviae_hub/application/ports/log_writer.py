from __future__ import annotations

from typing import Protocol


class ILogWriter(Protocol):
    def append_vision_log_line(self, line: dict) -> None:
        ...

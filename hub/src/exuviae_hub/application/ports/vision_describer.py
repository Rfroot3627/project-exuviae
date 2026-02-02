from __future__ import annotations

from typing import Protocol


class IVisionDescriber(Protocol):
    def describe_image_path(self, image_path: str) -> tuple[str, str]:
        """
        Returns (desc, model_name).
        v0.1 can be stubbed.
        """
        ...

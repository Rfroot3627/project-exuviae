from __future__ import annotations


class StubVisionDescriber:
    def describe_image_path(self, image_path: str) -> tuple[str, str]:
        # v0.1 stub: no model call yet
        desc = f"snapshot stored at {image_path}"
        model = "stub-v0.1"
        return desc, model

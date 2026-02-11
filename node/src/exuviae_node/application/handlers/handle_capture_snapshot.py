from __future__ import annotations
import logging
import requests
import json
import os
import tempfile
from pathlib import Path
from exuviae_node.infrastructure.camera.pi_camera import LibcameraAdapter

logger = logging.getLogger(__name__)

# Strict SSOT: Capture Handler
# Source: ws/messages.schema.json (CommandCaptureSnapshot)
# Dest: http/openapi.v0.yaml (/api/v0/snapshots/upload)

class CaptureSnapshotHandler:
    def __init__(self, camera_adapter: LibcameraAdapter, http_base: str, node_id: str):
        self.camera = camera_adapter
        self.http_base = http_base.rstrip("/")
        self.node_id = node_id

    def handle(self, command: dict):
        """
        Orchestrate capture and upload.
        """
        # 1. Validation (Fail-fast as per contract)
        if command.get("type") != "command.capture_snapshot":
            logger.warning(f"Handler received wrong type: {command.get('type')}")
            return

        snapshot_id = command.get("snapshot_id")
        params = command.get("params", {})
        
        if not snapshot_id:
            logger.error("Missing required field: snapshot_id")
            return

        # Params validation from contract
        fmt = params.get("format")
        res = params.get("resolution")

        if fmt != "jpeg":
            logger.error(f"Unsupported format: {fmt}. Only 'jpeg' is allowed by contract.")
            return
        
        if not res or "x" not in res:
            logger.error(f"Invalid or missing resolution: {res}")
            return
        
        try:
            width, height = map(int, res.split("x"))
        except ValueError:
            logger.error(f"Resolution parse error: {res}")
            return

        logger.info(f"[EXEC] Capture {snapshot_id} (res={res})")

        # 2. Capture (Execute)
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / f"{snapshot_id}.jpg"
            
            success = self.camera.capture(tmp_path, width, height)
            
            if not success:
                logger.error("Capture failed at infrastructure level.")
                # TODO: In strict contract, we might want to send Error message back via WS if allowed.
                # For now, MVP logs and returns.
                return

            # 3. Upload (Execute)
            self._upload_snapshot(tmp_path, snapshot_id)

    def _upload_snapshot(self, image_path: Path, snapshot_id: str):
        url = f"{self.http_base}/api/v0/snapshots/upload"
        
        # Contract: snapshot_id, node_id as form data, image as file
        files = {
            "image": (image_path.name, open(image_path, "rb"), "image/jpeg")
        }
        data = {
            "node_id": self.node_id,
            "snapshot_id": snapshot_id
        }

        try:
            logger.info(f"Uploading to {url}...")
            resp = requests.post(url, data=data, files=files, timeout=30)
            resp.raise_for_status()
            logger.info(f"Upload success: {resp.json()}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
        finally:
            files["image"][1].close()

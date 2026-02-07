from __future__ import annotations
import json
import os
from pathlib import Path
from fastapi.testclient import TestClient
from exuviae_hub.main import create_app
from exuviae_hub.infrastructure.config import settings

def test_pr4_command_to_logline_flow(tmp_path):
    # Setup: Use tmp_path for data root
    # 使用 tmp repo_root 注入 store/log 的根目錄；實際相對路徑由 settings/patterns 決定
    repo_root = tmp_path
    
    from exuviae_hub.infrastructure.storage.fs_snapshot_store import FsSnapshotStore
    from exuviae_hub.infrastructure.storage.jsonl_log_writer import JsonlLogWriter
    from exuviae_hub.application.usecases.ingest_snapshot_upload import IngestSnapshotUpload
    
    # Manually assemble to inject repo_root
    store = FsSnapshotStore(repo_root=repo_root)
    log_writer = JsonlLogWriter(repo_root=repo_root)
    
    app = create_app()
    from exuviae_hub.adapters.http import routes
    
    # We need a proper describer stub too
    from exuviae_hub.infrastructure.vision.describer_stub import StubVisionDescriber
    describer = StubVisionDescriber()
    
    ingest_uc = IngestSnapshotUpload(
        snapshot_store=store,
        describer=describer,
        log_writer=log_writer
    )
    routes.get_ingest_usecase = lambda: ingest_uc
    
    client = TestClient(app)
    
    node_id = "cam-test-01" # Valid node_id
    
    # 1. Trigger Capture (Command)
    resp_capture = client.post("/api/v0/capture", json={"node_id": node_id})
    assert resp_capture.status_code == 200
    snapshot_id = resp_capture.json()["snapshot_id"]
    
    # 2. Upload Image
    # Minimal valid JPEG bytes (SOI + EOI)
    image_bytes = b"\xff\xd8\xff\xd9"
    
    files = {"image": ("test.jpg", image_bytes, "image/jpeg")}
    data = {"node_id": node_id, "snapshot_id": snapshot_id}
    
    resp_upload = client.post("/api/v0/snapshots/upload", data=data, files=files)
    assert resp_upload.status_code == 200
    res_json = resp_upload.json()
    image_path_str = res_json["image_path"]
    
    # 3. Verify File Persistence
    abs_image_path = (repo_root / image_path_str).resolve()
    assert abs_image_path.exists()
    assert abs_image_path.read_bytes() == image_bytes
    
    # 4. Verify Vision Log Entry
    # Locate log file using settings
    log_rel_path = Path(settings.DATA_ROOT) / settings.LOG_SUBDIR / settings.VISION_LOG_FILENAME
    abs_log_path = (repo_root / log_rel_path).resolve()
    
    assert abs_log_path.exists()
    lines = abs_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 1
    
    # Parse last line to verify schema and data correlation
    last_line = json.loads(lines[-1])
    assert last_line["snapshot_id"] == snapshot_id
    assert last_line["node_id"] == node_id
    assert last_line["image_path"] == image_path_str
    assert "desc" in last_line
    assert isinstance(last_line["desc"], str)
    assert "ts" in last_line

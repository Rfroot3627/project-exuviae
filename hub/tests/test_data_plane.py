from __future__ import annotations
import os
from pathlib import Path
from fastapi.testclient import TestClient
from exuviae_hub.main import create_app
from exuviae_hub.infrastructure.config import settings

def test_upload_image_mvp(tmp_path):
    # Keep DATA_ROOT as 'data' to satisfy SSOT regex ^data/
    # But point the filesystem root (repo_root) to a temp dir
    repo_root = tmp_path
    
    from exuviae_hub.infrastructure.storage.fs_snapshot_store import FsSnapshotStore
    from exuviae_hub.infrastructure.storage.jsonl_log_writer import JsonlLogWriter
    from exuviae_hub.infrastructure.vision.describer_stub import StubVisionDescriber
    from exuviae_hub.application.usecases.ingest_snapshot_upload import IngestSnapshotUpload
    
    # 1. Create dependencies with the temp repo_root
    store = FsSnapshotStore(repo_root=repo_root)
    log_writer = JsonlLogWriter(repo_root=repo_root)
    describer = StubVisionDescriber()
    
    # 2. Create the use case
    ingest_uc = IngestSnapshotUpload(
        snapshot_store=store,
        describer=describer,
        log_writer=log_writer,
    )
    
    app = create_app()
    # 3. Inject our test use case
    from exuviae_hub.adapters.http import routes
    routes.get_ingest_usecase = lambda: ingest_uc
    
    client = TestClient(app)
    
    node_id = "cam-test-01"
    # Generate a valid snapshot_id using hub's core logic
    from exuviae_hub.core.ids import new_snapshot_id
    snapshot_id = new_snapshot_id()
    
    image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xff\xdb\x00\x43..."
    
    files = {"image": ("test.jpg", image_bytes, "image/jpeg")}
    data = {"node_id": node_id, "snapshot_id": snapshot_id}
    
    response = client.post("/api/v0/snapshots/upload", data=data, files=files)
    
    # Validation: HTTP 200 and JSON consistency
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["ok"] is True
    assert res_json["snapshot_id"] == snapshot_id
    
    # Validation: File existence
    image_path_str = res_json["image_path"]
    # Since repo_root is tmp_path, the file should be at tmp_path / image_path_str
    abs_stored_path = (repo_root / image_path_str).resolve()
    
    assert abs_stored_path.exists(), f"File should exist at {abs_stored_path}"
    assert abs_stored_path.read_bytes() == image_bytes

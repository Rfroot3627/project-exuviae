from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from ...application.usecases.ingest_snapshot_upload import IngestSnapshotUpload

router = APIRouter()


def get_ingest_usecase() -> IngestSnapshotUpload:
    # This will be replaced by DI wiring in main.py
    raise RuntimeError("DI not wired: IngestSnapshotUpload")


@router.post("/api/v0/snapshots/upload")
async def upload_snapshot(
    node_id: str = Form(...),
    snapshot_id: str = Form(...),
    image: UploadFile = File(...),
):
    jpeg_bytes = await image.read()

    uc = get_ingest_usecase()
    result = uc.handle(node_id=node_id, snapshot_id=snapshot_id, jpeg_bytes=jpeg_bytes)
    return result

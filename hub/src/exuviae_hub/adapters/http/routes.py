from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile, WebSocket, WebSocketDisconnect, HTTPException

from ...application.usecases.ingest_snapshot_upload import IngestSnapshotUpload
from .dto import (
    OkResponse,
    NodeRegister,
    NodeListResponse,
    CaptureRequest,
    CaptureResponse,
    SnapshotUploadResponse
)

router = APIRouter()


def get_ingest_usecase() -> IngestSnapshotUpload:
    # This will be replaced by DI wiring in main.py
    raise RuntimeError("DI not wired: IngestSnapshotUpload")


@router.post("/api/v0/nodes/register", response_model=OkResponse)
async def register_node(body: NodeRegister):
    return OkResponse(ok=True)


@router.get("/api/v0/nodes", response_model=NodeListResponse)
async def list_nodes():
    # DoD v0.1 does not explicitly require listing nodes.
    # Supporting it strictly for management is not part of "Capture -> Describe -> Log" loop.
    # marked as TODO/Not Implemented for MVP.
    raise HTTPException(status_code=501, detail="Not implemented in MVP v0.1")
    # return NodeListResponse(ok=True, nodes=[])


@router.post("/api/v0/capture", response_model=CaptureResponse)
async def request_capture(body: CaptureRequest):
    from ...core.ids import new_snapshot_id
    snapshot_id = new_snapshot_id()
    return CaptureResponse(ok=True, snapshot_id=snapshot_id)


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


@router.websocket("/ws/v0")
async def websocket_endpoint(websocket: WebSocket, node_id: str):
    await websocket.accept()
    try:
        while True:
            # Keep connection open for skeleton
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        pass

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

def get_register_usecase() -> RegisterNode:
    raise RuntimeError("DI not wired: RegisterNode")

def get_list_nodes_usecase() -> ListNodes:
    raise RuntimeError("DI not wired: ListNodes")


@router.post("/api/v0/nodes/register", response_model=OkResponse)
async def register_node(body: NodeRegister):
    uc = get_register_usecase()
    result = uc.handle(
        node_id=body.node_id,
        kind=body.kind,
        firmware=body.firmware,
        capabilities=body.capabilities
    )
    return result


@router.get("/api/v0/nodes", response_model=NodeListResponse)
async def list_nodes():
    uc = get_list_nodes_usecase()
    nodes = uc.handle()
    return NodeListResponse(ok=True, nodes=nodes) # type: ignore


@router.post("/api/v0/capture", response_model=CaptureResponse)
async def request_capture(body: CaptureRequest):
    from ...core.ids import new_snapshot_id
    from datetime import datetime
    
    snapshot_id = new_snapshot_id()
    
    # Construct WS Command
    # Strict SSOT: Must match messages.schema.json
    cmd = {
        "type": "command.capture_snapshot",
        "snapshot_id": snapshot_id,
        "params": {
            "format": "jpeg",
            "resolution": "1280x720" # Default or parameterized from API? API v0.yaml CaptureRequest only has node_id.
                                     # For MVP, hardcode valid resolution or derive from config if available.
                                     # Let's use a safe default 640x480 for speed/safety.
        },
        "issued_at": datetime.utcnow().isoformat()
    }
    
    # Broadcast to all (Node will filter by node_id if we add logic, or just handle if it's the target)
    # Currently Node logic handles all commands it receives. 
    # Ideally we should route to specific node_id, but broadcast is fine for MVP.
    await manager.broadcast(json.dumps(cmd))
    
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


from typing import List

import json
from pathlib import Path

class ConnectionManager:
    """Minimal WS manager with dynamic contract-driven guardrails."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._whitelist = self._load_contract_whitelist()

    def _load_contract_whitelist(self) -> set[str]:
        """Dynamically extract allowed message types from messages.schema.json."""
        try:
            # hub/src/exuviae_hub/adapters/http/routes.py -> hub/
            schema_path = Path(__file__).parent.parent.parent.parent.parent / "contracts/ws/messages.schema.json"
            if not schema_path.exists():
                # Fallback for different run contexts if needed, but primary is repo-relative
                schema_path = Path("contracts/ws/messages.schema.json")
            
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            
            allowed = set()
            # Walk oneOf to find types
            for item in schema.get("oneOf", []):
                ref = item.get("$ref")
                if ref and ref.startswith("#/$defs/"):
                    def_key = ref.split("/")[-1]
                    item_def = schema.get("$defs", {}).get(def_key, {})
                    
                    # Consistently look for properties/type/const in defs (Standard pattern in our schema)
                    # We look through allOf if present
                    potential_defs = [item_def]
                    if "allOf" in item_def:
                        potential_defs.extend(item_def["allOf"])
                    
                    for d in potential_defs:
                        t_const = d.get("properties", {}).get("type", {}).get("const")
                        if t_const:
                            allowed.add(t_const)
            
            if not allowed:
                # Fail-fast: If we can't extract any types, the contract might have changed or be unreadable
                print(f"CRITICAL: Failed to extract WS type whitelist from {schema_path}")
                return set()
            return allowed
        except Exception as e:
            print(f"CRITICAL: Error loading WS contract: {e}")
            return set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Relay message only if type is in the contract-driven whitelist."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type not in self._whitelist:
                print(f"[WS] Dropping unknown/invalid type: {msg_type}")
                return
                
            print(f"[WS] Broadcasting '{msg_type}' to {len(self.active_connections)} nodes")
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"[WS] Send failed for a connection: {e}")
                    pass
        except Exception as e:
            print(f"[WS] Broadcast error: {e}")

manager = ConnectionManager()

@router.websocket("/ws/v0")
async def websocket_endpoint(websocket: WebSocket, node_id: str):
    await manager.connect(websocket)
    try:
        while True:
            # Broadcast received messages to allow trigger tools to reach nodes
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

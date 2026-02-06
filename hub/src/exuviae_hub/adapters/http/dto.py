from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class OkResponse(BaseModel):
    ok: bool

class SnapshotUploadResponse(BaseModel):
    ok: bool
    snapshot_id: str
    image_path: str

class NodeRegister(BaseModel):
    node_id: str
    kind: str
    firmware: str
    capabilities: Dict[str, Any]

class NodeInfo(BaseModel):
    node_id: str
    kind: str
    firmware: str
    capabilities: Dict[str, Any]
    # last_seen_ts is optional in schema? 
    # Spec says required: [node_id, kind, firmware, capabilities]. last_seen_ts is in properties but not in required list of NodeInfo?
    # Checking spec... required: [node_id, kind, firmware, capabilities]. last_seen_ts is NOT required.
    last_seen_ts: Optional[str] = None

class NodeListResponse(BaseModel):
    ok: bool
    nodes: List[NodeInfo]

class CaptureRequest(BaseModel):
    node_id: str

class CaptureResponse(BaseModel):
    ok: bool
    snapshot_id: str

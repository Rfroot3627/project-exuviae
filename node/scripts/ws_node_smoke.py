import os
import sys
import json
import yaml
import asyncio
import websockets
import requests
from pathlib import Path

# --- SSOT Paths ---
ROOT = Path(__file__).parent.parent.parent
HTTP_CONTRACT = ROOT / "hub" / "contracts" / "http" / "openapi.v0.yaml"
WS_CONTRACT = ROOT / "hub" / "contracts" / "ws" / "messages.schema.json"

def resolve_ref(spec, ref):
    if not ref.startswith("#/"): return None
    parts = ref.split("/")[1:]
    doc = spec
    for p in parts: doc = doc.get(p, {})
    return doc

def extract_http_info():
    """Extract upload fields from OpenAPI"""
    with open(HTTP_CONTRACT, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    
    # Find upload path
    up_path = None
    up_op = None
    for path, methods in spec.get("paths", {}).items():
        if "snapshots/upload" in path and "post" in methods:
            up_path = path
            up_op = methods["post"]
            break
    
    if not up_path:
        print("Fail-fast: Could not find upload endpoint in openapi.v0.yaml")
        sys.exit(1)
        
    schema = up_op["requestBody"]["content"]["multipart/form-data"]["schema"]
    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])
    
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    
    file_field = None
    all_fields = list(properties.keys())
    for name, prop in properties.items():
        if "$ref" in prop: prop = resolve_ref(spec, prop["$ref"])
        if prop.get("type") == "string" and prop.get("format") == "binary":
            file_field = name
            
    if not file_field:
        print("Fail-fast: Could not identify file field in upload schema")
        sys.exit(1)
        
    return up_path, all_fields, file_field

def extract_ws_info():
    """Extract command type from WS schema"""
    with open(WS_CONTRACT, "r", encoding="utf-8") as f:
        spec = json.load(f)
    
    cmd_def = spec["$defs"].get("CommandCaptureSnapshot", {})
    # Find type const
    msg_type = None
    for schema in cmd_def.get("allOf", []):
        props = schema.get("properties", {})
        if "type" in props and "const" in props["type"]:
            msg_type = props["type"]["const"]
            break
            
    if not msg_type:
        # Fallback to example if schema feels too complex for this MVP logic
        print("Warning: Could not extract specific command type from schema defs, checking examples...")
        example_path = Path(WS_CONTRACT).parent / "examples" / "ws.command.capture_snapshot.json"
        if example_path.exists():
            with open(example_path, "r") as ef:
                msg_type = json.load(ef).get("type")
    
    if not msg_type:
        print("Fail-fast: Could not determine command type from WS contract")
        sys.exit(1)
        
    return msg_type

async def handle_command(msg_data, http_info, hub_base, node_id):
    up_path, up_fields, file_field = http_info
    
    sid = msg_data.get("snapshot_id")
    if not sid:
        print("Skipping: Received command but snapshot_id is missing (Schema violation)")
        return

    print(f"\n[EXEC] Received command. Triggering upload for snapshot_id: {sid}")
    
    url = f"{hub_base}{up_path}"
    mock_jpg = b"\xff\xd8\xff\xd9"
    files = {file_field: ("ws_trigger.jpg", mock_jpg, "image/jpeg")}
    
    # Map fields
    form_data = {}
    for f in up_fields:
        if "node_id" in f: form_data[f] = node_id
        if "snapshot_id" in f: form_data[f] = sid
        
    try:
        resp = requests.post(url, data=form_data, files=files, timeout=10)
        resp.raise_for_status()
        print(f"Success! Hub Response: {resp.json()}")
    except Exception as e:
        print(f"Upload failed: {e}")

async def listen():
    hub_base = os.getenv("HUB_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    node_id = os.getenv("NODE_ID", "cam-test-01")
    ws_url = os.getenv("HUB_WS_URL", f"ws://127.0.0.1:8000/ws/v0?node_id={node_id}")

    print("--- Node WS Client (Strict SSOT) ---")
    http_info = extract_http_info()
    cmd_type = extract_ws_info()
    print(f"Contract Alignment:")
    print(f" - Command Type: {cmd_type}")
    print(f" - Upload Path: {http_info[0]}")
    print(f" - File Field:  {http_info[2]}")

    print(f"\nConnecting to {ws_url}...")
    try:
        async with websockets.connect(ws_url) as ws:
            print("Connected. Waiting for commands...")
            while True:
                raw_msg = await ws.recv()
                try:
                    data = json.loads(raw_msg)
                    if data.get("type") == cmd_type:
                        await handle_command(data, http_info, hub_base, node_id)
                    else:
                        print(f"Ignored unknown message type: {data.get('type')}")
                except Exception as e:
                    print(f"Error parsing message: {e}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(listen())

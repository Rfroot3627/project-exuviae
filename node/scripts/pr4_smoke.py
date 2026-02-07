from __future__ import annotations
import os
import sys
import yaml
import requests
from pathlib import Path

# --- SSOT: OpenAPI Contract Path ---
CONTRACT_PATH = Path(__file__).parent.parent.parent / "hub" / "contracts" / "http" / "openapi.v0.yaml"

def resolve_ref(spec, ref):
    """Simple resolver for internal JSON references like #/components/schemas/Name"""
    if not ref.startswith("#/"):
        return None
    parts = ref.split("/")[1:]
    doc = spec
    for p in parts:
        doc = doc.get(p, {})
    return doc

def extract_schema_info(spec, schema):
    """Extract required fields and multipart file field name from a schema"""
    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])
    
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    
    file_field = None
    for name, prop in properties.items():
        if "$ref" in prop:
            prop = resolve_ref(spec, prop["$ref"])
        if prop.get("type") == "string" and prop.get("format") == "binary":
            file_field = name
            
    return required, list(properties.keys()), file_field

def find_endpoint(spec, keyword):
    """Find path and method containing the keyword in path string"""
    for path, methods in spec.get("paths", {}).items():
        if keyword in path:
            # We assume POST for these MVP endpoints
            if "post" in methods:
                return path, "post", methods["post"]
    return None, None, None

def parse_contract():
    if not CONTRACT_PATH.exists():
        print(f"Error: Contract NOT found at {CONTRACT_PATH}")
        sys.exit(1)
    
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    
    # 1. Register
    reg_path, reg_method, reg_op = find_endpoint(spec, "nodes/register")
    if not reg_path:
        print("Fail-fast: Register endpoint NOT found in OpenAPI contract.")
        sys.exit(1)
    reg_schema = reg_op["requestBody"]["content"]["application/json"]["schema"]
    reg_req, reg_all, _ = extract_schema_info(spec, reg_schema)

    # 2. Capture
    cap_path, cap_method, cap_op = find_endpoint(spec, "capture")
    if not cap_path:
        print("Fail-fast: Capture endpoint NOT found in OpenAPI contract.")
        sys.exit(1)
    cap_schema = cap_op["requestBody"]["content"]["application/json"]["schema"]
    cap_req, cap_all, _ = extract_schema_info(spec, cap_schema)

    # 3. Upload
    up_path, up_method, up_op = find_endpoint(spec, "snapshots/upload")
    if not up_path:
        print("Fail-fast: Upload endpoint NOT found in OpenAPI contract.")
        sys.exit(1)
    # Upload is multipart/form-data
    up_schema = up_op["requestBody"]["content"]["multipart/form-data"]["schema"]
    up_req, up_all, up_file = extract_schema_info(spec, up_schema)
    
    if not up_file:
        print("Fail-fast: Could NOT identify multipart file field (format: binary) in Upload schema.")
        sys.exit(1)

    return {
        "register": {"path": reg_path, "method": reg_method, "required": reg_req, "all": reg_all},
        "capture": {"path": cap_path, "method": cap_method, "required": cap_req, "all": cap_all},
        "upload": {"path": up_path, "method": up_method, "required": up_req, "all": up_all, "file_field": up_file}
    }

def run_smoke():
    hub_base = os.getenv("HUB_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    node_id = "cam-test-01"
    do_register = os.getenv("NODE_REGISTER") == "1" or "--register" in sys.argv

    print(f"--- PR4 Smoke (Strict SSOT) ---")
    print(f"Contract: {CONTRACT_PATH.resolve()}")
    
    contract = parse_contract()
    
    print("\n[Parsed Contract Domains]")
    for name, info in contract.items():
        print(f" - {name.capitalize()}: {info['method'].upper()} {info['path']}")
        print(f"   Fields: {info['all']}")
        if "file_field" in info:
            print(f"   File Field: {info['file_field']}")

    # 0. Optional Register
    if do_register:
        reg_info = contract["register"]
        url = f"{hub_base}{reg_info['path']}"
        print(f"\n[0] Optional Registering...")
        # Payload: ONLY required fields
        payload = {}
        for field in reg_info["required"]:
            if field == "node_id": payload[field] = node_id
            elif field == "kind": payload[field] = "node-runtime"
            elif field == "firmware": payload[field] = "0.1.0"
            elif field == "capabilities": payload[field] = {} # Empty mock
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"Body:   {resp.text}")
        except Exception as e:
            print(f"Register Failed: {e}")
            # Non-fatal for smoke if server rejects but we want to proceed to capture

    # 1. Capture
    cap_info = contract["capture"]
    url = f"{hub_base}{cap_info['path']}"
    print(f"\n[1/2] Requesting capture...")
    try:
        payload = {f: node_id for f in cap_info["all"] if "node_id" in f}
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        snapshot_id = data["snapshot_id"] # Use dynamic if it was in schema keys, but response is fixed here
        print(f"Success! snapshot_id: {snapshot_id}")
    except Exception as e:
        print(f"Capture failed: {e}")
        sys.exit(1)

    # 2. Upload
    up_info = contract["upload"]
    url = f"{hub_base}{up_info['path']}"
    print(f"\n[2/2] Uploading mock image...")
    
    mock_jpg = b"\xff\xd8\xff\xd9"
    files = {up_info["file_field"]: ("smoke.jpg", mock_jpg, "image/jpeg")}
    
    # Form data: Map IDs to keys found in contract
    form_data = {}
    for f in up_info["all"]:
        if "node_id" in f: form_data[f] = node_id
        if "snapshot_id" in f: form_data[f] = snapshot_id

    try:
        resp = requests.post(url, data=form_data, files=files, timeout=10)
        resp.raise_for_status()
        res_json = resp.json()
        print(f"Success! Response: {res_json}")
        print(f"Image Path: {res_json.get('image_path')}")
    except Exception as e:
        print(f"Upload failed: {e}")
        sys.exit(1)

    print(f"\nSmoke Finish. Hub record should be at {res_json.get('image_path')}")

if __name__ == "__main__":
    run_smoke()

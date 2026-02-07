from __future__ import annotations
import os
import requests
import sys

def run_smoke():
    hub_base = os.getenv("HUB_BASE_URL", "http://127.0.0.1:8000")
    node_id = "cam-test-01"
    
    print(f"--- Starting PR4 Smoke ---")
    print(f"Hub Base: {hub_base}")
    print(f"Node ID:  {node_id}")

    # 1. Capture (Get snapshot_id)
    capture_url = f"{hub_base}/api/v0/capture"
    print(f"\n[1/2] Requesting capture...")
    try:
        resp = requests.post(capture_url, json={"node_id": node_id}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        snapshot_id = data["snapshot_id"]
        print(f"Success! snapshot_id: {snapshot_id}")
    except Exception as e:
        print(f"Capture failed: {e}")
        if 'resp' in locals(): print(resp.text)
        sys.exit(1)

    # 2. Upload (Multipart)
    upload_url = f"{hub_base}/api/v0/snapshots/upload"
    print(f"\n[2/2] Uploading mock image...")
    # Minimal valid JPEG bytes (SOI + EOI)
    mock_jpg = b"\xff\xd8\xff\xd9"
    
    files = {"image": ("smoke.jpg", mock_jpg, "image/jpeg")}
    form_data = {
        "node_id": node_id,
        "snapshot_id": snapshot_id
    }
    
    try:
        resp = requests.post(upload_url, data=form_data, files=files, timeout=10)
        resp.raise_for_status()
        res_json = resp.json()
        print(f"Success! Response:")
        print(f" - ok: {res_json.get('ok')}")
        print(f" - image_path: {res_json.get('image_path')}")
        print(f"\nNode Side Done. Please check Hub's vision.jsonl and storage.")
    except Exception as e:
        print(f"Upload failed: {e}")
        if 'resp' in locals(): print(resp.text)
        sys.exit(1)

if __name__ == "__main__":
    run_smoke()

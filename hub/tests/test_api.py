#!/usr/bin/env python3
"""
Hub API 測試工具 (v0.1 MVP)

測試已實作的端點：
- POST /api/v0/nodes/register
- POST /api/v0/capture
- POST /api/v0/snapshots/upload
- GET /api/v0/nodes (應回傳 501)
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_register():
    """測試節點註冊"""
    print("🔵 測試 POST /api/v0/nodes/register")
    payload = {
        "node_id": "cam-test-01",
        "kind": "camera",
        "firmware": "0.1.0",
        "capabilities": {
            "capture": True,
            "resolution": "1920x1080"
        }
    }
    resp = requests.post(f"{BASE_URL}/api/v0/nodes/register", json=payload)
    print(f"   狀態: {resp.status_code}")
    print(f"   回應: {resp.json()}")
    assert resp.status_code == 200
    assert resp.json()["ok"] == True
    print("   ✅ 通過\n")

def test_list_nodes():
    """測試列出節點 (應為 501)"""
    print("🔵 測試 GET /api/v0/nodes (預期 501)")
    resp = requests.get(f"{BASE_URL}/api/v0/nodes")
    print(f"   狀態: {resp.status_code}")
    assert resp.status_code == 501
    print("   ✅ 通過 (正確回傳 Not Implemented)\n")

def test_capture():
    """測試觸發 Capture"""
    print("🔵 測試 POST /api/v0/capture")
    payload = {"node_id": "cam-test-01"}
    resp = requests.post(f"{BASE_URL}/api/v0/capture", json=payload)
    print(f"   狀態: {resp.status_code}")
    print(f"   回應: {resp.json()}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True
    assert "snapshot_id" in data
    print("   ✅ 通過\n")
    return data["snapshot_id"]

def test_upload_snapshot(snapshot_id: str):
    """測試上傳 Snapshot"""
    print("🔵 測試 POST /api/v0/snapshots/upload")
    
    # 建立測試用的假影像
    test_image = b'\xff\xd8\xff\xe0' + b'\x00' * 100  # 簡易 JPEG header
    
    files = {"image": ("test.jpg", test_image, "image/jpeg")}
    data = {
        "node_id": "cam-test-01",
        "snapshot_id": snapshot_id
    }
    
    resp = requests.post(f"{BASE_URL}/api/v0/snapshots/upload", files=files, data=data)
    print(f"   狀態: {resp.status_code}")
    
    # Better error handling
    if resp.status_code != 200:
        print(f"   錯誤回應 (text): {resp.text}")
        try:
            print(f"   錯誤回應 (json): {resp.json()}")
        except:
            pass
        raise AssertionError(f"Expected 200, got {resp.status_code}")
    
    print(f"   回應: {resp.json()}")
    result = resp.json()
    assert result["ok"] == True
    assert "image_path" in result
    print(f"   已儲存至: {result['image_path']}")
    print("   ✅ 通過\n")

def test_docs():
    """測試 Swagger UI 可訪問"""
    print("🔵 測試 GET /docs")
    resp = requests.get(f"{BASE_URL}/docs")
    print(f"   狀態: {resp.status_code}")
    assert resp.status_code == 200
    print("   ✅ Swagger UI 可訪問\n")

if __name__ == "__main__":
    print("="*60)
    print("Hub API 測試 (v0.1 MVP)")
    print("="*60 + "\n")
    
    try:
        test_docs()
        test_register()
        test_list_nodes()
        snapshot_id = test_capture()
        test_upload_snapshot(snapshot_id)
        
        print("="*60)
        print("✅ 所有測試通過！")
        print("="*60)
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        raise

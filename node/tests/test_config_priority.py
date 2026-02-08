import os
import yaml
import pytest
from pathlib import Path
from exuviae_node.infrastructure.config.loader import load_config, find_repo_root

def test_repo_root_detection():
    root = find_repo_root()
    assert (root / "node").is_dir() or (root / "hub").is_dir()
    assert root.is_absolute()

def test_config_priority_logic(tmp_path):
    # 建立一個測試用的 repo 結構模擬環境
    repo_mock = tmp_path / "repo"
    repo_mock.mkdir()
    (repo_mock / "node").mkdir() # Marker
    
    local_dir = repo_mock / ".agent" / "local"
    local_dir.mkdir(parents=True)
    local_config = local_dir / "config.yaml"
    
    # 我們需要稍微 Mock find_repo_root 或是透過環境變數直接測試 load_config 的路徑參數
    # 這裡直接測試帶有路徑參數的情境以及環境變數
    
    dummy_data = {
        "node_id": "test-node",
        "hub": {"http_base": "http://localhost", "ws_url": "ws://localhost"},
        "features": {"camera": {"enabled": True, "format": "jpeg", "resolution": "1x1"}}
    }
    
    config_file = tmp_path / "custom.yaml"
    with open(config_file, "w") as f:
        yaml.dump(dummy_data, f)
        
    # Test 1: Explicit path
    cfg = load_config(config_file)
    assert cfg.node_id == "test-node"
    
    # Test 2: Environment variable priority
    os.environ["EXUVIAE_NODE_CONFIG"] = str(config_file)
    try:
        # 即使傳入別的路徑，環境變數也應該贏
        cfg = load_config(Path(__file__).parent / "non_existent.yaml")
        assert cfg.node_id == "test-node"
    finally:
        del os.environ["EXUVIAE_NODE_CONFIG"]

def test_default_fallback():
    # 確保沒設定時至少能讀到 default.yaml (這依賴專案結構)
    cfg = load_config()
    assert cfg.node_id is not None
    assert cfg.hub.http_base is not None

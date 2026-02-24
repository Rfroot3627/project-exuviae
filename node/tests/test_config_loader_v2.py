import os
import yaml
import pytest
from pathlib import Path
from exuviae_node.infrastructure.config.loader import load_config

def create_valid_config(path: Path, node_id: str = "test-node"):
    data = {
        "node_id": node_id,
        "hub": {"http_base": "http://localhost:8000", "ws_url": "ws://localhost:8000"},
        "features": {"camera": {"enabled": True, "format": "jpeg", "resolution": "640x480"}}
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

def test_config_env_var_valid(tmp_path, monkeypatch):
    config_file = tmp_path / "custom_config.yaml"
    create_valid_config(config_file, node_id="env-node")
    
    monkeypatch.setenv("EXUVIAE_NODE_CONFIG", str(config_file))
    cfg = load_config()
    assert cfg.node_id == "env-node"

def test_config_env_var_invalid(tmp_path, monkeypatch):
    invalid_path = tmp_path / "missing.yaml"
    monkeypatch.setenv("EXUVIAE_NODE_CONFIG", str(invalid_path))
    
    with pytest.raises(RuntimeError, match="EXUVIAE_NODE_CONFIG is set but file not found"):
        load_config()

def test_config_upward_search(tmp_path, monkeypatch):
    # Setup: tmp_path / repo / .agent/local/config.yaml
    # CWD: tmp_path / repo / node / subdir
    repo_root = tmp_path / "my-repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").touch() # Root marker
    
    local_config = repo_root / ".agent" / "local" / "config.yaml"
    create_valid_config(local_config, node_id="upward-node")
    
    work_dir = repo_root / "node" / "subdir"
    work_dir.mkdir(parents=True)
    
    monkeypatch.delenv("EXUVIAE_NODE_CONFIG", raising=False)
    monkeypatch.chdir(work_dir)
    
    cfg = load_config()
    assert cfg.node_id == "upward-node"

def test_config_upward_search_stops_at_root(tmp_path, monkeypatch):
    # If a config exists outside the repo, it should NOT be found
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_config = outside_dir / ".agent" / "local" / "config.yaml"
    create_valid_config(outside_config, node_id="wrong-node")
    
    repo_root = outside_dir / "my-repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").touch() # Stop here
    
    work_dir = repo_root / "node"
    work_dir.mkdir()
    
    monkeypatch.delenv("EXUVIAE_NODE_CONFIG", raising=False)
    monkeypatch.chdir(work_dir)
    
    # Defaults to default.yaml because it stops at repo_root
    cfg = load_config()
    assert cfg.node_id != "wrong-node"

def test_config_fallback_with_warning(monkeypatch, capsys):
    monkeypatch.delenv("EXUVIAE_NODE_CONFIG", raising=False)
    # Ensure no .agent/local/config.yaml exists upward
    # (By chdir to a clean tmp directory)
    # But wait, default.yaml is relative to loader.py, so it will still be found.
    
    cfg = load_config()
    assert cfg is not None
    
    captured = capsys.readouterr()
    assert "WARNING: Using default config" in captured.err
    assert "Advice:" in captured.err

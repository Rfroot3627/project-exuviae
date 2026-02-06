import pytest
from pathlib import Path
from exuviae_node.infrastructure.config.loader import load_config

def test_load_config_default(tmp_path):
    # Create a dummy config file
    config_content = """
node_id: test-node
hub:
  http_base: "http://localhost:8000"
  ws_url: "ws://localhost:8000/ws/v0"
features:
  camera:
    enabled: true
    format: "jpeg"
    resolution: "640x480"
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    
    config = load_config(config_file)
    
    assert config.node_id == "test-node"
    assert config.hub.http_base == "http://localhost:8000"
    assert config.features.camera.enabled is True
    assert config.features.camera.format == "jpeg"

def test_load_config_schema_validation(tmp_path):
    # Missing required field 'hub'
    config_content = """
node_id: test-node
"""
    config_file = tmp_path / "invalid_config.yaml"
    config_file.write_text(config_content)
    
    with pytest.raises(Exception):
        load_config(config_file)

from __future__ import annotations
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class HubSettings(BaseModel):
    http_base: str
    ws_url: str

class CameraSettings(BaseModel):
    enabled: bool
    format: str
    resolution: str

class FeatureSettings(BaseModel):
    camera: CameraSettings

class NodeSettings(BaseModel):
    node_id: str
    hub: HubSettings
    features: FeatureSettings

def load_config(config_path: Path | str = None) -> NodeSettings:
    if config_path is None:
        # Default to the location of default.yaml relative to this file
        config_path = Path(__file__).parent / "default.yaml"
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return NodeSettings.model_validate(data)

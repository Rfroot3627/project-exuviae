from __future__ import annotations
import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

# --- Schema Definitions ---

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

# --- Logic ---

def find_repo_root() -> Path:
    """
    自目前檔案位置向上尋找包含特定標記(hub, node, contracts)的專案根目錄。
    避免硬編碼絕對路徑，確保跨環境穩定性。
    """
    current = Path(__file__).resolve().parent
    # 向上最多爬 10 層，避免無限循環
    for _ in range(10):
        if (current / "hub").is_dir() or (current / "node").is_dir() or (current / "contracts").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    
    # 回退機制：若找不到（例如單獨發布時），改以 node/ 目錄判定
    return Path(__file__).resolve().parent.parent.parent.parent.parent

def load_config(config_path: Path | str = None) -> NodeSettings:
    """
    載入配置優先序：
    1. EXUVIAE_NODE_CONFIG 環境變數
    2. [RepoRoot]/.agent/local/config.yaml (Gitignored)
    3. 內建 default.yaml
    """
    repo_root = find_repo_root()
    
    # 1. 環境變數優先
    env_path = os.environ.get("EXUVIAE_NODE_CONFIG")
    if env_path:
        target = Path(env_path)
    elif config_path:
        target = Path(config_path)
    else:
        # 2. 本地配置 (由 .gitignore 排出的開發者自定義)
        local_path = repo_root / ".agent" / "local" / "config.yaml"
        if local_path.exists():
            target = local_path
        else:
            # 3. 預設配置
            target = Path(__file__).parent / "default.yaml"
    
    if not target.exists():
        raise FileNotFoundError(f"Configuration file not found: {target}")

    with open(target, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return NodeSettings.model_validate(data)

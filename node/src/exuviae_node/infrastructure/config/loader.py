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


def load_config() -> NodeSettings:
    """
    載入配置優先序 (Strict v0.2)：
    1. EXUVIAE_NODE_CONFIG 環境變數 (必須指定現有檔案路徑，否則 Fail-fast)
    2. 向上搜尋：從 CWD 開始尋找 .agent/local/config.yaml，直到抵達專案根目錄 (.git 或 pyproject.toml)
    3. 回退至 default.yaml 並輸出明確告警
    """
    import sys

    # 1. 環境變數優先 (Pointer Only)
    env_path = os.environ.get("EXUVIAE_NODE_CONFIG")
    if env_path:
        target = Path(env_path)
        if not target.exists():
            # [Fail-fast] 如果指定了環境變數但找不到檔案，禁止執行
            raise RuntimeError(
                f"FATAL: EXUVIAE_NODE_CONFIG is set but file not found: {target.absolute()}\n"
                "Please check the path or unset the environment variable."
            )
        return _load_from_file(target)

    # 2. 向上搜尋 .agent/local/config.yaml
    # 從執行路徑 (CWD) 開始向上爬
    current = Path.cwd().resolve()
    for _ in range(12): # 限制深度避免過度搜尋
        local_config = current / ".agent" / "local" / "config.yaml"
        if local_config.exists():
            return _load_from_file(local_config)
        
        # 停止條件：抵達專案根目錄
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            break
            
        if current.parent == current:
            break
        current = current.parent

    # 3. 回退至內建預設配置
    default_path = Path(__file__).parent / "default.yaml"
    
    print("=" * 60, file=sys.stderr)
    print(f"WARNING: Using default config (v0.2 Fallback)", file=sys.stderr)
    print(f"Path: {default_path.absolute()}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    print("Advice:", file=sys.stderr)
    print("  - To use custom config, set environment variable:", file=sys.stderr)
    print("    $env:EXUVIAE_NODE_CONFIG = 'C:\\path\\to\\config.yaml'", file=sys.stderr)
    print("  - Or place it at: .agent/local/config.yaml (gitignored)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    return _load_from_file(default_path)

def _load_from_file(path: Path) -> NodeSettings:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return NodeSettings.model_validate(data)

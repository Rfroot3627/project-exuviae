from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

# Load SSOT patterns from the contract file
CONTRACTS_ROOT = Path(__file__).parents[3] / "contracts" / "_ssot"
PATTERNS_FILE = CONTRACTS_ROOT / "patterns.v0.1.json"

_patterns: dict[str, str] = {}

def _load_patterns():
    if not _patterns:
        with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            props = data.get("properties", {})
            for key, val in props.items():
                if isinstance(val, dict) and "pattern" in val:
                    _patterns[key] = val["pattern"]

def get_pattern(name: str) -> str:
    _load_patterns()
    pattern = _patterns.get(name)
    if not pattern:
        raise KeyError(f"Pattern {name!r} not found in SSOT contracts.")
    return pattern

def validate_by_pattern(name: str, value: str) -> bool:
    pattern = get_pattern(name)
    return bool(re.match(pattern, value))

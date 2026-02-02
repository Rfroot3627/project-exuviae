import json
import sys
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def load_yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))

def validate_examples(schema_path: Path, examples_dir: Path):
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)

    if not examples_dir.exists():
        return

    for ex in sorted(examples_dir.glob("*.json")):
        data = load_json(ex)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            print(f"[FAIL] {ex}")
            for e in errors[:5]:
                print("  -", e.message)
            raise SystemExit(1)
        print(f"[OK]   {ex}")

def main():
    # 1) OpenAPI YAML parse
    openapi = ROOT / "hub" / "contracts" / "http" / "openapi.v0.yaml"
    load_yaml(openapi)
    print(f"[OK]   parsed {openapi}")

    # 2) WS schema + examples
    ws_schema = ROOT / "hub" / "contracts" / "ws" / "messages.schema.json"
    ws_examples = ROOT / "hub" / "contracts" / "ws" / "examples"
    validate_examples(ws_schema, ws_examples)

    # 3) Capabilities schema + examples
    cap_schema = ROOT / "hub" / "contracts" / "capabilities" / "node_register.schema.json"
    cap_examples = ROOT / "hub" / "contracts" / "capabilities" / "examples"
    validate_examples(cap_schema, cap_examples)

    # 4) Logging schema + examples
    log_schema = ROOT / "hub" / "contracts" / "logging" / "vision_log_line.schema.json"
    log_examples = ROOT / "hub" / "contracts" / "logging" / "examples"
    validate_examples(log_schema, log_examples)

    print("\nAll contracts OK.")

if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print("[FAIL]", e)
        sys.exit(1)

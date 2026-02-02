from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Tuple

import jsonschema
import yaml
from openapi_spec_validator import validate_spec


ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_ID_RE = re.compile(r"^s-[0-9]{8}-[0-9]{6}-[0-9a-f]{8}$")


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def load_yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def validate_jsonschema_examples(schema_path: Path, examples_dir: Path):
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)

    if not examples_dir.exists():
        print(f"[WARN] examples dir not found: {examples_dir}")
        return

    examples = sorted(examples_dir.glob("*.json"))
    if not examples:
        print(f"[WARN] no examples found in: {examples_dir}")
        return

    for ex in examples:
        data = load_json(ex)
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            print(f"[FAIL] {ex}")
            for e in errors[:10]:
                path = "/".join(str(x) for x in e.path) if e.path else "<root>"
                print(f"  - {path}: {e.message}")
            raise SystemExit(1)
        print(f"[OK]   {ex}")


def validate_openapi(openapi_path: Path):
    spec = load_yaml(openapi_path)

    if not isinstance(spec, dict) or "openapi" not in spec:
        raise ValueError("Not a valid OpenAPI document (missing 'openapi' key)")

    validate_spec(spec)
    print(f"[OK]   validated OpenAPI: {openapi_path}")


def iter_snapshot_ids(obj: Any, path: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], str]]:
    """
    Recursively traverse JSON-like objects and yield (path, snapshot_id_value)
    for any field named 'snapshot_id'.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = path + (str(k),)
            if k == "snapshot_id" and isinstance(v, str):
                yield (new_path, v)
            else:
                yield from iter_snapshot_ids(v, new_path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_path = path + (f"[{i}]",)
            yield from iter_snapshot_ids(v, new_path)


def scan_examples_snapshot_ids():
    """
    Scan all examples JSON files under contracts/**/examples and ensure any
    snapshot_id matches v0.1 pattern: s-YYYYMMDD-HHMMSS-<8hex>
    """
    example_roots = [
        ROOT / "hub" / "contracts",
        ROOT / "node" / "contracts",
    ]

    json_files: list[Path] = []
    for base in example_roots:
        if not base.exists():
            continue
        json_files.extend(sorted(base.glob("**/examples/*.json")))

    if not json_files:
        print("[WARN] no example json files found under hub/node contracts examples")
        return

    failures = []
    for p in json_files:
        try:
            data = load_json(p)
        except Exception as e:
            failures.append((p, ("<parse>",), f"JSON parse failed: {e}"))
            continue

        found_any = False
        for spath, sval in iter_snapshot_ids(data):
            found_any = True
            if not SNAPSHOT_ID_RE.match(sval):
                failures.append((p, spath, sval))

        # Optional: could warn if a file is expected to have snapshot_id but doesn't.
        # We keep v0.1 minimal: no warning here.

    if failures:
        print("[FAIL] snapshot_id pattern scan failed:")
        for p, spath, sval in failures:
            jpath = "/".join(spath)
            print(f"  - {p}: {jpath} = {sval!r}")
        raise SystemExit(1)

    print(f"[OK]   snapshot_id scan passed ({len(json_files)} files scanned)")


def main():
    # --- OpenAPI ---
    openapi = ROOT / "hub" / "contracts" / "http" / "openapi.v0.yaml"
    if not openapi.exists():
        print(f"[FAIL] missing: {openapi}")
        return 1
    validate_openapi(openapi)

    # --- WebSocket schema + examples ---
    ws_schema = ROOT / "hub" / "contracts" / "ws" / "messages.schema.json"
    ws_examples = ROOT / "hub" / "contracts" / "ws" / "examples"
    validate_jsonschema_examples(ws_schema, ws_examples)

    # --- Capabilities schema + examples ---
    cap_schema = ROOT / "hub" / "contracts" / "capabilities" / "node_register.schema.json"
    cap_examples = ROOT / "hub" / "contracts" / "capabilities" / "examples"
    validate_jsonschema_examples(cap_schema, cap_examples)

    # --- Logging schema + examples ---
    log_schema = ROOT / "hub" / "contracts" / "logging" / "vision_log_line.schema.json"
    log_examples = ROOT / "hub" / "contracts" / "logging" / "examples"
    validate_jsonschema_examples(log_schema, log_examples)

    # --- Extra scan: snapshot_id in all examples ---
    scan_examples_snapshot_ids()

    print("\nAll contracts OK.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print("[FAIL]", repr(e))
        sys.exit(1)

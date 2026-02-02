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
IMAGE_PATH_RE = re.compile(
    r"^data/snapshots/[0-9]{4}-[0-9]{2}-[0-9]{2}/"
    r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}/"
    r"s-[0-9]{8}-[0-9]{6}-[0-9a-f]{8}\.jpg$"
)


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


def iter_field_values(obj: Any, field_name: str, path: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], str]]:
    """
    Recursively traverse JSON-like objects and yield (path, value) for any
    string field named field_name.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = path + (str(k),)
            if k == field_name and isinstance(v, str):
                yield (new_path, v)
            else:
                yield from iter_field_values(v, field_name, new_path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_path = path + (f"[{i}]",)
            yield from iter_field_values(v, field_name, new_path)


def scan_examples_fields():
    """
    Scan all examples JSON files under contracts/**/examples and ensure:
    - any snapshot_id matches v0.1 pattern
    - any image_path matches v0.1 snapshot storage path pattern
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

        # snapshot_id checks
        for spath, sval in iter_field_values(data, "snapshot_id"):
            if not SNAPSHOT_ID_RE.match(sval):
                failures.append((p, spath, f"snapshot_id {sval!r} does not match {SNAPSHOT_ID_RE.pattern!r}"))

        # image_path checks
        for ipath, ival in iter_field_values(data, "image_path"):
            if not IMAGE_PATH_RE.match(ival):
                failures.append((p, ipath, f"image_path {ival!r} does not match {IMAGE_PATH_RE.pattern!r}"))

    if failures:
        print("[FAIL] examples field scan failed:")
        for p, jpath, msg in failures:
            path_str = "/".join(jpath)
            print(f"  - {p}: {path_str}: {msg}")
        raise SystemExit(1)

    print(f"[OK]   examples scan passed ({len(json_files)} files scanned)")


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

    # --- Extra scan: snapshot_id + image_path across all examples ---
    scan_examples_fields()

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

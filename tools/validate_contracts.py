from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Tuple

import jsonschema
import yaml
from openapi_spec_validator import validate_spec


ROOT = Path(__file__).resolve().parents[1]

# v0.1 canonical patterns (SSOT for snapshot_id/node_id formats)
SNAPSHOT_ID_PATTERN = r"^s-[0-9]{8}-[0-9]{6}-[0-9a-f]{8}$"
NODE_ID_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$"

SNAPSHOT_ID_RE = re.compile(SNAPSHOT_ID_PATTERN)
NODE_ID_RE = re.compile(NODE_ID_PATTERN)


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {p} (line {e.lineno}, col {e.colno}): {e.msg}") from e


def load_yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def load_ssot_patterns() -> dict:
    """
    Load SSOT patterns for v0.1.
    This file is human-facing SSOT; tools enforce that all contracts match it.
    """
    p = ROOT / "hub" / "contracts" / "_ssot" / "patterns.v0.1.json"
    if not p.exists():
        print(f"[FAIL] SSOT patterns missing: {p}")
        raise SystemExit(1)
    return load_json(p)


# -----------------------------
# Dynamic rule: image_path from hub config constants
# -----------------------------
def _load_hub_config_constants() -> tuple[str, str]:
    """
    Load DATA_ROOT and SNAPSHOT_SUBDIR from hub config.py without importing the hub package.
    Falls back to ("data", "snapshots") if not found.
    """
    cfg_path = ROOT / "hub" / "src" / "exuviae_hub" / "infrastructure" / "config.py"
    if not cfg_path.exists():
        return ("data", "snapshots")

    spec = importlib.util.spec_from_file_location("_exuviae_hub_config", cfg_path)
    if spec is None or spec.loader is None:
        return ("data", "snapshots")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore

    data_root = getattr(module, "DATA_ROOT", "data")
    subdir = getattr(module, "SNAPSHOT_SUBDIR", "snapshots")
    return (str(data_root), str(subdir))


def _build_image_path_pattern() -> str:
    """
    Build v0.1 image_path pattern string using hub config constants.
    Expected layout:
      {DATA_ROOT}/{SNAPSHOT_SUBDIR}/YYYY-MM-DD/<node_id>/<snapshot_id>.jpg
    """
    data_root, subdir = _load_hub_config_constants()

    # Normalize (contracts/examples use forward slashes)
    data_root = data_root.strip("/\\")
    subdir = subdir.strip("/\\")
    dr = re.escape(data_root)
    sd = re.escape(subdir)

    return (
        rf"^{dr}/{sd}/[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}/"
        rf"[a-zA-Z0-9][a-zA-Z0-9._-]{{0,63}}/"
        rf"s-[0-9]{{8}}-[0-9]{{6}}-[0-9a-f]{{8}}\.jpg$"
    )


def _build_image_path_re() -> re.Pattern[str]:
    return re.compile(_build_image_path_pattern())


# -----------------------------
# Validators
# -----------------------------
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


def validate_openapi(openapi_path: Path) -> dict:
    spec = load_yaml(openapi_path)
    if not isinstance(spec, dict) or "openapi" not in spec:
        raise ValueError("Not a valid OpenAPI document (missing 'openapi' key)")
    validate_spec(spec)
    print(f"[OK]   validated OpenAPI: {openapi_path}")
    return spec


# -----------------------------
# Scanners for examples
# -----------------------------
def iter_field_values(obj: Any, field_name: str, path: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], str]]:
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
    Scan all example JSON files under hub/node contracts examples and ensure:
    - snapshot_id matches v0.1
    - image_path matches v0.1 (dynamic from hub config)
    - node_id matches v0.1 (if present in examples)
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

    ssot = load_ssot_patterns()
    ssot_node_pat = ssot["properties"]["node_id"]["pattern"]
    ssot_snapshot_pat = ssot["properties"]["snapshot_id"]["pattern"]
    ssot_image_pat = ssot["properties"]["image_path"]["pattern"]

    node_id_re = re.compile(ssot_node_pat)
    snapshot_id_re = re.compile(ssot_snapshot_pat)
    image_path_re = re.compile(ssot_image_pat)

    failures = []

    for p in json_files:
        try:
            data = load_json(p)
        except Exception as e:
            failures.append((p, ("<parse>",), f"JSON parse failed: {e}"))
            continue

        for spath, sval in iter_field_values(data, "snapshot_id"):
            if not snapshot_id_re.match(sval):
                failures.append((p, spath, f"snapshot_id {sval!r} does not match {ssot_snapshot_pat!r}"))

        for ipath, ival in iter_field_values(data, "image_path"):
            if not image_path_re.match(ival):
                failures.append((p, ipath, f"image_path {ival!r} does not match {ssot_image_pat!r}"))

        for npath, nval in iter_field_values(data, "node_id"):
            if not node_id_re.match(nval):
                failures.append((p, npath, f"node_id {nval!r} does not match {ssot_node_pat!r}"))

    if failures:
        print("[FAIL] examples field scan failed:")
        for p, jpath, msg in failures:
            path_str = "/".join(jpath)
            print(f"  - {p}: {path_str}: {msg}")
        raise SystemExit(1)

    print(f"[OK]   examples scan passed ({len(json_files)} files scanned)")


# -----------------------------
# Contract consistency checks
# -----------------------------
def _require_openapi_prop_ref(spec: dict, parent_schema: str, prop_name: str, expected_ref: str):
    try:
        prop = spec["components"]["schemas"][parent_schema]["properties"][prop_name]
    except Exception as e:
        raise KeyError(f"OpenAPI missing components.schemas.{parent_schema}.properties.{prop_name}") from e

    if not (isinstance(prop, dict) and prop.get("$ref") == expected_ref and len(prop) == 1):
        print("[FAIL] OpenAPI property must be $ref-only:")
        print(f"  - schema: {parent_schema}")
        print(f"  - prop  : {prop_name}")
        print(f"  - got   : {prop!r}")
        print(f"  - want  : {{'$ref': {expected_ref!r}}}")
        raise SystemExit(1)

    print(f"[OK]   openapi $ref-only: {parent_schema}.{prop_name}")


def _get_openapi_component_pattern(spec: dict, schema_name: str) -> str:
    try:
        return spec["components"]["schemas"][schema_name]["pattern"]
    except Exception as e:
        raise KeyError(f"OpenAPI missing components.schemas.{schema_name}.pattern") from e

def _get_jsonschema_defs_pattern(schema_path: Path, defs_key: str) -> str:
    schema = load_json(schema_path)
    try:
        return schema["$defs"][defs_key]["pattern"]
    except Exception as e:
        raise KeyError(f"JSON schema missing $defs.{defs_key}.pattern in {schema_path}") from e


def _get_jsonschema_prop_pattern(schema_path: Path, prop_name: str) -> str:
    schema = load_json(schema_path)
    try:
        return schema["properties"][prop_name]["pattern"]
    except Exception as e:
        raise KeyError(f"JSON schema missing properties.{prop_name}.pattern in {schema_path}") from e


def _check_pattern_equal(name: str, left: str, right: str):
    if left != right:
        print(f"[FAIL] pattern mismatch: {name}")
        print(f"  - left : {left!r}")
        print(f"  - right: {right!r}")
        raise SystemExit(1)
    print(f"[OK]   pattern equal: {name}")


def _check_pattern_matches_sample(name: str, pattern: str, sample: str):
    if not re.compile(pattern).match(sample):
        print(f"[FAIL] pattern does not match canonical sample: {name}")
        print(f"  - pattern: {pattern!r}")
        print(f"  - sample : {sample!r}")
        raise SystemExit(1)
    print(f"[OK]   pattern matches sample: {name}")


def check_contract_consistency(spec: dict):
    ssot = load_ssot_patterns()
    ssot_node_pat = ssot["properties"]["node_id"]["pattern"]
    ssot_snapshot_pat = ssot["properties"]["snapshot_id"]["pattern"]
    ssot_image_pat = ssot["properties"]["image_path"]["pattern"]

    # image_path must also match hub config-derived rule
    expected_image_path_pattern = _build_image_path_pattern()
    _check_pattern_equal("ssot.image_path vs hub.config", ssot_image_pat, expected_image_path_pattern)

    # --- OpenAPI components are the public API SSOT; must match human SSOT ---
    openapi_snapshot_pat = _get_openapi_component_pattern(spec, "SnapshotId")
    _check_pattern_equal("openapi.components.SnapshotId", openapi_snapshot_pat, ssot_snapshot_pat)

    openapi_node_pat = _get_openapi_component_pattern(spec, "NodeId")
    _check_pattern_equal("openapi.components.NodeId", openapi_node_pat, ssot_node_pat)

    openapi_image_pat = _get_openapi_component_pattern(spec, "ImagePath")
    _check_pattern_equal("openapi.components.ImagePath", openapi_image_pat, ssot_image_pat)

    # --- WS defs must match SSOT ---
    ws_schema_path = ROOT / "hub" / "contracts" / "ws" / "messages.schema.json"
    ws_snapshot = _get_jsonschema_defs_pattern(ws_schema_path, "SnapshotId")
    _check_pattern_equal("ws.$defs.SnapshotId", ws_snapshot, ssot_snapshot_pat)

    ws_node = _get_jsonschema_defs_pattern(ws_schema_path, "NodeId")
    _check_pattern_equal("ws.$defs.NodeId", ws_node, ssot_node_pat)

    ws_img = _get_jsonschema_defs_pattern(ws_schema_path, "ImagePath")
    _check_pattern_equal("ws.$defs.ImagePath", ws_img, ssot_image_pat)

    # --- Logging defs must match SSOT ---
    log_schema_path = ROOT / "hub" / "contracts" / "logging" / "vision_log_line.schema.json"
    log_snapshot = _get_jsonschema_defs_pattern(log_schema_path, "SnapshotId")
    _check_pattern_equal("logging.$defs.SnapshotId", log_snapshot, ssot_snapshot_pat)

    log_node = _get_jsonschema_defs_pattern(log_schema_path, "NodeId")
    _check_pattern_equal("logging.$defs.NodeId", log_node, ssot_node_pat)

    log_img = _get_jsonschema_defs_pattern(log_schema_path, "ImagePath")
    _check_pattern_equal("logging.$defs.ImagePath", log_img, ssot_image_pat)

    # --- Node config schema node_id must match SSOT ---
    node_cfg = ROOT / "node" / "contracts" / "node" / "node_config.schema.json"
    if not node_cfg.exists():
        print("[FAIL] node config schema missing:", node_cfg)
        raise SystemExit(1)

    node_cfg_node_id = _get_jsonschema_prop_pattern(node_cfg, "node_id")
    _check_pattern_equal("node.node_config.node_id", node_cfg_node_id, ssot_node_pat)

    # --- Enforce $ref-only usage (WS / logging) ---
    ws = load_json(ws_schema_path)
    _scan_require_ref_for_field(ws, "node_id", "#/$defs/NodeId")
    _scan_require_ref_for_field(ws, "snapshot_id", "#/$defs/SnapshotId")
    _scan_require_ref_for_field(ws, "image_path", "#/$defs/ImagePath")

    log = load_json(log_schema_path)
    _scan_require_ref_for_field(log, "node_id", "#/$defs/NodeId")
    _scan_require_ref_for_field(log, "snapshot_id", "#/$defs/SnapshotId")
    _scan_require_ref_for_field(log, "image_path", "#/$defs/ImagePath")

    # --- Enforce $ref-only usage (OpenAPI key properties) ---
    _require_openapi_prop_ref(spec, "CaptureResponse", "snapshot_id", "#/components/schemas/SnapshotId")
    _require_openapi_prop_ref(spec, "SnapshotUploadResponse", "image_path", "#/components/schemas/ImagePath")

    # --- canonical sample checks ---
    snapshot_sample = "s-20260202-173012-4f2a9c10"
    _check_pattern_matches_sample("snapshot_id.v0.1", ssot_snapshot_pat, snapshot_sample)

    node_sample = "cam-01"
    _check_pattern_matches_sample("node_id.v0.1", ssot_node_pat, node_sample)

    data_root, subdir = _load_hub_config_constants()
    data_root = str(data_root).strip("/\\")
    subdir = str(subdir).strip("/\\")
    image_sample = f"{data_root}/{subdir}/2026-02-02/{node_sample}/{snapshot_sample}.jpg"
    _check_pattern_matches_sample("image_path.v0.1", ssot_image_pat, image_sample)




def _scan_require_ref_for_field(schema_obj: Any, field_name: str, expected_ref: str, in_defs: bool = False, path: Tuple[str, ...] = ()):
    """
    Traverse JSON schema object and ensure that any occurrence of a property named field_name
    (outside of $defs) is a dict that equals {"$ref": expected_ref} (allowing extra keys is NOT allowed).
    """
    if isinstance(schema_obj, dict):
        # Track whether we're inside $defs
        if "$defs" in schema_obj:
            # Still traverse others; $defs itself should be excluded from enforcement
            pass

        for k, v in schema_obj.items():
            new_in_defs = in_defs or (k == "$defs")
            new_path = path + (str(k),)

            # Enforce only when not in $defs and this is a properties dict entry
            if (not new_in_defs) and k == field_name and isinstance(v, dict):
                # Must be exactly {"$ref": expected_ref}
                if not (len(v) == 1 and v.get("$ref") == expected_ref):
                    p = "/".join(new_path)
                    print("[FAIL] field must be $ref-only:")
                    print(f"  - field: {field_name}")
                    print(f"  - path : {p}")
                    print(f"  - got  : {v!r}")
                    print(f"  - want : {{'$ref': {expected_ref!r}}}")
                    raise SystemExit(1)

            _scan_require_ref_for_field(v, field_name, expected_ref, new_in_defs, new_path)

    elif isinstance(schema_obj, list):
        for i, item in enumerate(schema_obj):
            _scan_require_ref_for_field(item, field_name, expected_ref, in_defs, path + (f"[{i}]",))


# -----------------------------
# Main
# -----------------------------
def main():
    # --- OpenAPI ---
    openapi = ROOT / "hub" / "contracts" / "http" / "openapi.v0.yaml"
    if not openapi.exists():
        print(f"[FAIL] missing: {openapi}")
        return 1
    spec = validate_openapi(openapi)

    # --- Hub contracts: schema + examples ---
    ws_schema = ROOT / "hub" / "contracts" / "ws" / "messages.schema.json"
    ws_examples = ROOT / "hub" / "contracts" / "ws" / "examples"
    validate_jsonschema_examples(ws_schema, ws_examples)

    cap_schema = ROOT / "hub" / "contracts" / "capabilities" / "node_register.schema.json"
    cap_examples = ROOT / "hub" / "contracts" / "capabilities" / "examples"
    validate_jsonschema_examples(cap_schema, cap_examples)

    log_schema = ROOT / "hub" / "contracts" / "logging" / "vision_log_line.schema.json"
    log_examples = ROOT / "hub" / "contracts" / "logging" / "examples"
    validate_jsonschema_examples(log_schema, log_examples)

    # --- Node contracts (optional but you said it's added) ---
    node_cfg_schema = ROOT / "node" / "contracts" / "node" / "node_config.schema.json"
    node_cfg_examples = ROOT / "node" / "contracts" / "node" / "examples"
    if node_cfg_schema.exists():
        validate_jsonschema_examples(node_cfg_schema, node_cfg_examples)
    else:
        print("[WARN] node config schema missing (skipped):", node_cfg_schema)

    # --- Extra scan: snapshot_id + image_path + node_id across all examples ---
    scan_examples_fields()

    # --- Cross-contract consistency checks (patterns must not drift) ---
    check_contract_consistency(spec)

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

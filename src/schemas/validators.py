from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"


def _schema_path(schema_name: str) -> Path:
    return SCHEMA_DIR / schema_name


def load_schema(schema_name: str) -> dict:
    return json.loads(_schema_path(schema_name).read_text(encoding="utf-8"))


def validate_json(data: Any, schema_name: str) -> dict:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda item: list(item.path))
    return {
        "schema_valid": not errors,
        "errors": [
            {
                "path": ".".join(str(part) for part in error.path),
                "message": error.message,
            }
            for error in errors
        ],
    }


def validate_or_raise(data: Any, schema_name: str) -> None:
    result = validate_json(data, schema_name)
    if not result["schema_valid"]:
        messages = "; ".join(error["message"] for error in result["errors"])
        raise ValueError(f"{schema_name} validation failed: {messages}")


def canonical_evidence_hash(bundle: dict) -> str:
    normalized = copy.deepcopy(bundle)
    audit = normalized.get("audit")
    if isinstance(audit, dict):
        audit["evidence_hash_sha256"] = None
    payload = json.dumps(normalized, sort_keys=True, default=str, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

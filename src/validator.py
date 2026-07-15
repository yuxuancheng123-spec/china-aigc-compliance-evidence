from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_instance(instance: Any, schema_path: Path) -> dict:
    validator = Draft202012Validator(load_schema(schema_path))
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    return {
        "valid": not errors,
        "errors": [
            {
                "path": ".".join(str(part) for part in error.path),
                "message": error.message,
            }
            for error in errors
        ],
    }


def validate_legal_norm(norm: dict) -> dict:
    return validate_instance(norm, ROOT / "schema" / "legal-norm-schema.json")


def validate_control(control: dict) -> dict:
    return validate_instance(control, ROOT / "schema" / "control-schema.json")


def validate_control_mapping(path: Path | None = None) -> dict:
    mapping_path = path or ROOT / "mappings" / "clause-to-control.yml"
    controls = load_yaml(mapping_path)
    results = []
    for control in controls:
        result = validate_control(control)
        traceability = control.get("traceability", {})
        has_traceability = bool(
            control.get("norm_id")
            and traceability.get("source_document")
            and traceability.get("article")
            and traceability.get("legal_review_status")
            and control.get("test", {}).get("expression")
            and control.get("automation_level")
        )
        if not has_traceability:
            result["valid"] = False
            result["errors"].append(
                {
                    "path": "traceability",
                    "message": "control must include norm_id, source, article, test expression, automation level, and review status",
                }
            )
        results.append({"control_id": control.get("control_id"), **result})
    return {
        "valid": all(item["valid"] for item in results),
        "controls_checked": len(results),
        "results": results,
    }


def validate_example_norms() -> dict:
    results = []
    for path in sorted((ROOT / "examples").glob("*-control.yml")):
        norm = load_yaml(path)
        result = validate_legal_norm(norm)
        results.append({"path": str(path.relative_to(ROOT)), **result})
    return {
        "valid": all(item["valid"] for item in results),
        "examples_checked": len(results),
        "results": results,
    }


if __name__ == "__main__":
    mapping = validate_control_mapping()
    examples = validate_example_norms()
    print(json.dumps({"mapping": mapping, "examples": examples}, indent=2))

from __future__ import annotations

import ast
import csv
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


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def _expression_names(expression: str) -> set[str]:
    expression = expression.replace(" true", " True").replace(" false", " False").replace(" null", " None")
    if expression.startswith("true"):
        expression = "True" + expression[4:]
    if expression.startswith("false"):
        expression = "False" + expression[5:]
    if expression.startswith("null"):
        expression = "None" + expression[4:]
    tree = ast.parse(expression, mode="eval")
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id not in {"True", "False", "None"}}


def _row_by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def _append_error(errors: list[dict[str, str]], item_id: str, message: str, path: str = "cross_file") -> None:
    errors.append({"id": item_id, "path": path, "message": message})


def validate_control_mapping(path: Path | None = None) -> dict:
    mapping_path = path or ROOT / "mappings" / "clause-to-control.yml"
    controls = load_yaml(mapping_path)
    results = []
    for control in controls:
        result = validate_control(control)
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


def validate_cross_file_integrity() -> dict:
    controls = load_yaml(ROOT / "mappings" / "clause-to-control.yml")
    source_index = _row_by(load_csv(ROOT / "legal-corpus" / "source-index.csv"), "source_id")
    decompositions = _row_by(load_csv(ROOT / "annotations" / "clause-decomposition.csv"), "norm_id")
    traceability_rows = load_csv(ROOT / "mappings" / "traceability-matrix.csv")
    traceability_by_control = _row_by(traceability_rows, "control_id")
    examples = {
        yaml.safe_load(path.read_text(encoding="utf-8"))["norm_id"]: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "examples").glob("*-control.yml"))
    }

    errors: list[dict[str, str]] = []
    seen_control_ids: set[str] = set()
    objective_by_norm: dict[str, str] = {}
    expression_by_norm: dict[str, str] = {}

    for control in controls:
        control_id = control["control_id"]
        norm_id = control["norm_id"]
        trace = control["traceability"]
        review = control["review"]

        if control_id in seen_control_ids:
            _append_error(errors, control_id, "control_id is duplicated")
        seen_control_ids.add(control_id)

        if norm_id not in decompositions:
            _append_error(errors, control_id, "norm_id is missing from clause-decomposition.csv")
            continue
        if control_id not in traceability_by_control:
            _append_error(errors, control_id, "control_id is missing from traceability-matrix.csv")
            continue
        if trace["source_id"] not in source_index:
            _append_error(errors, control_id, "source_id is missing from legal-corpus/source-index.csv")
            continue

        source = source_index[trace["source_id"]]
        decomposition = decompositions[norm_id]
        trace_row = traceability_by_control[control_id]

        for field in ("document_title_zh", "document_title_en", "effective_date"):
            values = {trace[field], source[field], decomposition[field], trace_row[field]}
            if len(values) != 1:
                _append_error(errors, control_id, f"{field} is inconsistent across files")
        if trace["article"] != decomposition["article"] or trace["article"] != trace_row["article"]:
            _append_error(errors, control_id, "article is inconsistent across mapping, decomposition, and traceability matrix")
        if trace["source_url"] != source["source_url"] or trace["source_url"] != trace_row["source_url"]:
            _append_error(errors, control_id, "source_url is inconsistent across files")
        if control["automation_level"] != decomposition["automation_level"] or control["automation_level"] != trace_row["automation_level"]:
            _append_error(errors, control_id, "automation_level is inconsistent across files")
        if review["interpretation_version"] != trace["interpretation_version"] or review["interpretation_version"] != decomposition["interpretation_version"] or review["interpretation_version"] != trace_row["interpretation_version"]:
            _append_error(errors, control_id, "interpretation_version is inconsistent across files")

        declared_fields = set(control["evidence"]["required_fields"])
        declared_fields.update(control.get("applicability", {}).get("conditions", {}).keys())
        declared_fields.update(control.get("exception_path", {}).get("required_fields", []))
        undeclared = _expression_names(control["test"]["expression"]) - declared_fields
        if undeclared:
            _append_error(errors, control_id, f"test expression references undeclared fields: {', '.join(sorted(undeclared))}")
        if control.get("exception_path"):
            undeclared_exception = _expression_names(control["exception_path"]["expression"]) - declared_fields
            if undeclared_exception:
                _append_error(errors, control_id, f"exception expression references undeclared fields: {', '.join(sorted(undeclared_exception))}")

        if norm_id in examples:
            example_fields = set(examples[norm_id]["evidence"]["required_fields"])
            if example_fields != set(control["evidence"]["required_fields"]):
                _append_error(errors, control_id, "required evidence fields differ from example norm")

        if review["legal_expert_review_status"] == "reviewed" and (not review.get("reviewer_name") or not review.get("review_date")):
            _append_error(errors, control_id, "legal expert reviewed status requires reviewer identity and review date")

        if not trace.get("source_url"):
            _append_error(errors, control_id, "control lacks official source URL")

        if norm_id in objective_by_norm and objective_by_norm[norm_id] != control["control_objective"]:
            if norm_id not in {"CN-AIGC-LABEL-001"}:
                _append_error(errors, control_id, "same norm has conflicting control objective")
        objective_by_norm.setdefault(norm_id, control["control_objective"])

        if norm_id in expression_by_norm and expression_by_norm[norm_id] != control["test"]["expression"]:
            if norm_id not in {"CN-AIGC-LABEL-001"}:
                _append_error(errors, control_id, "same norm has conflicting test expression")
        expression_by_norm.setdefault(norm_id, control["test"]["expression"])

    return {
        "valid": not errors,
        "checks": [
            "norm_id presence in clause decomposition and traceability matrix",
            "source_id presence in source index",
            "document title, article number, effective date, and URL consistency",
            "unique and traceable control_id",
            "test-expression variables declared in evidence, applicability, or exception fields",
            "required evidence fields aligned with example norms where examples exist",
            "automation_level consistency",
            "interpretation_version consistency",
            "legal expert reviewed status requires reviewer identity and date",
            "official source URL present",
            "conflicting objective or expression detection",
        ],
        "errors": errors,
    }


def validate_legal_source_metadata() -> dict:
    errors: list[dict[str, str]] = []
    for path in sorted((ROOT / "examples").glob("*-control.yml")):
        norm = load_yaml(path)
        source = norm["source"]
        if not source.get("source_text_zh"):
            _append_error(errors, str(path), "source_text_zh must not be empty", "source")
        if source.get("source_text_zh") == source.get("working_translation_en"):
            _append_error(errors, str(path), "source_text_zh must not equal working_translation_en", "source")
        if not source.get("source_url"):
            _append_error(errors, str(path), "source_url must not be empty", "source")
        if not source.get("document_title_zh") or not source.get("document_title_en"):
            _append_error(errors, str(path), "Chinese and English document titles are required", "source")
    return {"valid": not errors, "errors": errors}


def validate_repository() -> dict:
    mapping = validate_control_mapping()
    examples = validate_example_norms()
    cross_file = validate_cross_file_integrity()
    legal_source = validate_legal_source_metadata()
    schema_valid = mapping["valid"] and examples["valid"]
    return {
        "schema_valid": schema_valid,
        "cross_file_valid": cross_file["valid"],
        "legal_source_metadata_complete": legal_source["valid"],
        "mapping": mapping,
        "examples": examples,
        "cross_file": cross_file,
        "legal_source_metadata": legal_source,
    }


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, ensure_ascii=False))

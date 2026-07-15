from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DERIVATION_TYPES = {"direct_legal_requirement", "derived_organizational_control", "technical_implementation_control"}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_instance(instance: Any, schema_path: Path) -> dict:
    errors = sorted(Draft202012Validator(load_schema(schema_path)).iter_errors(instance), key=lambda error: list(error.path))
    return {"valid": not errors, "errors": [{"path": ".".join(str(part) for part in error.path), "message": error.message} for error in errors]}


def validate_legal_norm(norm: dict) -> dict:
    return validate_instance(norm, ROOT / "schema" / "legal-norm-schema.json")


def validate_control(control: dict) -> dict:
    return validate_instance(control, ROOT / "schema" / "control-schema.json")


def load_norm_artifacts() -> dict[str, dict]:
    norms: dict[str, dict] = {}
    for path in sorted((ROOT / "norms").glob("*.yml")):
        norm = load_yaml(path)
        norms[norm["norm_id"]] = norm
    return norms


def _normalise_expression(expression: str) -> str:
    for source, replacement in (("true", "True"), ("false", "False"), ("null", "None")):
        expression = expression.replace(f" {source}", f" {replacement}")
        if expression.startswith(source):
            expression = replacement + expression[len(source) :]
    return expression


def _expression_names(expression: str) -> set[str]:
    tree = ast.parse(_normalise_expression(expression), mode="eval")
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id not in {"True", "False", "None"}}


def _row_by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def _append(items: list[dict[str, str]], item_id: str, message: str, path: str = "cross_file") -> None:
    items.append({"id": item_id, "path": path, "message": message})


def validate_control_mapping(path: Path | None = None) -> dict:
    controls = load_yaml(path or ROOT / "mappings" / "clause-to-control.yml")
    results = [{"control_id": control.get("control_id"), **validate_control(control)} for control in controls]
    return {"valid": all(item["valid"] for item in results), "controls_checked": len(results), "results": results}


def validate_norm_artifacts() -> dict:
    results = []
    for path in sorted((ROOT / "norms").glob("*.yml")):
        result = validate_legal_norm(load_yaml(path))
        results.append({"path": str(path.relative_to(ROOT)), **result})
    return {"valid": bool(results) and all(item["valid"] for item in results), "norms_checked": len(results), "results": results}


def validate_example_norms() -> dict:
    results = []
    for path in sorted((ROOT / "examples").glob("*-control.yml")):
        result = validate_legal_norm(load_yaml(path))
        results.append({"path": str(path.relative_to(ROOT)), **result})
    return {"valid": all(item["valid"] for item in results), "examples_checked": len(results), "results": results}


def validate_cross_file_integrity() -> dict:
    controls = load_yaml(ROOT / "mappings" / "clause-to-control.yml")
    norms = load_norm_artifacts()
    source_index = _row_by(load_csv(ROOT / "legal-corpus" / "source-index.csv"), "source_id")
    decompositions = _row_by(load_csv(ROOT / "annotations" / "clause-decomposition.csv"), "norm_id")
    traceability_rows = load_csv(ROOT / "mappings" / "traceability-matrix.csv")
    traceability_by_control = _row_by(traceability_rows, "control_id")
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    referenced_norms: set[str] = set()
    seen_control_ids: set[str] = set()
    controls_by_norm: dict[str, list[dict]] = {}

    for control in controls:
        control_id, norm_id = control["control_id"], control["norm_id"]
        referenced_norms.add(norm_id)
        controls_by_norm.setdefault(norm_id, []).append(control)
        if control_id in seen_control_ids:
            _append(errors, control_id, "control_id is duplicated")
        seen_control_ids.add(control_id)
        if control.get("control_derivation_type") not in DERIVATION_TYPES:
            _append(errors, control_id, "control_derivation_type is invalid")
        if not control.get("control_component"):
            _append(errors, control_id, "control_component is required")
        if norm_id not in norms:
            _append(errors, control_id, "mapping references a missing norm artifact")
            continue
        if norm_id not in decompositions:
            _append(errors, control_id, "norm_id is missing from clause-decomposition.csv")
        if control_id not in traceability_by_control:
            _append(errors, control_id, "control_id is missing from traceability-matrix.csv")
        trace, norm = control["traceability"], norms[norm_id]
        source = norm["source"]
        if trace["source_id"] not in source_index:
            _append(errors, control_id, "source_id is missing from legal-corpus/source-index.csv")
            continue
        index = source_index[trace["source_id"]]
        decomposition = decompositions.get(norm_id)
        row = traceability_by_control.get(control_id)
        for field in ("source_id", "document_title_zh", "document_title_en", "article", "effective_date", "source_url", "source_url_specificity"):
            expected = source.get(field)
            if trace.get(field) != expected:
                _append(errors, control_id, f"{field} is inconsistent between mapping and norm artifact")
            if index.get(field) not in {None, ""} and index.get(field) != expected:
                _append(errors, control_id, f"{field} is inconsistent between norm artifact and source index")
            if decomposition and field in decomposition and decomposition[field] and decomposition[field] != expected:
                _append(errors, control_id, f"{field} is inconsistent between norm artifact and clause decomposition")
            if row and field in row and row[field] and row[field] != expected:
                _append(errors, control_id, f"{field} is inconsistent between norm artifact and traceability matrix")
        if control["automation_level"] != norm["interpretation"]["automation_level"]:
            _append(errors, control_id, "automation_level is inconsistent between mapping and norm artifact")
        if control["review"]["interpretation_version"] != norm["review"]["interpretation_version"] or trace["interpretation_version"] != norm["review"]["interpretation_version"]:
            _append(errors, control_id, "interpretation_version is inconsistent between mapping and norm artifact")
        if control["review"]["legal_expert_review_status"] == "reviewed" and (not control["review"].get("reviewer_name") or not control["review"].get("review_date")):
            _append(errors, control_id, "legal expert reviewed status requires reviewer identity and review date")
        if trace["source_url_specificity"] == "institution_homepage":
            _append(warnings, control_id, "source URL uses low-specificity institution_homepage")
        declared = set(control["evidence"]["required_fields"])
        declared.update(control.get("applicability", {}).get("conditions", {}).keys())
        declared.update(control.get("applicability", {}).get("human_confirmed_fields", []))
        declared.update(control.get("exception_path", {}).get("required_fields", []))
        for expression_name, expression in [("test", control["test"]["expression"]), ("exception", control.get("exception_path", {}).get("expression"))]:
            if expression:
                undeclared = _expression_names(expression) - declared
                if undeclared:
                    _append(errors, control_id, f"{expression_name} expression references undeclared fields: {', '.join(sorted(undeclared))}")
        if control.get("exception_path", {}).get("outcome") == "pass" and not control["exception_path"].get("control_scope"):
            _append(errors, control_id, "pass exception path must declare control_scope")
        if control.get("applicability", {}).get("human_confirmed_fields") and not isinstance(control.get("applicability", {}).get("human_confirmed_fields"), list):
            _append(errors, control_id, "human_confirmed_fields must declare confirmation requirements")
        if control["control_derivation_type"] == "direct_legal_requirement" and any(word in control["control_objective"].lower() for word in ("retain consent", "organizational assurance")):
            _append(errors, control_id, "direct legal requirement appears to contain an unlabelled derived assurance duty")

    for norm_id in norms:
        if norm_id not in referenced_norms:
            _append(errors, norm_id, "norm artifact is orphaned and has no referencing control", "norms")
    for norm_id, norm_controls in controls_by_norm.items():
        components = [control["control_component"] for control in norm_controls]
        if len(components) != len(set(components)):
            _append(errors, norm_id, "multiple controls for one norm must have distinct control_component values", "mapping")

    return {
        "valid": not errors,
        "checks": [
            "complete norm artifact coverage", "source, article, date, URL, and specificity consistency",
            "automation and interpretation-version consistency", "expression variable declarations",
            "control derivation and component semantics", "human-confirmation declarations",
            "scoped pass exceptions", "orphan norm detection", "low-specificity source warnings",
        ],
        "errors": errors,
        "warnings": warnings,
    }


def validate_legal_source_metadata() -> dict:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for norm_id, norm in load_norm_artifacts().items():
        source = norm["source"]
        if not source.get("source_text_zh"):
            _append(errors, norm_id, "source_text_zh must not be empty", "source")
        if source.get("source_text_zh") == source.get("working_translation_en"):
            _append(errors, norm_id, "source_text_zh must not equal working_translation_en", "source")
        if not source.get("source_url") or not source.get("document_title_zh") or not source.get("document_title_en"):
            _append(errors, norm_id, "source URL and Chinese and English titles are required", "source")
        if source.get("source_url_specificity") == "institution_homepage":
            _append(warnings, norm_id, "source URL uses low-specificity institution_homepage", "source")
    return {"valid": not errors, "errors": errors, "warnings": warnings, "notice": "This check confirms required source metadata fields are present and internally consistent. It does not independently verify that the stored text is identical to the current official source."}


def validate_repository() -> dict:
    mapping = validate_control_mapping()
    norms = validate_norm_artifacts()
    examples = validate_example_norms()
    cross_file = validate_cross_file_integrity()
    legal_source = validate_legal_source_metadata()
    return {
        "schema_valid": mapping["valid"] and norms["valid"] and examples["valid"],
        "cross_file_valid": cross_file["valid"],
        "legal_source_metadata_fields_complete": legal_source["valid"],
        "legal_source_metadata_notice": legal_source["notice"],
        "mapping": mapping, "norms": norms, "examples": examples,
        "cross_file": cross_file, "legal_source_metadata": legal_source,
    }


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, ensure_ascii=False))

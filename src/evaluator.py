from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import yaml

from src.validator import validate_runtime_evidence


ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = {"pass", "fail", "review", "not_applicable"}


class UnsafeExpressionError(ValueError):
    pass


def load_controls(path: Path | None = None) -> list[dict]:
    mapping_path = path or ROOT / "mappings" / "clause-to-control.yml"
    return yaml.safe_load(mapping_path.read_text(encoding="utf-8"))


def _normalise_expression(expression: str) -> str:
    for source, replacement in (("true", "True"), ("false", "False"), ("null", "None")):
        expression = expression.replace(f" {source}", f" {replacement}")
        if expression.startswith(source):
            expression = replacement + expression[len(source) :]
    return expression


def _safe_eval(expression: str, evidence: dict[str, Any]) -> bool:
    tree = ast.parse(_normalise_expression(expression), mode="eval")
    allowed_nodes = (
        ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
        ast.Compare, ast.Eq, ast.NotEq, ast.GtE, ast.Gt, ast.LtE, ast.Lt,
        ast.Is, ast.IsNot, ast.Name, ast.Load, ast.Constant, ast.List,
        ast.Tuple, ast.In, ast.NotIn,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise UnsafeExpressionError(f"Unsupported expression node: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in evidence:
            raise KeyError(node.id)
    return bool(eval(compile(tree, "<control-expression>", "eval"), {"__builtins__": {}}, evidence))


def _base_result(
    control: dict,
    status: str,
    message: str,
    *,
    machine_result: str | None = None,
    requires_human_confirmation: bool = False,
    review_reason: str | None = None,
    confirmations_checked: list[str] | None = None,
    human_review_key: str | None = None,
    human_review_completed: bool = False,
    scope_result: dict[str, str] | None = None,
) -> dict:
    return {
        "control_id": control["control_id"],
        "norm_id": control["norm_id"],
        "status": status,
        "final_status": status,
        "machine_result": machine_result or status,
        "automation_level": control["automation_level"],
        "requires_human_confirmation": requires_human_confirmation,
        "human_confirmations_checked": confirmations_checked or [],
        "human_review_key": human_review_key,
        "human_review_completed": human_review_completed,
        "review_reason": review_reason,
        "scope_result": scope_result,
        "message": message,
    }


def _conditions_apply(control: dict, evidence: dict[str, Any]) -> str:
    human_fields = set(control.get("applicability", {}).get("human_confirmed_fields", []))
    for field, expected in control.get("applicability", {}).get("conditions", {}).items():
        if field in human_fields:
            continue
        if field not in evidence:
            return "review"
        if evidence[field] != expected:
            return "not_applicable"
    return "applicable"


def _check_human_confirmations(control: dict, evidence: dict[str, Any]) -> tuple[list[str], str | None]:
    fields = control.get("applicability", {}).get("human_confirmed_fields", [])
    confirmations = evidence.get("human_confirmations")
    checked: list[str] = list(fields)
    if not fields:
        return checked, None
    if not isinstance(confirmations, dict):
        return checked, "human confirmation records are missing"
    for field in fields:
        record = confirmations.get(field)
        if not isinstance(record, dict):
            return checked, f"human confirmation record is missing for {field}"
        missing = [key for key in ("confirmed", "value", "reviewer_role", "reviewed_at") if key not in record]
        if missing:
            return checked, f"human confirmation for {field} is incomplete: {', '.join(missing)}"
        if record["confirmed"] is not True:
            return checked, f"human confirmation for {field} is not complete"
        if field not in evidence:
            return checked, f"business evidence is missing human-confirmed field {field}"
        if record["value"] != evidence[field]:
            return checked, f"human confirmation value conflicts with business evidence for {field}"
    return checked, None


def _human_review(control: dict, evidence: dict[str, Any]) -> tuple[str | None, dict | None]:
    key = control.get("required_human_review", {}).get("review_key")
    if not key:
        return None, None
    reviews = evidence.get("human_reviews")
    record = reviews.get(key) if isinstance(reviews, dict) else None
    if record is None and key == "general":
        record = evidence.get("human_review")
    return key, record if isinstance(record, dict) else None


def _review_result(control: dict, evidence: dict[str, Any], machine_result: str, confirmations: list[str]) -> dict:
    review_key, review = _human_review(control, evidence)
    if not review or review.get("completed") is not True:
        return _base_result(
            control, "review", control["outcomes"]["review"], machine_result=machine_result,
            requires_human_confirmation=True, confirmations_checked=confirmations,
            human_review_key=review_key, review_reason=f"required human review '{review_key}' has not been completed",
        )
    result = review.get("result")
    if result not in {"pass", "fail"}:
        return _base_result(
            control, "review", control["outcomes"]["review"], machine_result=machine_result,
            requires_human_confirmation=True, confirmations_checked=confirmations,
            human_review_key=review_key, human_review_completed=True,
            review_reason=f"required human review '{review_key}' has no pass/fail conclusion",
        )
    return _base_result(
        control, result, control["outcomes"][result], machine_result=machine_result,
        confirmations_checked=confirmations, human_review_key=review_key, human_review_completed=True,
    )


def _exception_applies(control: dict, evidence: dict[str, Any], confirmations: list[str]) -> dict | None:
    exception = control.get("exception_path")
    if not exception or any(field not in evidence for field in exception["required_fields"]):
        return None
    try:
        if _safe_eval(exception["expression"], evidence):
            status = exception.get("outcome", "pass")
            return _base_result(
                control, status, exception["message"], machine_result="pass",
                confirmations_checked=confirmations,
                scope_result={"scope": exception["control_scope"], "status": status},
            )
    except KeyError:
        return None
    return None


def evaluate_control(control: dict, evidence: dict[str, Any]) -> dict:
    applicability = _conditions_apply(control, evidence)
    if applicability != "applicable":
        return _base_result(control, applicability, control["outcomes"][applicability])

    confirmations, confirmation_problem = _check_human_confirmations(control, evidence)
    if confirmation_problem:
        return _base_result(
            control, "review", control["outcomes"]["review"], machine_result="review",
            requires_human_confirmation=True, confirmations_checked=confirmations,
            review_reason=confirmation_problem,
        )

    missing = [field for field in control["evidence"]["required_fields"] if field not in evidence]
    if missing:
        exception_result = _exception_applies(control, evidence, confirmations)
        if exception_result:
            return exception_result
        return _base_result(
            control, "review", f"Missing required evidence fields: {', '.join(missing)}", machine_result="review",
            confirmations_checked=confirmations, review_reason="missing required evidence",
        )

    try:
        passed = _safe_eval(control["test"]["expression"], evidence)
    except KeyError as exc:
        return _base_result(
            control, "review", f"Expression references missing evidence field: {exc.args[0]}", machine_result="review",
            confirmations_checked=confirmations, review_reason="expression references missing evidence field",
        )

    if not passed:
        exception_result = _exception_applies(control, evidence, confirmations)
        if exception_result:
            return exception_result
        return _base_result(control, "fail", control["outcomes"]["fail"], machine_result="fail", confirmations_checked=confirmations)

    if control.get("automation_profile", {}).get("final_decision") == "automated_after_confirmation":
        return _base_result(control, "pass", control["outcomes"]["pass"], machine_result="pass", confirmations_checked=confirmations)

    if control["automation_level"] in {"partially_automatable", "human_review_required"}:
        return _review_result(control, evidence, "pass" if control["automation_level"] == "partially_automatable" else "review", confirmations)

    return _base_result(control, "pass", control["outcomes"]["pass"], machine_result="pass", confirmations_checked=confirmations)


def evaluate_case(evidence: dict[str, Any], controls: list[dict] | None = None) -> list[dict]:
    return [evaluate_control(control, evidence) for control in (controls or load_controls())]


def evaluate_validation_cases(path: Path | None = None, controls: list[dict] | None = None) -> dict:
    cases_path = path or ROOT / "examples" / "validation-cases.yml"
    cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    controls_by_id = {control["control_id"]: control for control in (controls or load_controls())}
    results = []
    for case in cases:
        runtime_validation = validate_runtime_evidence(case["evidence"])
        if not runtime_validation["valid"]:
            results.append({"case_id": case["case_id"], "expected": case.get("expected", {}), "actual": "validation_error", "validation_errors": runtime_validation["errors"], "passed": False})
            continue
        actual = {control_id: evaluate_control(controls_by_id[control_id], case["evidence"])["status"] for control_id in case.get("expected", {})}
        results.append({"case_id": case["case_id"], "expected": case.get("expected", {}), "actual": actual, "passed": actual == case.get("expected", {})})
    return {"cases_checked": len(results), "passed": sum(item["passed"] for item in results), "failed": sum(not item["passed"] for item in results), "results": results}


if __name__ == "__main__":
    print(evaluate_validation_cases())

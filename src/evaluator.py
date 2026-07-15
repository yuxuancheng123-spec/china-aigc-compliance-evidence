from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = {"pass", "fail", "review", "not_applicable"}


class UnsafeExpressionError(ValueError):
    pass


def load_controls(path: Path | None = None) -> list[dict]:
    mapping_path = path or ROOT / "mappings" / "clause-to-control.yml"
    return yaml.safe_load(mapping_path.read_text(encoding="utf-8"))


def _safe_eval(expression: str, evidence: dict[str, Any]) -> bool:
    expression = expression.replace(" true", " True").replace(" false", " False").replace(" null", " None")
    if expression.startswith("true"):
        expression = "True" + expression[4:]
    if expression.startswith("false"):
        expression = "False" + expression[5:]
    if expression.startswith("null"):
        expression = "None" + expression[4:]
    tree = ast.parse(expression, mode="eval")
    allowed_nodes = (
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.UnaryOp,
        ast.Not,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.GtE,
        ast.Gt,
        ast.LtE,
        ast.Lt,
        ast.Is,
        ast.IsNot,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.List,
        ast.Tuple,
        ast.In,
        ast.NotIn,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise UnsafeExpressionError(f"Unsupported expression node: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in evidence:
            raise KeyError(node.id)
    return bool(eval(compile(tree, "<control-expression>", "eval"), {"__builtins__": {}}, evidence))


def _conditions_apply(conditions: dict[str, Any], evidence: dict[str, Any]) -> str:
    for field, expected in conditions.items():
        if field not in evidence:
            return "review"
        if evidence[field] != expected:
            return "not_applicable"
    return "applicable"


def _base_result(
    control: dict,
    status: str,
    message: str,
    machine_result: str | None = None,
    requires_human_confirmation: bool = False,
    review_reason: str | None = None,
) -> dict:
    return {
        "control_id": control["control_id"],
        "norm_id": control["norm_id"],
        "status": status,
        "final_status": status,
        "machine_result": machine_result or status,
        "automation_level": control["automation_level"],
        "requires_human_confirmation": requires_human_confirmation,
        "review_reason": review_reason,
        "message": message,
    }


def _exception_applies(control: dict, evidence: dict[str, Any]) -> dict | None:
    exception = control.get("exception_path")
    if not exception:
        return None
    missing = [field for field in exception.get("required_fields", []) if field not in evidence]
    if missing:
        return None
    try:
        if _safe_eval(exception["expression"], evidence):
            status = exception.get("outcome", "pass")
            return _base_result(
                control,
                status,
                exception.get("message", control["outcomes"][status]),
                machine_result="pass",
            )
    except KeyError:
        return None
    return None


def evaluate_control(control: dict, evidence: dict[str, Any]) -> dict:
    applicability = _conditions_apply(control.get("applicability", {}).get("conditions", {}), evidence)
    if applicability != "applicable":
        return _base_result(control, applicability, control["outcomes"][applicability])

    missing = [field for field in control["evidence"]["required_fields"] if field not in evidence]
    if missing:
        exception_result = _exception_applies(control, evidence)
        if exception_result:
            return exception_result
        return _base_result(
            control,
            "review",
            f"Missing required evidence fields: {', '.join(missing)}",
            machine_result="review",
            review_reason="missing required evidence",
        )

    if control["automation_level"] == "human_review_required":
        if evidence.get("human_review_completed") is True or evidence.get("label_prominence_review_completed") is True or evidence.get("content_safety_human_review_completed") is True or evidence.get("biometric_classification_reviewed") is True:
            human_result = evidence.get("human_review_result")
            if human_result in {"pass", "fail"}:
                return _base_result(control, human_result, control["outcomes"][human_result], machine_result="review")
        return _base_result(
            control,
            "review",
            control["outcomes"]["review"],
            machine_result="review",
            requires_human_confirmation=True,
            review_reason="human review required",
        )

    try:
        passed = _safe_eval(control["test"]["expression"], evidence)
    except KeyError as exc:
        return _base_result(
            control,
            "review",
            f"Expression references missing evidence field: {exc.args[0]}",
            machine_result="review",
            review_reason="expression references missing evidence field",
        )

    if not passed:
        exception_result = _exception_applies(control, evidence)
        if exception_result:
            return exception_result
        return _base_result(control, "fail", control["outcomes"]["fail"], machine_result="fail")

    if control["automation_level"] == "partially_automatable":
        if evidence.get("human_review_completed") is True and evidence.get("human_review_result") in {"pass", "fail"}:
            human_status = evidence["human_review_result"]
            return _base_result(control, human_status, control["outcomes"][human_status], machine_result="pass")
        return _base_result(
            control,
            "review",
            control["outcomes"]["review"],
            machine_result="pass",
            requires_human_confirmation=True,
            review_reason="machine-check passed but human confirmation is still required",
        )

    return _base_result(control, "pass", control["outcomes"]["pass"], machine_result="pass")


def evaluate_case(evidence: dict[str, Any], controls: list[dict] | None = None) -> list[dict]:
    return [evaluate_control(control, evidence) for control in (controls or load_controls())]


def evaluate_validation_cases(path: Path | None = None, controls: list[dict] | None = None) -> dict:
    cases_path = path or ROOT / "examples" / "validation-cases.yml"
    cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    controls_by_id = {control["control_id"]: control for control in (controls or load_controls())}
    results = []
    for case in cases:
        actual = {}
        for control_id in case.get("expected", {}):
            actual[control_id] = evaluate_control(controls_by_id[control_id], case["evidence"])["status"]
        results.append(
            {
                "case_id": case["case_id"],
                "expected": case.get("expected", {}),
                "actual": actual,
                "passed": actual == case.get("expected", {}),
            }
        )
    return {
        "cases_checked": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "results": results,
    }


if __name__ == "__main__":
    print(evaluate_validation_cases())

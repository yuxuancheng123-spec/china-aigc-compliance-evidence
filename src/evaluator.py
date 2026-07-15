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
    expression = expression.replace(" true", " True").replace(" false", " False")
    if expression.startswith("true"):
        expression = "True" + expression[4:]
    if expression.startswith("false"):
        expression = "False" + expression[5:]
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


def evaluate_control(control: dict, evidence: dict[str, Any]) -> dict:
    applicability = _conditions_apply(control.get("applicability", {}).get("conditions", {}), evidence)
    if applicability != "applicable":
        return {
            "control_id": control["control_id"],
            "norm_id": control["norm_id"],
            "status": applicability,
            "automation_level": control["automation_level"],
            "message": control["outcomes"][applicability],
        }

    missing = [field for field in control["evidence"]["required_fields"] if field not in evidence]
    if missing:
        return {
            "control_id": control["control_id"],
            "norm_id": control["norm_id"],
            "status": "review",
            "automation_level": control["automation_level"],
            "message": f"Missing required evidence fields: {', '.join(missing)}",
        }

    if control["automation_level"] == "human_review_required":
        return {
            "control_id": control["control_id"],
            "norm_id": control["norm_id"],
            "status": "review",
            "automation_level": control["automation_level"],
            "message": control["outcomes"]["review"],
        }

    try:
        passed = _safe_eval(control["test"]["expression"], evidence)
    except KeyError as exc:
        return {
            "control_id": control["control_id"],
            "norm_id": control["norm_id"],
            "status": "review",
            "automation_level": control["automation_level"],
            "message": f"Expression references missing evidence field: {exc.args[0]}",
        }

    status = "pass" if passed else "fail"
    return {
        "control_id": control["control_id"],
        "norm_id": control["norm_id"],
        "status": status,
        "automation_level": control["automation_level"],
        "message": control["outcomes"][status],
    }


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

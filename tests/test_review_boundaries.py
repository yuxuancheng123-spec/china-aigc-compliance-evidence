"""Regression tests for review-boundary defects found by targeted counterexamples.

Each case in examples/boundary-diagnostics.yml records the outcome observed at commit 9694fb3
and the outcome required after the fix. These tests pin the fixed behaviour.
"""
from pathlib import Path

import pytest
import yaml

from src.evaluator import evaluate_control, load_controls
from src.validator import validate_runtime_evidence

ROOT = Path(__file__).resolve().parents[1]
CASES = yaml.safe_load((ROOT / "examples" / "boundary-diagnostics.yml").read_text(encoding="utf-8"))
CONTROLS = {control["control_id"]: control for control in load_controls()}


@pytest.mark.parametrize("case", CASES, ids=[case["case_id"] for case in CASES])
def test_boundary_case_routes_as_expected(case: dict) -> None:
    assert validate_runtime_evidence(case["evidence"])["valid"] or case["case_id"].startswith("prominence_minimal_review")
    result = evaluate_control(CONTROLS[case["control_id"]], case["evidence"])
    assert result["final_status"] == case["expected"]


def test_confirmed_false_trigger_is_not_applicable() -> None:
    case = next(c for c in CASES if c["case_id"] == "confirmed_outside_scenario")
    assert case["before_fix_9694fb3"] == "pass"
    assert evaluate_control(CONTROLS[case["control_id"]], case["evidence"])["final_status"] == "not_applicable"


def test_exception_does_not_travel_beyond_its_lifecycle_stage() -> None:
    case = next(c for c in CASES if c["case_id"] == "exception_wrong_lifecycle")
    result = evaluate_control(CONTROLS[case["control_id"]], case["evidence"])
    assert result["final_status"] == "fail"
    assert result.get("scope_result") is None


def test_unattributed_human_review_cannot_close_a_control() -> None:
    for case_id in ("prominence_minimal_review_pass", "prominence_minimal_review_fail"):
        case = next(c for c in CASES if c["case_id"] == case_id)
        assert not validate_runtime_evidence(case["evidence"])["valid"]
        assert evaluate_control(CONTROLS[case["control_id"]], case["evidence"])["final_status"] == "review"

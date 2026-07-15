from pathlib import Path

import yaml

from src.evaluator import OUTCOMES, evaluate_control, evaluate_validation_cases, load_controls
from src.validator import validate_control_mapping, validate_example_norms


ROOT = Path(__file__).resolve().parents[1]


def test_example_legal_norms_validate_against_schema() -> None:
    result = validate_example_norms()

    assert result["valid"] is True
    assert result["examples_checked"] >= 3


def test_clause_to_control_mapping_is_traceable_and_valid() -> None:
    result = validate_control_mapping()

    assert result["valid"] is True
    assert result["controls_checked"] >= 6


def test_controls_declare_automation_level_and_review_status() -> None:
    controls = load_controls()

    assert {control["automation_level"] for control in controls} == {
        "fully_automatable",
        "partially_automatable",
        "human_review_required",
    }
    assert all(control["traceability"]["legal_review_status"] for control in controls)


def test_evaluator_supports_pass_fail_review_and_not_applicable() -> None:
    controls = {control["control_id"]: control for control in load_controls()}
    visible = controls["CTRL-AIGC-VISIBLE-LABEL"]
    biometric = controls["CTRL-PIPL-BIOMETRIC-CLASSIFICATION"]

    assert evaluate_control(
        visible,
        {
            "output_is_ai_generated": True,
            "output_is_user_facing": True,
            "visible_label_present": True,
        },
    )["status"] == "pass"
    assert evaluate_control(
        visible,
        {
            "output_is_ai_generated": True,
            "output_is_user_facing": True,
            "visible_label_present": False,
        },
    )["status"] == "fail"
    assert evaluate_control(
        visible,
        {
            "output_is_ai_generated": True,
            "output_is_user_facing": True,
        },
    )["status"] == "review"
    assert evaluate_control(
        visible,
        {
            "output_is_ai_generated": False,
            "output_is_user_facing": True,
        },
    )["status"] == "not_applicable"
    assert evaluate_control(
        biometric,
        {
            "biometric_data_processed": True,
            "biometric_classification_reviewed": True,
        },
    )["status"] == "review"


def test_validation_cases_match_expected_outcomes() -> None:
    result = evaluate_validation_cases()

    assert result["cases_checked"] >= 15
    assert result["failed"] == 0


def test_every_control_exposes_all_four_outcomes() -> None:
    for control in load_controls():
        assert set(control["outcomes"]) == OUTCOMES


def test_examples_include_consent_labeling_and_filing_controls() -> None:
    examples = {
        path.name: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in (ROOT / "examples").glob("*-control.yml")
    }

    assert examples["consent-control.yml"]["norm_id"] == "CN-PIPL-CONSENT-001"
    assert examples["labeling-control.yml"]["norm_id"] == "CN-AIGC-LABEL-001"
    assert examples["filing-control.yml"]["norm_id"] == "CN-AIGC-FILING-001"

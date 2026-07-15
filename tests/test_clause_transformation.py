from pathlib import Path

import yaml

from src.evaluator import OUTCOMES, evaluate_control, evaluate_validation_cases, load_controls
from src.validator import validate_control_mapping, validate_cross_file_integrity, validate_example_norms, validate_repository


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
    assert all(control["review"]["author_review_status"] == "reviewed" for control in controls)
    assert all(control["review"]["legal_expert_review_status"] == "not_reviewed" for control in controls)


def test_evaluator_supports_pass_fail_review_and_not_applicable() -> None:
    controls = {control["control_id"]: control for control in load_controls()}
    visible = controls["CTRL-AIGC-VISIBLE-LABEL-EXISTENCE"]
    biometric = controls["CTRL-PIPL-BIOMETRIC-CLASSIFICATION"]

    machine_pass = evaluate_control(
        visible,
        {
            "output_is_ai_generated": True,
            "output_is_user_facing": True,
            "output_matches_explicit_label_scenario": True,
            "visible_label_present": True,
        },
    )
    assert machine_pass["machine_result"] == "pass"
    assert machine_pass["status"] == "review"
    assert machine_pass["requires_human_confirmation"] is True

    assert evaluate_control(
        visible,
        {
            "output_is_ai_generated": True,
            "output_is_user_facing": True,
            "output_matches_explicit_label_scenario": True,
            "visible_label_present": True,
            "human_review_completed": True,
            "human_review_result": "pass",
        },
    )["status"] == "pass"
    assert evaluate_control(
        visible,
        {
            "output_is_ai_generated": True,
            "output_is_user_facing": True,
            "output_matches_explicit_label_scenario": True,
            "visible_label_present": False,
        },
    )["status"] == "fail"
    assert evaluate_control(
        visible,
        {
            "output_is_ai_generated": True,
            "output_is_user_facing": True,
            "output_matches_explicit_label_scenario": True,
        },
    )["status"] == "review"
    assert evaluate_control(
        visible,
        {
            "output_is_ai_generated": False,
            "output_is_user_facing": True,
            "output_matches_explicit_label_scenario": True,
        },
    )["status"] == "not_applicable"
    assert evaluate_control(
        biometric,
        {
            "biometric_data_processed": True,
            "biometric_classification_reviewed": True,
            "human_review_result": "pass",
        },
    )["status"] == "pass"


def test_validation_cases_match_expected_outcomes() -> None:
    result = evaluate_validation_cases()

    assert result["cases_checked"] >= 19
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


def test_repository_validation_reports_three_validation_layers() -> None:
    result = validate_repository()

    assert result["schema_valid"] is True
    assert result["cross_file_valid"] is True
    assert result["legal_source_metadata_complete"] is True


def test_cross_file_integrity_checks_are_registered() -> None:
    result = validate_cross_file_integrity()

    assert result["valid"] is True
    assert "test-expression variables declared in evidence, applicability, or exception fields" in result["checks"]
    assert "document title, article number, effective date, and URL consistency" in result["checks"]

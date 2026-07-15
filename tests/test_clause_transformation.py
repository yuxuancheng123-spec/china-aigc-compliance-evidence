from pathlib import Path

import yaml

from src.evaluator import OUTCOMES, evaluate_control, evaluate_validation_cases, load_controls
from src.validator import validate_control_mapping, validate_cross_file_integrity, validate_example_norms, validate_norm_artifacts, validate_repository


ROOT = Path(__file__).resolve().parents[1]


def _confirmation(value: bool = True) -> dict:
    return {"confirmed": True, "value": value, "reviewer_role": "compliance_reviewer", "reviewed_at": "2026-07-15"}


def test_norm_artifacts_validate_and_cover_each_mapping_norm() -> None:
    norms = validate_norm_artifacts()
    controls = load_controls()
    assert norms["valid"] is True
    assert norms["norms_checked"] == 11
    assert {item["norm_id"] for item in [yaml.safe_load(path.read_text(encoding="utf-8")) for path in (ROOT / "norms").glob("*.yml")]} == {control["norm_id"] for control in controls}


def test_examples_remain_display_instances_not_canonical_storage() -> None:
    result = validate_example_norms()
    assert result["valid"] is True
    assert result["examples_checked"] == 3


def test_mapping_is_traceable_and_classifies_control_derivation() -> None:
    controls = load_controls()
    assert validate_control_mapping()["valid"] is True
    assert {control["control_derivation_type"] for control in controls} == {"direct_legal_requirement", "derived_organizational_control", "technical_implementation_control"}
    assert {control["control_id"] for control in controls if control["control_derivation_type"] == "derived_organizational_control"} >= {"CTRL-DEEPSYN-FACE-VOICE-CONSENT-ASSURANCE", "CTRL-PIPL-SEPARATE-CONSENT"}


def test_human_confirmed_fields_require_complete_matching_records() -> None:
    visible = next(control for control in load_controls() if control["control_id"] == "CTRL-AIGC-VISIBLE-LABEL-EXISTENCE")
    base = {"output_is_ai_generated": True, "output_is_user_facing": True, "output_matches_explicit_label_scenario": True, "visible_label_present": True}
    missing = evaluate_control(visible, base)
    assert missing["status"] == "review"
    assert "output_matches_explicit_label_scenario" in missing["human_confirmations_checked"]
    assert evaluate_control(visible, {**base, "human_confirmations": {"output_matches_explicit_label_scenario": _confirmation(False)}})["status"] == "review"
    complete = evaluate_control(visible, {**base, "human_confirmations": {"output_matches_explicit_label_scenario": _confirmation()}})
    assert complete["status"] == "pass"
    assert complete["human_confirmations_checked"] == ["output_matches_explicit_label_scenario"]


def test_article_9_exception_is_scoped_to_provider_delivery() -> None:
    visible = next(control for control in load_controls() if control["control_id"] == "CTRL-AIGC-VISIBLE-LABEL-EXISTENCE")
    result = evaluate_control(visible, {
        "output_is_ai_generated": True, "output_is_user_facing": True, "output_matches_explicit_label_scenario": True,
        "visible_label_present": False, "visible_label_exception_requested": True,
        "user_labeling_obligation_disclosed": True, "user_use_responsibility_disclosed": True,
        "exception_log_retained": True, "log_retention_period_months": 6,
        "human_confirmations": {"output_matches_explicit_label_scenario": _confirmation()},
    })
    assert result["status"] == "pass"
    assert result["scope_result"] == {"scope": "provider_delivery", "status": "pass"}
    assert "downstream publication" in result["message"]


def test_generic_keyed_human_review_controls_final_status() -> None:
    prominence = next(control for control in load_controls() if control["control_id"] == "CTRL-AIGC-VISIBLE-LABEL-PROMINENCE")
    evidence = {
        "output_is_ai_generated": True, "output_is_user_facing": True, "output_matches_explicit_label_scenario": True,
        "visible_label_present": True, "human_confirmations": {"output_matches_explicit_label_scenario": _confirmation()},
    }
    review = evaluate_control(prominence, evidence)
    assert review["status"] == "review"
    assert review["human_review_key"] == "label_prominence"
    final = evaluate_control(prominence, {**evidence, "human_reviews": {"label_prominence": {"completed": True, "result": "pass", "reviewer_role": "compliance_reviewer", "reviewed_at": "2026-07-15"}}})
    assert final["status"] == "pass"
    assert final["human_review_completed"] is True


def test_article_14_direct_and_derived_controls_are_distinct() -> None:
    controls = {control["control_id"]: control for control in load_controls()}
    assert controls["CTRL-DEEPSYN-FACE-VOICE-USER-PROMPT"]["control_derivation_type"] == "direct_legal_requirement"
    assert controls["CTRL-DEEPSYN-FACE-VOICE-CONSENT-ASSURANCE"]["control_derivation_type"] == "derived_organizational_control"
    evidence = {"deep_synthesis_face_or_voice_editing_feature": True, "user_notified_to_inform_edited_person": True, "user_prompt_timestamp": "2026-07-15T10:00:00Z", "human_reviews": {"face_voice_feature_scope": {"completed": True, "result": "pass"}}}
    assert evaluate_control(controls["CTRL-DEEPSYN-FACE-VOICE-USER-PROMPT"], evidence)["status"] == "pass"
    assert evaluate_control(controls["CTRL-DEEPSYN-FACE-VOICE-CONSENT-ASSURANCE"], evidence)["status"] == "review"


def test_validation_cases_match_expected_outcomes() -> None:
    result = evaluate_validation_cases()
    assert result["cases_checked"] >= 21
    assert result["failed"] == 0


def test_every_control_exposes_all_four_outcomes() -> None:
    assert all(set(control["outcomes"]) == OUTCOMES for control in load_controls())


def test_repository_validation_reports_precise_layers_and_notice() -> None:
    result = validate_repository()
    assert result["schema_valid"] is True
    assert result["cross_file_valid"] is True
    assert result["legal_source_metadata_fields_complete"] is True
    assert "does not independently verify" in result["legal_source_metadata_notice"]


def test_cross_file_integrity_checks_include_norm_and_scope_checks() -> None:
    result = validate_cross_file_integrity()
    assert result["valid"] is True
    assert "complete norm artifact coverage" in result["checks"]
    assert "scoped pass exceptions" in result["checks"]
    assert result["warnings"] == []

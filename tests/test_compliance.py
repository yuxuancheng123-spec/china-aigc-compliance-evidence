from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from src.evidence import build_evidence_bundle, build_output_artifacts
from src.generator import generate_synthetic_dataset
from src.models import ComplaintRecord, GenerationRequest
from src.policy_engine import evaluate_request
from src.report import render_markdown_report


def load_rules() -> dict:
    rules_path = Path(__file__).resolve().parents[1] / "policies" / "rules.yml"
    return yaml.safe_load(rules_path.read_text())


def test_request_with_all_controls_passes() -> None:
    request = GenerationRequest(
        request_id="REQ-TEST-001",
        client_id="CLIENT-SYN-001",
        campaign="synthetic product launch",
        actor_asset_id="VACTOR-001",
        requested_usage="advertising_video",
        requested_region="CN",
        model_id="MODEL-AIGC-001",
        output_id="OUT-TEST-001",
        has_visible_label=True,
        has_invisible_label=True,
        safety_status="pass",
        complaint_id=None,
    )
    dataset = generate_synthetic_dataset(seed=7, request_count=3)
    dataset.actor_consents[0].actor_asset_id = "VACTOR-001"
    dataset.actor_consents[0].allowed_usage = ["advertising_video"]
    dataset.actor_consents[0].allowed_regions = ["CN"]
    dataset.actor_consents[0].status = "active"
    dataset.model_filings[0].model_id = "MODEL-AIGC-001"
    dataset.model_filings[0].filing_status = "registered"

    result = evaluate_request(request, dataset, load_rules())

    assert result.overall_status == "pass"
    assert {check.status for check in result.checks} == {"pass"}


def test_request_outside_consent_scope_fails() -> None:
    request = GenerationRequest(
        request_id="REQ-TEST-002",
        client_id="CLIENT-SYN-001",
        campaign="synthetic product launch",
        actor_asset_id="VACTOR-002",
        requested_usage="livestream",
        requested_region="CN",
        model_id="MODEL-AIGC-001",
        output_id="OUT-TEST-002",
        has_visible_label=True,
        has_invisible_label=True,
        safety_status="pass",
        complaint_id=None,
    )
    dataset = generate_synthetic_dataset(seed=11, request_count=3)
    dataset.actor_consents[0].actor_asset_id = "VACTOR-002"
    dataset.actor_consents[0].allowed_usage = ["advertising_video"]
    dataset.actor_consents[0].allowed_regions = ["CN"]
    dataset.actor_consents[0].status = "active"
    dataset.model_filings[0].model_id = "MODEL-AIGC-001"
    dataset.model_filings[0].filing_status = "registered"

    result = evaluate_request(request, dataset, load_rules())

    assert result.overall_status == "fail"
    assert any(
        check.control_id == "CONSENT_SCOPE_USAGE" and check.status == "fail"
        for check in result.checks
    )


def test_evidence_bundle_contains_synthetic_metadata_only() -> None:
    dataset = generate_synthetic_dataset(seed=42, request_count=5)
    bundle = build_evidence_bundle(dataset, load_rules())

    assert bundle["metadata"]["data_classification"] == "synthetic_operational_logs"
    assert bundle["metadata"]["contains_real_personal_data"] is False
    assert len(bundle["request_results"]) == 5
    assert {"pass", "fail", "review"}.issuperset(
        {item["overall_status"] for item in bundle["request_results"]}
    )


def test_seeded_demo_dataset_includes_at_least_one_pass() -> None:
    dataset = generate_synthetic_dataset(seed=20260625, request_count=25)
    bundle = build_evidence_bundle(dataset, load_rules())

    assert bundle["summary"]["pass"] >= 1


def compliant_request(**overrides) -> GenerationRequest:
    values = {
        "request_id": "REQ-TEST-9001",
        "client_id": "CLIENT-SYN-001",
        "campaign": "synthetic product launch",
        "actor_asset_id": "VACTOR-001",
        "consent_id": "CONSENT-SYN-0001",
        "requested_usage": "advertising_video",
        "requested_region": "CN",
        "model_id": "MODEL-AIGC-001",
        "output_id": "OUT-TEST-9001",
        "labeling_check_id": "LBL-TEST-9001",
        "safety_check_id": "SAFE-TEST-9001",
        "complaint_id": None,
    }
    values.update(overrides)
    return GenerationRequest(**values)


def dataset_for_request(request: GenerationRequest):
    dataset = generate_synthetic_dataset(seed=7, request_count=1)
    dataset.generation_requests = [request]
    dataset.actor_consents[0].actor_asset_id = request.actor_asset_id
    dataset.actor_consents[0].consent_id = request.consent_id
    dataset.actor_consents[0].status = "active"
    dataset.actor_consents[0].allowed_usage = ["advertising_video"]
    dataset.actor_consents[0].allowed_regions = ["CN"]
    dataset.actor_consents[0].valid_from = datetime.now(timezone.utc) - timedelta(days=30)
    dataset.actor_consents[0].valid_until = datetime.now(timezone.utc) + timedelta(days=30)
    dataset.model_filings[0].model_id = request.model_id
    dataset.model_filings[0].filing_status = "registered"
    dataset.model_filings[0].registration_ref = "CN-AIGC-SYN-2026-0001"
    dataset.outputs[0].output_id = request.output_id
    dataset.outputs[0].request_id = request.request_id
    dataset.labeling_checks[0].labeling_check_id = request.labeling_check_id
    dataset.labeling_checks[0].output_id = request.output_id
    dataset.labeling_checks[0].has_visible_label = True
    dataset.labeling_checks[0].has_invisible_label = True
    dataset.labeling_checks[0].metadata_label_status = "present"
    dataset.content_safety_checks[0].safety_check_id = request.safety_check_id
    dataset.content_safety_checks[0].request_id = request.request_id
    dataset.content_safety_checks[0].risk_level = "low"
    dataset.content_safety_checks[0].action = "allow"
    return dataset


def assert_failed_control(request: GenerationRequest, dataset, control_id: str) -> None:
    result = evaluate_request(request, dataset, load_rules())

    assert result.overall_status == "fail"
    assert any(check.control_id == control_id and check.status == "fail" for check in result.checks)


def test_expired_consent_fails() -> None:
    request = compliant_request()
    dataset = dataset_for_request(request)
    dataset.actor_consents[0].status = "expired"
    dataset.actor_consents[0].valid_until = datetime.now(timezone.utc) - timedelta(days=1)

    assert_failed_control(request, dataset, "CONSENT_EXISTS")


def test_commercial_use_outside_scope_fails() -> None:
    request = compliant_request(requested_usage="advertising_video")
    dataset = dataset_for_request(request)
    dataset.actor_consents[0].allowed_usage = ["product_demo"]

    assert_failed_control(request, dataset, "CONSENT_SCOPE_USAGE")


def test_revoked_consent_fails() -> None:
    request = compliant_request()
    dataset = dataset_for_request(request)
    dataset.actor_consents[0].status = "revoked"

    assert_failed_control(request, dataset, "CONSENT_EXISTS")


def test_missing_model_filing_metadata_fails() -> None:
    request = compliant_request()
    dataset = dataset_for_request(request)
    dataset.model_filings[0].filing_status = "missing"
    dataset.model_filings[0].registration_ref = None

    assert_failed_control(request, dataset, "MODEL_FILING")


def test_missing_invisible_metadata_label_fails() -> None:
    request = compliant_request()
    dataset = dataset_for_request(request)
    dataset.labeling_checks[0].has_invisible_label = False
    dataset.labeling_checks[0].metadata_label_status = "missing"

    assert_failed_control(request, dataset, "AIGC_INVISIBLE_LABEL")


def test_high_risk_content_must_be_blocked_or_manually_reviewed() -> None:
    request = compliant_request()
    dataset = dataset_for_request(request)
    dataset.content_safety_checks[0].risk_level = "high"
    dataset.content_safety_checks[0].action = "allow"

    assert_failed_control(request, dataset, "CONTENT_SAFETY")

    dataset.content_safety_checks[0].action = "manual_review"
    result = evaluate_request(request, dataset, load_rules())
    assert result.overall_status == "review"
    assert any(check.control_id == "CONTENT_SAFETY" and check.status == "review" for check in result.checks)


def test_overdue_complaint_fails() -> None:
    request = compliant_request(complaint_id="CMP-TEST-9001")
    dataset = dataset_for_request(request)
    dataset.complaints = [
        ComplaintRecord(
            complaint_id="CMP-TEST-9001",
            request_id=request.request_id,
            category="labeling",
            status="acknowledged",
            received_at=datetime.now(timezone.utc) - timedelta(hours=120),
            resolved_at=None,
        )
    ]

    assert_failed_control(request, dataset, "COMPLAINT_HANDLING")


def test_default_v02_dataset_size_and_distribution() -> None:
    dataset = generate_synthetic_dataset(seed=20260625)
    bundle = build_evidence_bundle(dataset, load_rules())

    assert len(dataset.generation_requests) == 1000
    assert len(dataset.virtual_actors) == 50
    assert len(dataset.actor_consents) == 200
    assert len(dataset.model_filings) == 10
    assert len(dataset.outputs) == 1000
    assert len(dataset.labeling_checks) == 1000
    assert len(dataset.content_safety_checks) == 1000
    assert 50 <= len(dataset.complaints) <= 70
    assert 750 <= bundle["summary"]["pass"] <= 850
    assert 80 <= bundle["summary"]["review"] <= 150
    assert 50 <= bundle["summary"]["fail"] <= 100


def test_split_artifacts_and_request_bundles_are_built() -> None:
    dataset = generate_synthetic_dataset(seed=20260625)
    bundle = build_evidence_bundle(dataset, load_rules())
    artifacts = build_output_artifacts(dataset, bundle, load_rules())

    assert "assessment_results" in artifacts
    assert "risk_register" in artifacts
    assert "remediation_items" in artifacts
    assert "summary_table" in artifacts
    assert "request_bundles" in artifacts
    assert len(artifacts["request_bundles"]) >= 30
    first_bundle = next(iter(artifacts["request_bundles"].values()))
    assert {"actor", "consent", "model", "generation_request", "output", "labeling_check", "content_safety_check"}.issubset(first_bundle)


def test_report_generation_does_not_crash(tmp_path: Path) -> None:
    dataset = generate_synthetic_dataset(seed=20260625, request_count=50)
    bundle = build_evidence_bundle(dataset, load_rules())
    artifacts = build_output_artifacts(dataset, bundle, load_rules())
    report_path = tmp_path / "evidence_report.md"

    render_markdown_report(bundle, artifacts, Path(__file__).resolve().parents[1] / "reports", report_path)

    assert report_path.exists()
    assert "Executive Summary" in report_path.read_text(encoding="utf-8")

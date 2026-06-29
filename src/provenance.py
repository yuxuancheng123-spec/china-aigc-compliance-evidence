from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel

from .models import LabelMetadata, SyntheticDataset


class ProvenanceEvent(BaseModel):
    event_type: str
    timestamp: datetime
    actor: str
    status: str
    evidence_ref: str | None = None


class ProvenanceManifest(BaseModel):
    provenance_id: str
    output_id: str
    request_id: str
    actor_asset_id: str
    consent_id: str | None
    model_id: str
    label_id: str
    safety_check_id: str | None
    complaint_id: str | None
    events: list[ProvenanceEvent]


def generate_provenance_manifests(
    dataset: SyntheticDataset,
    label_metadata: list[LabelMetadata],
    request_results: list[dict] | None = None,
) -> list[ProvenanceManifest]:
    labels_by_output = {item.output_id: item for item in label_metadata}
    outputs = {item.output_id: item for item in dataset.outputs}
    safety_by_id = {item.safety_check_id: item for item in dataset.content_safety_checks}
    results_by_request = {item["request_id"]: item for item in request_results or []}
    manifests: list[ProvenanceManifest] = []

    for request in dataset.generation_requests:
        output = outputs[request.output_id]
        label = labels_by_output[request.output_id]
        safety = safety_by_id.get(request.safety_check_id) if request.safety_check_id else None
        base_time = output.created_at
        overall = results_by_request.get(request.request_id, {}).get("overall_status", "recorded")
        events = [
            ProvenanceEvent(
                event_type="request_created",
                timestamp=(base_time - timedelta(seconds=30)).isoformat(),
                actor="synthetic_client",
                status="submitted",
                evidence_ref=f"synthetic://requests/{request.request_id}",
            ),
            ProvenanceEvent(
                event_type="consent_validated",
                timestamp=(base_time - timedelta(seconds=20)).isoformat(),
                actor="consent_control",
                status="checked",
                evidence_ref=f"synthetic://consents/{request.consent_id}",
            ),
            ProvenanceEvent(
                event_type="model_filing_checked",
                timestamp=(base_time - timedelta(seconds=15)).isoformat(),
                actor="model_registry_control",
                status="checked",
                evidence_ref=f"synthetic://models/{request.model_id}",
            ),
            ProvenanceEvent(
                event_type="output_generated",
                timestamp=base_time.isoformat(),
                actor="synthetic_generation_service",
                status="generated",
                evidence_ref=f"synthetic://outputs/{request.output_id}",
            ),
            ProvenanceEvent(
                event_type="label_attached",
                timestamp=label.label_created_at.isoformat(),
                actor="label_metadata_service",
                status=label.verification_status,
                evidence_ref=f"synthetic://labels/{label.label_id}",
            ),
            ProvenanceEvent(
                event_type="content_safety_checked",
                timestamp=(safety.checked_at.isoformat() if safety else base_time.isoformat()),
                actor="content_safety_control",
                status=safety.action if safety else "missing",
                evidence_ref=f"synthetic://safety/{request.safety_check_id}" if request.safety_check_id else None,
            ),
            ProvenanceEvent(
                event_type="complaint_checked",
                timestamp=(base_time + timedelta(seconds=25)).isoformat(),
                actor="complaint_sla_control",
                status="linked" if request.complaint_id else "not_applicable",
                evidence_ref=f"synthetic://complaints/{request.complaint_id}" if request.complaint_id else None,
            ),
            ProvenanceEvent(
                event_type="assessment_completed",
                timestamp=(base_time + timedelta(seconds=30)).isoformat(),
                actor="compliance_assessment_engine",
                status=overall,
                evidence_ref=f"synthetic://assessments/{request.request_id}",
            ),
        ]
        manifests.append(
            ProvenanceManifest(
                provenance_id=f"PROV-{request.request_id}",
                output_id=request.output_id,
                request_id=request.request_id,
                actor_asset_id=request.actor_asset_id,
                consent_id=request.consent_id,
                model_id=request.model_id,
                label_id=label.label_id,
                safety_check_id=request.safety_check_id,
                complaint_id=request.complaint_id,
                events=events,
            )
        )
    return manifests

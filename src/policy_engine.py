from __future__ import annotations

from datetime import datetime, timezone

from .models import ControlCheck, GenerationRequest, RequestEvaluation, SyntheticDataset


def _control(rules: dict, key: str) -> dict:
    return rules["controls"][key]


def _check(rules: dict, key: str, status: str, evidence: dict, message: str) -> ControlCheck:
    rule = _control(rules, key)
    return ControlCheck(
        control_id=rule["id"],
        description=rule["description"],
        severity=rule["severity"],
        status=status,
        evidence=evidence,
        message=message,
    )


def _find_consent(request: GenerationRequest, dataset: SyntheticDataset):
    if request.consent_id:
        for consent in dataset.actor_consents:
            if consent.consent_id == request.consent_id:
                return consent
    for consent in dataset.actor_consents:
        if consent.actor_asset_id == request.actor_asset_id:
            return consent
    return None


def evaluate_request(request: GenerationRequest, dataset: SyntheticDataset, rules: dict) -> RequestEvaluation:
    now = datetime.now(timezone.utc)
    filings = {item.model_id: item for item in dataset.model_filings}
    complaints = {item.complaint_id: item for item in dataset.complaints}
    labels = {item.labeling_check_id: item for item in dataset.labeling_checks}
    labels_by_output = {item.output_id: item for item in dataset.labeling_checks}
    safety_checks = {item.safety_check_id: item for item in dataset.content_safety_checks}
    safety_by_request = {item.request_id: item for item in dataset.content_safety_checks}
    checks: list[ControlCheck] = []

    consent = _find_consent(request, dataset)
    consent_active = bool(consent and consent.status == "active" and consent.valid_from <= now <= consent.valid_until)
    checks.append(
        _check(
            rules,
            "consent_exists",
            "pass" if consent_active else "fail",
            {
                "actor_asset_id": request.actor_asset_id,
                "consent_id": consent.consent_id if consent else None,
                "consent_status": consent.status if consent else None,
            },
            "Active synthetic consent found." if consent_active else "No active synthetic consent found.",
        )
    )

    usage_ok = bool(consent and request.requested_usage in consent.allowed_usage)
    checks.append(
        _check(
            rules,
            "consent_scope_usage",
            "pass" if usage_ok else "fail",
            {
                "requested_usage": request.requested_usage,
                "allowed_usage": ",".join(consent.allowed_usage) if consent else None,
            },
            "Requested usage is within consent scope." if usage_ok else "Requested usage is outside consent scope.",
        )
    )

    region_ok = bool(consent and request.requested_region in consent.allowed_regions)
    checks.append(
        _check(
            rules,
            "consent_scope_region",
            "pass" if region_ok else "fail",
            {
                "requested_region": request.requested_region,
                "allowed_regions": ",".join(consent.allowed_regions) if consent else None,
            },
            "Requested region is within consent scope." if region_ok else "Requested region is outside consent scope.",
        )
    )

    filing = filings.get(request.model_id)
    filing_ok = bool(filing and filing.filing_status == "registered" and filing.registration_ref)
    checks.append(
        _check(
            rules,
            "model_filing",
            "pass" if filing_ok else "fail",
            {
                "model_id": request.model_id,
                "filing_status": filing.filing_status if filing else None,
                "registration_ref": filing.registration_ref if filing else None,
            },
            "Registered synthetic model filing metadata found." if filing_ok else "Model filing metadata is missing or not registered.",
        )
    )

    label = labels.get(request.labeling_check_id) if request.labeling_check_id else labels_by_output.get(request.output_id)
    has_visible_label = label.has_visible_label if label else request.has_visible_label
    has_invisible_label = label.has_invisible_label if label else request.has_invisible_label
    metadata_label_status = label.metadata_label_status if label else ("present" if request.has_invisible_label else "missing")
    checks.append(
        _check(
            rules,
            "visible_label",
            "pass" if has_visible_label else "review",
            {"output_id": request.output_id, "has_visible_label": has_visible_label},
            "Visible AIGC label present." if has_visible_label else "Visible AIGC label needs manual confirmation.",
        )
    )
    invisible_ok = bool(has_invisible_label and metadata_label_status == "present")
    checks.append(
        _check(
            rules,
            "invisible_label",
            "pass" if invisible_ok else "fail",
            {
                "output_id": request.output_id,
                "has_invisible_label": has_invisible_label,
                "metadata_label_status": metadata_label_status,
            },
            "Invisible AIGC metadata present." if invisible_ok else "Invisible AIGC metadata missing.",
        )
    )

    safety = safety_checks.get(request.safety_check_id) if request.safety_check_id else safety_by_request.get(request.request_id)
    if safety:
        if safety.risk_level == "high" and safety.action == "allow":
            safety_status = "fail"
            safety_message = "High-risk content was allowed instead of blocked or manually reviewed."
        elif safety.risk_level == "high" and safety.action == "manual_review":
            safety_status = "review"
            safety_message = "High-risk content is routed for manual review."
        else:
            safety_status = "pass"
            safety_message = "Content safety action is appropriate for the risk level."
        safety_evidence = {
            "risk_level": safety.risk_level,
            "action": safety.action,
            "categories": ",".join(safety.categories),
        }
    else:
        safety_status = request.safety_status
        safety_message = "Content safety check passed." if request.safety_status == "pass" else "Content safety requires action."
        safety_evidence = {"safety_status": request.safety_status}
    checks.append(_check(rules, "content_safety", safety_status, safety_evidence, safety_message))

    complaint = complaints.get(request.complaint_id) if request.complaint_id else None
    complaint_status = "pass"
    complaint_message = "No complaint linked to this request."
    evidence = {"complaint_id": request.complaint_id, "status": None, "age_hours": None, "resolution_hours": None}
    if complaint:
        sla_hours = rules["complaint_sla_hours"]
        age_hours = int((now - complaint.received_at).total_seconds() // 3600)
        resolution_hours = None
        if complaint.resolved_at:
            resolution_hours = int((complaint.resolved_at - complaint.received_at).total_seconds() // 3600)
        if complaint.status == "resolved" and resolution_hours is not None and resolution_hours <= sla_hours:
            complaint_status = "pass"
            complaint_message = "Complaint resolved within SLA."
        elif complaint.status == "resolved" and resolution_hours is not None and resolution_hours > sla_hours:
            complaint_status = "fail"
            complaint_message = "Complaint was resolved after the SLA."
        elif age_hours > sla_hours:
            complaint_status = "fail"
            complaint_message = "Complaint is overdue and unresolved."
        else:
            complaint_status = "review"
            complaint_message = "Complaint is open but still within SLA."
        evidence = {
            "complaint_id": complaint.complaint_id,
            "status": complaint.status,
            "age_hours": age_hours,
            "resolution_hours": resolution_hours,
        }
    checks.append(_check(rules, "complaint_handling", complaint_status, evidence, complaint_message))

    if any(check.status == "fail" for check in checks):
        overall = "fail"
    elif any(check.status == "review" for check in checks):
        overall = "review"
    else:
        overall = "pass"

    return RequestEvaluation(request_id=request.request_id, output_id=request.output_id, overall_status=overall, checks=checks)

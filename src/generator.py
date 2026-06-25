from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

from faker import Faker

from .models import (
    ActorConsent,
    ComplaintRecord,
    ContentSafetyCheck,
    GenerationRequest,
    LabelingCheck,
    ModelFiling,
    OutputRecord,
    SyntheticDataset,
    VirtualActor,
)


USAGES = ["advertising_video", "product_demo", "livestream", "internal_training"]
COMMERCIAL_USAGES = ["advertising_video", "livestream"]
REGIONS = ["CN", "HK", "SG"]
FAILURE_REASONS = [
    "expired_consent",
    "commercial_scope",
    "revoked_consent",
    "missing_model_filing",
    "missing_invisible_label",
    "high_risk_allowed",
    "overdue_complaint",
]
REVIEW_REASONS = ["manual_safety_review", "recent_open_complaint", "pending_visible_label_review"]


def _request_status_plan(request_count: int) -> list[str]:
    pass_count = round(request_count * 0.80)
    review_count = round(request_count * 0.12)
    fail_count = request_count - pass_count - review_count
    return ["pass"] * pass_count + ["review"] * review_count + ["fail"] * fail_count


def _make_actors(count: int) -> list[VirtualActor]:
    return [
        VirtualActor(
            actor_asset_id=f"VACTOR-{idx:03d}",
            asset_name=f"Synthetic Virtual Actor {idx:03d}",
            asset_type="digital_human",
        )
        for idx in range(1, count + 1)
    ]


def _make_consents(now: datetime, actor_count: int, consent_count: int, rng: random.Random) -> list[ActorConsent]:
    consents: list[ActorConsent] = []
    active_count = int(consent_count * 0.80)
    expired_count = int(consent_count * 0.10)
    statuses = ["active"] * active_count + ["expired"] * expired_count
    statuses += ["revoked"] * (consent_count - len(statuses))
    for idx, status in enumerate(statuses, start=1):
        actor_idx = ((idx - 1) % actor_count) + 1
        valid_until = now + timedelta(days=rng.randint(30, 365))
        if status == "expired":
            valid_until = now - timedelta(days=rng.randint(1, 120))
        consents.append(
            ActorConsent(
                actor_asset_id=f"VACTOR-{actor_idx:03d}",
                consent_id=f"CONSENT-SYN-{idx:04d}",
                status=status,
                allowed_usage=rng.sample(USAGES, k=rng.randint(2, 3)),
                allowed_regions=rng.sample(REGIONS, k=rng.randint(1, 3)),
                valid_from=now - timedelta(days=rng.randint(30, 540)),
                valid_until=valid_until,
                evidence_uri=f"synthetic://consents/CONSENT-SYN-{idx:04d}.json",
            )
        )
    for consent in consents[: max(20, actor_count)]:
        consent.status = "active"
        consent.allowed_usage = ["advertising_video", "product_demo", "livestream"]
        consent.allowed_regions = ["CN", "HK", "SG"]
        consent.valid_until = now + timedelta(days=180)
    return consents


def _make_models(now: datetime, count: int) -> list[ModelFiling]:
    models: list[ModelFiling] = []
    for idx in range(1, count + 1):
        filing_status = "registered"
        registration_ref = f"CN-AIGC-SYN-2026-{idx:04d}"
        if idx == count - 1:
            filing_status = "pending"
        if idx == count:
            filing_status = "missing"
            registration_ref = None
        models.append(
            ModelFiling(
                model_id=f"MODEL-AIGC-{idx:03d}",
                provider=f"Synthetic Model Provider {idx:02d}",
                filing_status=filing_status,
                registration_ref=registration_ref,
                last_reviewed_at=now - timedelta(days=idx * 3),
            )
        )
    return models


def generate_synthetic_dataset(
    seed: int = 20260625,
    request_count: int = 1000,
    actor_count: int = 50,
    consent_count: int = 200,
    model_count: int = 10,
) -> SyntheticDataset:
    fake = Faker()
    Faker.seed(seed)
    rng = random.Random(seed)
    now = datetime.now(timezone.utc).replace(microsecond=0)

    virtual_actors = _make_actors(actor_count)
    actor_consents = _make_consents(now, actor_count, consent_count, rng)
    model_filings = _make_models(now, model_count)
    active_consents = [item for item in actor_consents if item.status == "active" and item.valid_until > now]
    expired_consents = [item for item in actor_consents if item.status == "expired"]
    revoked_consents = [item for item in actor_consents if item.status == "revoked"]
    registered_models = [item for item in model_filings if item.filing_status == "registered"]
    missing_model = next(item for item in model_filings if item.filing_status == "missing")

    plan = _request_status_plan(request_count)
    rng.shuffle(plan)
    complaint_target = min(request_count, max(1, round(request_count * 0.06)))
    complaint_indices = set(rng.sample(range(1, request_count + 1), k=complaint_target))
    forced_fail_reasons = FAILURE_REASONS.copy()
    forced_review_reasons = REVIEW_REASONS.copy()

    outputs: list[OutputRecord] = []
    labeling_checks: list[LabelingCheck] = []
    content_safety_checks: list[ContentSafetyCheck] = []
    complaints: list[ComplaintRecord] = []
    generation_requests: list[GenerationRequest] = []

    for idx, planned_status in enumerate(plan, start=1):
        request_id = f"REQ-{idx:04d}"
        output_id = f"OUT-{idx:04d}"
        labeling_check_id = f"LBL-{idx:04d}"
        safety_check_id = f"SAFE-{idx:04d}"
        consent = active_consents[(idx - 1) % len(active_consents)]
        model = registered_models[(idx - 1) % len(registered_models)]
        requested_usage = rng.choice([usage for usage in consent.allowed_usage if usage in USAGES])
        requested_region = rng.choice(consent.allowed_regions)
        visible_label = True
        invisible_label = True
        metadata_label_status = "present"
        risk_level = rng.choices(["low", "medium"], weights=[85, 15])[0]
        action = "allow"
        complaint_id = None

        if planned_status == "fail":
            reason = forced_fail_reasons.pop(0) if forced_fail_reasons else rng.choice(
                [item for item in FAILURE_REASONS if item != "overdue_complaint"]
            )
            if reason == "expired_consent":
                consent = expired_consents[idx % len(expired_consents)]
                requested_usage = consent.allowed_usage[0]
                requested_region = consent.allowed_regions[0]
            elif reason == "commercial_scope":
                consent = next(
                    item for item in active_consents if any(usage not in item.allowed_usage for usage in COMMERCIAL_USAGES)
                )
                requested_usage = next(usage for usage in COMMERCIAL_USAGES if usage not in consent.allowed_usage)
                requested_region = consent.allowed_regions[0]
            elif reason == "revoked_consent":
                consent = revoked_consents[idx % len(revoked_consents)]
                requested_usage = consent.allowed_usage[0]
                requested_region = consent.allowed_regions[0]
            elif reason == "missing_model_filing":
                model = missing_model
            elif reason == "missing_invisible_label":
                invisible_label = False
                metadata_label_status = "missing"
            elif reason == "high_risk_allowed":
                risk_level = "high"
                action = "allow"
            elif reason == "overdue_complaint":
                complaint_indices.add(idx)
        elif planned_status == "review":
            reason = forced_review_reasons.pop(0) if forced_review_reasons else rng.choice(
                [item for item in REVIEW_REASONS if item != "recent_open_complaint"]
            )
            if reason == "manual_safety_review":
                risk_level = "high"
                action = "manual_review"
            elif reason == "recent_open_complaint":
                complaint_indices.add(idx)
            elif reason == "pending_visible_label_review":
                visible_label = False

        if planned_status != "fail" and risk_level != "high":
            action = "allow"

        if idx in complaint_indices:
            complaint_id = f"CMP-{idx:04d}"
            if planned_status == "fail":
                received_at = now - timedelta(hours=120)
                complaints.append(
                    ComplaintRecord(
                        complaint_id=complaint_id,
                        request_id=request_id,
                        category=rng.choice(["labeling", "scope_question", "content_safety"]),
                        status="acknowledged",
                        received_at=received_at,
                        resolved_at=None,
                    )
                )
            elif planned_status == "review":
                complaints.append(
                    ComplaintRecord(
                        complaint_id=complaint_id,
                        request_id=request_id,
                        category=rng.choice(["labeling", "scope_question", "content_safety"]),
                        status="acknowledged",
                        received_at=now - timedelta(hours=rng.randint(4, 36)),
                        resolved_at=None,
                    )
                )
            else:
                received_at = now - timedelta(hours=rng.randint(4, 48))
                complaints.append(
                    ComplaintRecord(
                        complaint_id=complaint_id,
                        request_id=request_id,
                        category=rng.choice(["labeling", "scope_question", "content_safety"]),
                        status="resolved",
                        received_at=received_at,
                        resolved_at=received_at + timedelta(hours=rng.randint(2, 36)),
                    )
                )

        generation_requests.append(
            GenerationRequest(
                request_id=request_id,
                client_id=f"CLIENT-SYN-{rng.randint(1, 80):03d}",
                campaign=fake.catch_phrase(),
                actor_asset_id=consent.actor_asset_id,
                consent_id=consent.consent_id,
                requested_usage=requested_usage,
                requested_region=requested_region,
                model_id=model.model_id,
                output_id=output_id,
                labeling_check_id=labeling_check_id,
                safety_check_id=safety_check_id,
                has_visible_label=visible_label,
                has_invisible_label=invisible_label,
                safety_status="review" if action == "manual_review" else "pass",
                complaint_id=complaint_id,
            )
        )
        outputs.append(
            OutputRecord(
                output_id=output_id,
                request_id=request_id,
                format="mp4",
                storage_uri=f"synthetic://outputs/{output_id}.mp4",
                created_at=now + timedelta(seconds=idx),
            )
        )
        labeling_checks.append(
            LabelingCheck(
                labeling_check_id=labeling_check_id,
                output_id=output_id,
                has_visible_label=visible_label,
                has_invisible_label=invisible_label,
                metadata_label_status=metadata_label_status,
                checked_at=now + timedelta(seconds=idx + 10),
            )
        )
        content_safety_checks.append(
            ContentSafetyCheck(
                safety_check_id=safety_check_id,
                request_id=request_id,
                risk_level=risk_level,
                action=action,
                categories=["synthetic_advertising_claims"] if risk_level != "low" else [],
                checked_at=now + timedelta(seconds=idx + 20),
            )
        )

    return SyntheticDataset(
        generated_at=now,
        virtual_actors=virtual_actors,
        actor_consents=actor_consents,
        model_filings=model_filings,
        generation_requests=generation_requests,
        outputs=outputs,
        labeling_checks=labeling_checks,
        content_safety_checks=content_safety_checks,
        complaints=complaints,
    )

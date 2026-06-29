from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ActorConsent(BaseModel):
    actor_asset_id: str
    consent_id: str
    status: Literal["active", "expired", "revoked"]
    allowed_usage: list[str]
    allowed_regions: list[str]
    valid_from: datetime
    valid_until: datetime
    evidence_uri: str


class VirtualActor(BaseModel):
    actor_asset_id: str
    asset_name: str
    asset_type: Literal["digital_human", "synthetic_voice", "virtual_presenter"]
    synthetic_only: bool = True
    source: str = "synthetic_inventory"


class ModelFiling(BaseModel):
    model_id: str
    provider: str
    filing_status: Literal["registered", "pending", "missing"]
    registration_ref: str | None
    last_reviewed_at: datetime


class GenerationRequest(BaseModel):
    request_id: str
    client_id: str
    campaign: str
    actor_asset_id: str
    consent_id: str | None = None
    requested_usage: str
    requested_region: str
    model_id: str
    output_id: str
    labeling_check_id: str | None = None
    safety_check_id: str | None = None
    has_visible_label: bool = True
    has_invisible_label: bool = True
    safety_status: Literal["pass", "fail", "review"] = "pass"
    complaint_id: str | None = None


class OutputRecord(BaseModel):
    output_id: str
    request_id: str
    format: Literal["mp4", "webm"]
    storage_uri: str
    created_at: datetime
    synthetic_media_only: bool = True


class LabelingCheck(BaseModel):
    labeling_check_id: str
    output_id: str
    has_visible_label: bool
    has_invisible_label: bool
    metadata_label_status: Literal["present", "missing"]
    checked_at: datetime


class LabelMetadata(BaseModel):
    label_id: str
    output_id: str
    request_id: str
    actor_asset_id: str
    model_id: str
    content_type: Literal["video", "image", "audio", "text"]
    visible_disclosure_text: str | None
    visible_label_position: str | None
    machine_readable_format: Literal["json-ld", "xmp", "c2pa_like_manifest", "synthetic_metadata"]
    ai_generated: bool
    output_hash_sha256: str
    metadata_hash_sha256: str
    verifier_uri: str
    label_created_at: datetime
    label_verified_at: datetime | None
    verification_status: Literal["valid", "missing", "tampered", "unknown"]


class ContentSafetyCheck(BaseModel):
    safety_check_id: str
    request_id: str
    risk_level: Literal["low", "medium", "high"]
    action: Literal["allow", "manual_review", "blocked"]
    categories: list[str]
    checked_at: datetime


class ComplaintRecord(BaseModel):
    complaint_id: str
    request_id: str
    category: str
    status: Literal["open", "acknowledged", "resolved"]
    received_at: datetime
    resolved_at: datetime | None


class SyntheticDataset(BaseModel):
    generated_at: datetime
    virtual_actors: list[VirtualActor] = Field(default_factory=list)
    actor_consents: list[ActorConsent]
    model_filings: list[ModelFiling]
    generation_requests: list[GenerationRequest]
    outputs: list[OutputRecord] = Field(default_factory=list)
    labeling_checks: list[LabelingCheck] = Field(default_factory=list)
    content_safety_checks: list[ContentSafetyCheck] = Field(default_factory=list)
    complaints: list[ComplaintRecord] = Field(default_factory=list)


class ControlCheck(BaseModel):
    control_id: str
    description: str
    status: Literal["pass", "fail", "review"]
    severity: str
    evidence: dict[str, str | bool | int | None]
    message: str


class RequestEvaluation(BaseModel):
    request_id: str
    output_id: str
    overall_status: Literal["pass", "fail", "review"]
    checks: list[ControlCheck]

from __future__ import annotations

import hashlib
import json
from typing import Any

from .models import LabelMetadata, SyntheticDataset


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_label_metadata(dataset: SyntheticDataset) -> tuple[list[LabelMetadata], dict]:
    requests = {item.output_id: item for item in dataset.generation_requests}
    outputs = {item.output_id: item for item in dataset.outputs}
    checks = {item.output_id: item for item in dataset.labeling_checks}
    records: list[LabelMetadata] = []

    for idx, output in enumerate(dataset.outputs, start=1):
        request = requests[output.output_id]
        check = checks.get(output.output_id)
        has_visible = check.has_visible_label if check else request.has_visible_label
        has_invisible = check.has_invisible_label if check else request.has_invisible_label
        metadata_label_status = check.metadata_label_status if check else ("present" if has_invisible else "missing")
        verified = metadata_label_status == "present" and has_invisible
        base_payload = {
            "label_id": f"LABEL-META-{idx:04d}",
            "output_id": output.output_id,
            "request_id": request.request_id,
            "actor_asset_id": request.actor_asset_id,
            "model_id": request.model_id,
            "content_type": "video",
            "visible_disclosure_text": "AI-generated synthetic content" if has_visible else None,
            "visible_label_position": "lower_third_overlay" if has_visible else None,
            "machine_readable_format": "synthetic_metadata",
            "ai_generated": True,
            "output_hash_sha256": stable_hash(outputs[output.output_id].model_dump(mode="json")),
            "verifier_uri": f"synthetic://verifier/outputs/{output.output_id}",
            "label_created_at": check.checked_at if check else output.created_at,
            "label_verified_at": check.checked_at if check else None,
            "verification_status": "valid" if verified else "missing",
        }
        base_payload["metadata_hash_sha256"] = stable_hash(base_payload)
        records.append(LabelMetadata(**base_payload))

    summary = {
        "total": len(records),
        "valid": sum(item.verification_status == "valid" for item in records),
        "missing": sum(item.verification_status == "missing" for item in records),
        "tampered": sum(item.verification_status == "tampered" for item in records),
        "unknown": sum(item.verification_status == "unknown" for item in records),
    }
    return records, {
        "schema_version": "0.3",
        "generated_at": dataset.generated_at.isoformat(),
        "jurisdiction": "CN",
        "summary": summary,
        "results": [
            {
                "label_id": item.label_id,
                "output_id": item.output_id,
                "request_id": item.request_id,
                "verification_status": item.verification_status,
                "output_hash_sha256": item.output_hash_sha256,
                "metadata_hash_sha256": item.metadata_hash_sha256,
            }
            for item in records
        ],
    }

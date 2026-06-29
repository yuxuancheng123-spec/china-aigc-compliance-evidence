from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from pydantic import BaseModel

from .models import LabelMetadata, RequestEvaluation, SyntheticDataset
from .policy_engine import evaluate_request
from .provenance import ProvenanceManifest
from .schemas.validators import canonical_evidence_hash


def _dump(model: BaseModel | None) -> dict | None:
    return model.model_dump(mode="json") if model else None


def evaluate_dataset(dataset: SyntheticDataset, rules: dict) -> list[RequestEvaluation]:
    return [evaluate_request(request, dataset, rules) for request in dataset.generation_requests]


def _policy_summary(policy_mapping: list[dict] | None) -> list[dict]:
    return [
        {
            "obligation_id": item.get("obligation_id"),
            "policy_source": item.get("policy_source"),
            "control_ids": item.get("control_ids", []),
            "pipeline_stage": item.get("pipeline_stage"),
        }
        for item in policy_mapping or []
    ]


def _policy_for_controls(policy_mapping: list[dict] | None, control_ids: set[str]) -> list[dict]:
    return [
        item
        for item in policy_mapping or []
        if control_ids.intersection(set(item.get("control_ids", [])))
    ]


def build_evidence_bundle(dataset: SyntheticDataset, rules: dict, policy_mapping: list[dict] | None = None) -> dict:
    results = evaluate_dataset(dataset, rules)
    summary = Counter(result.overall_status for result in results)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    jurisdiction = rules.get("jurisdiction", "CN")
    return {
        "schema_version": "0.3",
        "generated_at": generated_at,
        "jurisdiction": jurisdiction,
        "metadata": {
            "project": "china-ai-compliance-evidence",
            "version": "0.3",
            "generated_at": generated_at,
            "data_classification": "synthetic_operational_logs",
            "contains_real_personal_data": False,
            "contains_real_face_or_voice_data": False,
            "contains_real_contract_data": False,
            "contains_real_company_data": False,
            "jurisdiction": jurisdiction,
            "prototype_notice": rules.get("prototype_notice"),
        },
        "summary": {
            "total_requests": len(results),
            "pass": summary.get("pass", 0),
            "review": summary.get("review", 0),
            "fail": summary.get("fail", 0),
        },
        "source_inventory": {
            "virtual_actors": len(dataset.virtual_actors),
            "actor_consents": len(dataset.actor_consents),
            "model_filings": len(dataset.model_filings),
            "generation_requests": len(dataset.generation_requests),
            "outputs": len(dataset.outputs),
            "labeling_checks": len(dataset.labeling_checks),
            "content_safety_checks": len(dataset.content_safety_checks),
            "complaints": len(dataset.complaints),
        },
        "control_catalog": [
            {"control_key": key, **value}
            for key, value in rules.get("controls", {}).items()
        ],
        "policy_mapping_summary": _policy_summary(policy_mapping),
        "artifact_index": {
            "aggregate_evidence_bundle": "outputs/evidence_bundle.json",
            "assessment_results": "outputs/assessment_results.json",
            "risk_register": "outputs/risk_register.json",
            "remediation_items": "outputs/remediation_items.json",
            "summary_table": "outputs/summary_table.csv",
            "label_metadata": "outputs/label_metadata.json",
            "label_verification_results": "outputs/label_verification_results.json",
            "provenance_export": "outputs/provenance_export.ndjson",
            "provenance_manifest": "outputs/provenance_manifest.json",
            "selected_request_bundles": "outputs/evidence_bundles/{request_id}.json",
        },
        "audit_summary": {
            "schema_valid": True,
            "generated_by": "china-ai-compliance-evidence v0.3",
            "synthetic_data_notice": "All records are synthetic operational logs; no real personal, biometric, contract, company, face, or voice data are used.",
        },
        "request_results": [_dump(result) for result in results],
    }


def _indexes(dataset: SyntheticDataset) -> dict:
    return {
        "actors": {item.actor_asset_id: item for item in dataset.virtual_actors},
        "consents": {item.consent_id: item for item in dataset.actor_consents},
        "models": {item.model_id: item for item in dataset.model_filings},
        "outputs": {item.output_id: item for item in dataset.outputs},
        "labels": {item.labeling_check_id: item for item in dataset.labeling_checks},
        "safety": {item.safety_check_id: item for item in dataset.content_safety_checks},
        "complaints": {item.complaint_id: item for item in dataset.complaints},
    }


def build_request_evidence_bundle(
    request_id: str,
    dataset: SyntheticDataset,
    result: dict,
    policy_mapping: list[dict] | None = None,
    label_metadata: list[LabelMetadata] | None = None,
    provenance_manifests: list[ProvenanceManifest] | None = None,
) -> dict:
    indexes = _indexes(dataset)
    request = next(item for item in dataset.generation_requests if item.request_id == request_id)
    consent = indexes["consents"].get(request.consent_id)
    label_by_output = {item.output_id: item for item in label_metadata or []}
    provenance_by_output = {item.output_id: item for item in provenance_manifests or []}
    control_ids = {check["control_id"] for check in result["checks"]}
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    bundle = {
        "schema_version": "0.3",
        "generated_at": generated_at,
        "jurisdiction": "CN",
        "case_ref": {
            "request_id": request.request_id,
            "output_id": request.output_id,
            "actor_asset_id": request.actor_asset_id,
            "model_id": request.model_id,
            "consent_id": request.consent_id,
        },
        "metadata": {
            "bundle_type": "per_request_synthetic_evidence",
            "data_classification": "synthetic_operational_logs",
            "contains_real_personal_data": False,
        },
        "assessment_result": result,
        "control_results": result["checks"],
        "policy_mapping": _policy_for_controls(policy_mapping, control_ids),
        "actor": _dump(indexes["actors"].get(request.actor_asset_id)),
        "consent": _dump(consent),
        "model": _dump(indexes["models"].get(request.model_id)),
        "generation_request": _dump(request),
        "output": _dump(indexes["outputs"].get(request.output_id)),
        "labeling_check": _dump(indexes["labels"].get(request.labeling_check_id)),
        "content_safety_check": _dump(indexes["safety"].get(request.safety_check_id)),
        "complaint": _dump(indexes["complaints"].get(request.complaint_id)) if request.complaint_id else None,
        "label_metadata": _dump(label_by_output.get(request.output_id)),
        "provenance": _dump(provenance_by_output.get(request.output_id)),
        "audit": {
            "evidence_hash_sha256": None,
            "schema_valid": True,
            "generated_by": "china-ai-compliance-evidence v0.3",
            "retention_class": "synthetic_research_artifact",
            "synthetic_data_notice": "Synthetic demo evidence only; not legal certification.",
        },
    }
    bundle["audit"]["evidence_hash_sha256"] = canonical_evidence_hash(bundle)
    return bundle


def _selected_request_ids(dataset: SyntheticDataset, results: list[dict]) -> list[str]:
    selected: list[str] = []
    for status in ["pass", "review", "fail"]:
        selected.extend([item["request_id"] for item in results if item["overall_status"] == status][:10])
    selected.extend([request.request_id for request in dataset.generation_requests if request.complaint_id])
    return list(dict.fromkeys(selected))


def _control_summary(results: list[dict]) -> list[dict]:
    summary: dict[str, Counter] = defaultdict(Counter)
    descriptions: dict[str, str] = {}
    severities: dict[str, str] = {}
    for result in results:
        for check in result["checks"]:
            control_id = check["control_id"]
            summary[control_id][check["status"]] += 1
            descriptions[control_id] = check["description"]
            severities[control_id] = check["severity"]
    return [
        {
            "control_id": control_id,
            "description": descriptions[control_id],
            "severity": severities[control_id],
            "pass": counts.get("pass", 0),
            "review": counts.get("review", 0),
            "fail": counts.get("fail", 0),
            "total": sum(counts.values()),
        }
        for control_id, counts in sorted(summary.items())
    ]


def _risk_register(control_summary: list[dict]) -> list[dict]:
    risks = []
    for row in control_summary:
        open_items = row["review"] + row["fail"]
        if not open_items:
            continue
        severity = row["severity"]
        impact = "high" if severity == "high" or row["fail"] else "medium"
        risks.append(
            {
                "risk_id": f"RISK-{len(risks) + 1:03d}",
                "control_id": row["control_id"],
                "risk_statement": f"{row['control_id']} has {open_items} synthetic exceptions requiring attention.",
                "severity": severity,
                "impact": impact,
                "open_review_items": row["review"],
                "open_fail_items": row["fail"],
                "owner": "synthetic_compliance_operations",
            }
        )
    return risks


def _remediation_items(risk_register: list[dict]) -> list[dict]:
    actions = {
        "CONSENT_EXISTS": "Refresh consent status and block use of expired or revoked actor assets.",
        "CONSENT_SCOPE_USAGE": "Route commercial usage outside consent scope to contract review.",
        "CONSENT_SCOPE_REGION": "Restrict generation in regions outside approved consent scope.",
        "MODEL_FILING": "Suspend affected model until filing metadata is registered.",
        "AIGC_VISIBLE_LABEL": "Confirm visible AIGC label placement before release.",
        "AIGC_INVISIBLE_LABEL": "Re-run metadata labeling pipeline and prevent publication until present.",
        "CONTENT_SAFETY": "Block high-risk outputs or route them to manual review.",
        "COMPLAINT_HANDLING": "Escalate overdue complaints and record resolution evidence.",
    }
    return [
        {
            "remediation_id": f"REM-{idx:03d}",
            "risk_id": risk["risk_id"],
            "control_id": risk["control_id"],
            "action": actions.get(risk["control_id"], "Review and close the synthetic control exception."),
            "priority": "high" if risk["open_fail_items"] else "medium",
            "status": "open",
        }
        for idx, risk in enumerate(risk_register, start=1)
    ]


def build_output_artifacts(
    dataset: SyntheticDataset,
    bundle: dict,
    rules: dict,
    policy_mapping: list[dict] | None = None,
    label_metadata: list[LabelMetadata] | None = None,
    provenance_manifests: list[ProvenanceManifest] | None = None,
) -> dict:
    results = bundle["request_results"]
    control_summary = _control_summary(results)
    risk_register = _risk_register(control_summary)
    selected_ids = _selected_request_ids(dataset, results)
    result_by_id = {item["request_id"]: item for item in results}
    return {
        "assessment_results": {
            "metadata": bundle["metadata"],
            "summary": bundle["summary"],
            "results": results,
        },
        "risk_register": {
            "metadata": bundle["metadata"],
            "risks": risk_register,
        },
        "remediation_items": {
            "metadata": bundle["metadata"],
            "items": _remediation_items(risk_register),
        },
        "summary_table": [
            {
                "request_id": item["request_id"],
                "output_id": item["output_id"],
                "overall_status": item["overall_status"],
                "failed_controls": ",".join(check["control_id"] for check in item["checks"] if check["status"] == "fail"),
                "review_controls": ",".join(check["control_id"] for check in item["checks"] if check["status"] == "review"),
            }
            for item in results
        ],
        "control_summary": control_summary,
        "request_bundles": {
            request_id: build_request_evidence_bundle(
                request_id,
                dataset,
                result_by_id[request_id],
                policy_mapping=policy_mapping,
                label_metadata=label_metadata,
                provenance_manifests=provenance_manifests,
            )
            for request_id in selected_ids
        },
    }

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from .schemas.validators import canonical_evidence_hash, validate_json


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"

app = FastAPI(
    title="China AIGC Compliance Evidence Audit API",
    version="0.3",
    description="Prototype API for synthetic machine-readable compliance evidence. Not for production use.",
)


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "china-aigc-compliance-evidence-audit-api",
        "prototype": True,
    }


@app.get("/requests/{request_id}/evidence")
def request_evidence(request_id: str) -> dict:
    return _read_json(OUTPUTS_DIR / "evidence_bundles" / f"{request_id}.json")


@app.get("/outputs/{output_id}/label-metadata")
def output_label_metadata(output_id: str) -> dict:
    artifact = _read_json(OUTPUTS_DIR / "label_metadata.json")
    for record in artifact.get("records", []):
        if record.get("output_id") == output_id:
            return record
    raise HTTPException(status_code=404, detail=f"Label metadata not found for {output_id}")


@app.get("/outputs/{output_id}/provenance")
def output_provenance(output_id: str) -> dict:
    artifact = _read_json(OUTPUTS_DIR / "provenance_manifest.json")
    for record in artifact.get("manifests", []):
        if record.get("output_id") == output_id:
            return record
    raise HTTPException(status_code=404, detail=f"Provenance manifest not found for {output_id}")


@app.get("/controls/{control_id}/exceptions")
def control_exceptions(control_id: str) -> dict:
    assessment = _read_json(OUTPUTS_DIR / "assessment_results.json")
    exceptions = []
    for result in assessment.get("results", []):
        for check in result.get("checks", []):
            if check.get("control_id") == control_id and check.get("status") != "pass":
                exceptions.append(
                    {
                        "request_id": result.get("request_id"),
                        "output_id": result.get("output_id"),
                        "overall_status": result.get("overall_status"),
                        "check": check,
                    }
                )
    return {"control_id": control_id, "count": len(exceptions), "exceptions": exceptions}


@app.get("/risks")
def risks() -> dict:
    return _read_json(OUTPUTS_DIR / "risk_register.json")


@app.get("/remediations")
def remediations() -> dict:
    return _read_json(OUTPUTS_DIR / "remediation_items.json")


@app.post("/verify/evidence-bundle")
def verify_evidence_bundle(bundle: dict) -> dict:
    schema_result = validate_json(bundle, "evidence_bundle.schema.json")
    case_ref = bundle.get("case_ref") or {}
    has_required_fields = bool(
        case_ref.get("request_id")
        and case_ref.get("output_id")
        and isinstance(bundle.get("control_results"), list)
        and bundle.get("control_results")
    )
    stored_hash = (bundle.get("audit") or {}).get("evidence_hash_sha256")
    recomputed_hash = canonical_evidence_hash(bundle)
    return {
        "schema_valid": schema_result["schema_valid"],
        "schema_errors": schema_result["errors"],
        "required_fields_present": has_required_fields,
        "stored_hash": stored_hash,
        "recomputed_hash": recomputed_hash,
        "hash_valid": bool(stored_hash and stored_hash == recomputed_hash),
    }

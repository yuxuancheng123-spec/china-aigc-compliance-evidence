import json

from fastapi.testclient import TestClient

from src import audit_api


def test_audit_api_health_endpoint() -> None:
    client = TestClient(audit_api.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_audit_api_evidence_lookup_endpoint(tmp_path, monkeypatch) -> None:
    outputs = tmp_path / "outputs"
    bundles = outputs / "evidence_bundles"
    bundles.mkdir(parents=True)
    bundle = {
        "schema_version": "0.3",
        "generated_at": "2026-06-25T00:00:00+00:00",
        "jurisdiction": "CN",
        "case_ref": {"request_id": "REQ-TEST", "output_id": "OUT-TEST"},
        "control_results": [{"control_id": "CONSENT_EXISTS", "status": "pass"}],
        "policy_mapping": [],
        "label_metadata": {"output_id": "OUT-TEST"},
        "provenance": {"output_id": "OUT-TEST"},
        "audit": {"evidence_hash_sha256": "demo"},
    }
    (bundles / "REQ-TEST.json").write_text(json.dumps(bundle), encoding="utf-8")
    monkeypatch.setattr(audit_api, "OUTPUTS_DIR", outputs)
    client = TestClient(audit_api.app)

    response = client.get("/requests/REQ-TEST/evidence")

    assert response.status_code == 200
    assert response.json()["case_ref"]["request_id"] == "REQ-TEST"

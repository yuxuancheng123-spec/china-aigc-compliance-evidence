from pathlib import Path

import yaml

from src.evidence import build_evidence_bundle, build_output_artifacts
from src.generator import generate_synthetic_dataset
from src.label_metadata import generate_label_metadata
from src.provenance import generate_provenance_manifests
from src.schemas.validators import validate_json


ROOT = Path(__file__).resolve().parents[1]


def test_evidence_bundle_schema_validation() -> None:
    rules = yaml.safe_load((ROOT / "policies" / "rules.yml").read_text(encoding="utf-8"))
    policy_mapping = yaml.safe_load((ROOT / "policies" / "policy_to_control_mapping.yml").read_text(encoding="utf-8"))
    dataset = generate_synthetic_dataset(seed=20260625, request_count=10)
    labels, _ = generate_label_metadata(dataset)
    provenance = generate_provenance_manifests(dataset, labels)
    bundle = build_evidence_bundle(dataset, rules, policy_mapping=policy_mapping)
    artifacts = build_output_artifacts(
        dataset,
        bundle,
        rules,
        policy_mapping=policy_mapping,
        label_metadata=labels,
        provenance_manifests=provenance,
    )

    per_request_bundle = next(iter(artifacts["request_bundles"].values()))
    result = validate_json(per_request_bundle, "evidence_bundle.schema.json")

    assert result["schema_valid"] is True

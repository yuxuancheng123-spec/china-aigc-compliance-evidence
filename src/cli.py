from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import pandas as pd
import yaml
from rich.console import Console
from rich.table import Table

from .evidence import build_evidence_bundle, build_output_artifacts
from .generator import generate_synthetic_dataset
from .label_metadata import generate_label_metadata
from .provenance import generate_provenance_manifests
from .report import render_markdown_report
from .schemas.validators import validate_json


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic China AIGC compliance evidence.")
    parser.add_argument("--seed", type=int, default=20260625)
    parser.add_argument("--requests", type=int, default=1000)
    args = parser.parse_args()

    rules = yaml.safe_load((ROOT / "policies" / "rules.yml").read_text(encoding="utf-8"))
    policy_mapping = yaml.safe_load((ROOT / "policies" / "policy_to_control_mapping.yml").read_text(encoding="utf-8"))
    dataset = generate_synthetic_dataset(seed=args.seed, request_count=args.requests)
    label_metadata, label_verification = generate_label_metadata(dataset)
    bundle = build_evidence_bundle(dataset, rules, policy_mapping=policy_mapping)
    provenance_manifests = generate_provenance_manifests(
        dataset,
        label_metadata,
        request_results=bundle["request_results"],
    )
    artifacts = build_output_artifacts(
        dataset,
        bundle,
        rules,
        policy_mapping=policy_mapping,
        label_metadata=label_metadata,
        provenance_manifests=provenance_manifests,
    )
    label_metadata_artifact = {
        "schema_version": "0.3",
        "generated_at": dataset.generated_at.isoformat(),
        "jurisdiction": rules.get("jurisdiction", "CN"),
        "records": [item.model_dump(mode="json") for item in label_metadata],
    }
    provenance_artifact = {
        "schema_version": "0.3",
        "generated_at": dataset.generated_at.isoformat(),
        "jurisdiction": rules.get("jurisdiction", "CN"),
        "manifests": [item.model_dump(mode="json") for item in provenance_manifests],
    }
    schema_checks = {
        "evidence_bundle": validate_json(bundle, "evidence_bundle.schema.json"),
        "label_metadata": validate_json(label_metadata_artifact, "label_metadata.schema.json"),
        "provenance_manifest": validate_json(provenance_artifact, "provenance_manifest.schema.json"),
    }
    bundle["audit_summary"]["schema_validation"] = schema_checks

    outputs = ROOT / "outputs"
    reports = ROOT / "reports"
    request_bundle_dir = outputs / "evidence_bundles"
    outputs.mkdir(exist_ok=True)
    reports.mkdir(exist_ok=True)
    if request_bundle_dir.exists():
        shutil.rmtree(request_bundle_dir)
    request_bundle_dir.mkdir(exist_ok=True)

    write_json(outputs / "evidence_bundle.json", bundle)
    write_json(outputs / "synthetic_dataset.json", dataset.model_dump(mode="json"))
    write_json(outputs / "assessment_results.json", artifacts["assessment_results"])
    write_json(outputs / "risk_register.json", artifacts["risk_register"])
    write_json(outputs / "remediation_items.json", artifacts["remediation_items"])
    write_json(outputs / "label_metadata.json", label_metadata_artifact)
    write_json(outputs / "label_verification_results.json", label_verification)
    write_json(outputs / "provenance_manifest.json", provenance_artifact)
    (outputs / "provenance_export.ndjson").write_text(
        "\n".join(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) for item in provenance_manifests) + "\n",
        encoding="utf-8",
    )
    for request_id, request_bundle in artifacts["request_bundles"].items():
        write_json(request_bundle_dir / f"{request_id}.json", request_bundle)

    frame = pd.DataFrame(artifacts["summary_table"])
    frame.to_csv(outputs / "request_control_matrix.csv", index=False)
    frame.to_csv(outputs / "summary_table.csv", index=False)
    render_markdown_report(bundle, artifacts, ROOT / "reports", reports / "evidence_report.md")

    table = Table(title="Synthetic AIGC Compliance Evidence")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key, value in bundle["summary"].items():
        table.add_row(key, str(value))
    console = Console()
    console.print(table)
    console.print(f"Wrote {outputs / 'evidence_bundle.json'}")
    console.print(f"Wrote {outputs / 'assessment_results.json'}")
    console.print(f"Wrote {outputs / 'risk_register.json'}")
    console.print(f"Wrote {outputs / 'label_metadata.json'}")
    console.print(f"Wrote {outputs / 'label_verification_results.json'}")
    console.print(f"Wrote {outputs / 'provenance_export.ndjson'}")
    console.print(f"Wrote {outputs / 'provenance_manifest.json'}")
    console.print(f"Wrote {reports / 'evidence_report.md'}")


if __name__ == "__main__":
    main()

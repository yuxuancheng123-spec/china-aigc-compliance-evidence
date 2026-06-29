import subprocess
import sys
from pathlib import Path

import yaml

from src.evidence import build_evidence_bundle
from src.generator import generate_synthetic_dataset


ROOT = Path(__file__).resolve().parents[1]


def test_seeded_pipeline_still_produces_v02_distribution() -> None:
    rules = yaml.safe_load((ROOT / "policies" / "rules.yml").read_text(encoding="utf-8"))
    dataset = generate_synthetic_dataset(seed=20260625)
    bundle = build_evidence_bundle(dataset, rules)

    assert bundle["summary"] == {"total_requests": 1000, "pass": 800, "review": 120, "fail": 80}


def test_cli_still_writes_original_and_v03_artifacts() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "--seed", "20260625"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    for path in [
        ROOT / "outputs" / "assessment_results.json",
        ROOT / "outputs" / "risk_register.json",
        ROOT / "outputs" / "remediation_items.json",
        ROOT / "outputs" / "summary_table.csv",
        ROOT / "outputs" / "label_metadata.json",
        ROOT / "outputs" / "label_verification_results.json",
        ROOT / "outputs" / "provenance_export.ndjson",
        ROOT / "outputs" / "provenance_manifest.json",
    ]:
        assert path.exists()

# China AIGC Compliance Evidence Generator

A research prototype for machine-readable compliance evidence in China-facing AIGC actor and digital human platforms.

**Article PDF:** [Making China AIGC Compliance Evidence Machine-Readable: A Governance Pipeline Prototype for Synthetic Actor and Digital Human Platforms](article/china-aigc-compliance-evidence-paper.pdf)

`china-ai-compliance-evidence` is a Python 3.11 prototype that converts synthetic operational logs for a China-based AIGC actor / digital human advertising platform into machine-readable compliance evidence. It models a platform that generates advertising videos from licensed virtual actor assets and evaluates whether each request has valid consent, scoped usage, model filing metadata, AIGC labels, content safety review, and complaint handling evidence.

All data in this repository are synthetic. The project does not use real personal data, face data, voice data, biometric data, contracts, company records, or customer records.

## Research Context

This project is inspired by recent work on machine-readable AI compliance evidence and Compliance-as-Code. Instead of focusing on EU AI Act high-risk systems, this prototype adapts the idea to selected Chinese AI governance obligations around generative AI services, deep synthesis, AIGC labeling, model filing/disclosure, consent management, content safety, and complaint handling.

## Why This Project Matters

AI governance programs increasingly need evidence that is structured, repeatable, and reviewable by both humans and machines. This prototype explores how selected governance expectations can be represented as operational controls, assessed at request level, and exported as JSON, CSV, and Markdown artifacts suitable for audit preparation, technical documentation, and portfolio demonstration.

## Regulatory Scope

The prototype is informed by Chinese AI governance materials related to generative AI services, deep synthesis services, algorithmic recommendation governance, AIGC labeling, and personal information protection. It is a simplified technical model, not a legal interpretation. See [references.md](references.md) for background sources.

## What The Prototype Does

- Generates synthetic virtual actors, consent records, model filing records, generation requests, outputs, labeling checks, content safety checks, and complaint records.
- Evaluates request-level controls for consent validity, consent scope, model filing metadata, visible and invisible AIGC labels, content safety disposition, and complaint SLA handling.
- Produces assessment results, a risk register, remediation items, summary tables, a Markdown report, and selected per-request evidence bundles.
- Calibrates the default synthetic run to a realistic demonstration distribution: 75-85% pass, 8-15% review, and 5-10% fail.

## Folder Structure

```text
china-ai-compliance-evidence/
├── article/              # Article-support drafts
├── data/                 # Reserved for non-sensitive synthetic input data
├── docs/                 # Methodology and project documentation
├── outputs/              # Generated JSON/CSV evidence artifacts
├── policies/             # Synthetic control rules
├── reports/              # Generated reports and article-ready tables
├── src/                  # Python source code
├── tests/                # Pytest tests
├── LICENSE
├── README.md
├── references.md
└── requirements.txt
```

## Quick Start

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.cli --seed 20260625
pytest
```

If `python3.11` is not available on your machine, use an installed Python 3.11 interpreter path.

Expected seeded output:

- 1,000 synthetic generation requests
- 800 pass, 120 review, 80 fail
- 88 selected per-request evidence bundles
- 14 passing tests

## Example Outputs

The default run generates:

- `outputs/synthetic_dataset.json`
- `outputs/evidence_bundle.json`
- `outputs/assessment_results.json`
- `outputs/risk_register.json`
- `outputs/remediation_items.json`
- `outputs/request_control_matrix.csv`
- `outputs/summary_table.csv`
- `outputs/evidence_bundles/REQ-xxxx.json`
- `reports/evidence_report.md`
- `reports/table_3_validation_results.md`

The current seeded run produces 1,000 generation requests: 800 pass, 120 review, and 80 fail. The repository keeps a small representative sample of per-request evidence bundles for GitHub readability. The full set of 88 selected per-request bundles can be regenerated locally by running the pipeline:

```bash
python -m src.cli --seed 20260625
```

## Limitations

This is a minimal prototype. The controls are intentionally simplified, the data are generated rather than collected from production systems, and the policy mapping is illustrative. The project does not implement authentication, secure evidence retention, cryptographic watermarking, production logging, legal workflow management, or regulator-facing filing integrations.

## Legal Disclaimer

This project is for technical demonstration, research, and portfolio use only. It is not legal advice and does not establish compliance with any law, regulation, standard, or filing obligation. Any production use would require qualified legal review, full policy mapping, validated data lineage, security controls, governance ownership, and human oversight.

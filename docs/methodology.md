# Methodology

## Overview

This project demonstrates a reproducible method for turning synthetic operational records into machine-readable compliance evidence. The workflow has three stages: synthetic data generation, control evaluation, and evidence bundle construction.

## Synthetic Data Generation

The generator creates a deterministic dataset from a seed value. The default seed is `20260625`, which produces:

- 1,000 generation requests
- 50 synthetic virtual actor assets
- 200 synthetic consent records
- 10 synthetic model filing records
- 1,000 synthetic output records
- 1,000 synthetic labeling checks
- 1,000 synthetic content safety checks
- Approximately 60 synthetic complaint records

The generated records are operational logs only. They do not contain real personal data, face data, voice data, biometric data, contracts, companies, customers, or production media.

The generator intentionally includes realistic control exceptions, including expired consent, revoked consent, commercial use outside scope, missing model filing metadata, missing invisible labels, high-risk content that was not blocked, and overdue complaint handling. The default run is calibrated to approximately 80% pass, 12% review, and 8% fail.

## Control Evaluation

Each generation request is evaluated against the synthetic policy file in `policies/rules.yml`. The evaluator joins a request to its consent, model, output, labeling check, content safety check, and complaint record where available.

The implemented controls are:

- Active actor consent exists.
- Requested usage is within consent scope.
- Requested region is within consent scope.
- Model filing metadata is registered.
- Visible AIGC label is present or routed for review.
- Invisible or metadata AIGC label is present.
- High-risk content is blocked or manually reviewed.
- Complaints are resolved within the synthetic SLA or escalated.

Each control returns `pass`, `review`, or `fail`. A request fails if any control fails, is marked review if no control fails but at least one control requires review, and passes only if all controls pass.

## Evidence Bundle Construction

The evidence builder creates both aggregate and per-request artifacts:

- `assessment_results.json` contains request-level assessment results.
- `risk_register.json` groups open review/fail items into synthetic risk records.
- `remediation_items.json` proposes synthetic remediation actions for open risks.
- `summary_table.csv` provides a compact request-level table.
- `evidence_bundles/REQ-xxxx.json` joins all available records for selected requests.

Per-request evidence bundles are generated for 10 passing requests, 10 review requests, 10 failing requests, and all complaint-related requests. Each bundle includes only synthetic records.

## Reproducibility

Run the full pipeline with:

```bash
python -m src.cli --seed 20260625
pytest
```

The seed makes the default dataset and summary distribution reproducible for article drafting and portfolio review.

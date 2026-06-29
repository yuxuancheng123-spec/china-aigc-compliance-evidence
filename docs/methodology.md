# Methodology

## Overview

This project demonstrates a reproducible method for turning synthetic operational records into machine-readable compliance evidence. The v0.3 workflow has six stages:

```text
Policy → Controls → Evidence → Label Metadata → Provenance → Audit API
```

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

## Policy-to-Control Mapping

`policies/policy_to_control_mapping.yml` links selected policy sources, obligation summaries, control IDs, required evidence fields, generated artifacts, and pipeline stages. This mapping is illustrative. It is designed to show how policy requirements can be decomposed into controls and evidence artifacts without claiming full legal coverage.

## Schema Validation

The `schemas/` directory defines lightweight JSON Schemas for evidence bundles, label metadata, provenance manifests, and audit events. The pipeline validates aggregate evidence, label metadata, and provenance artifacts during generation and records validation results in the evidence bundle audit summary.

## Machine-readable Label Metadata

`src/label_metadata.py` generates one synthetic label metadata record per output. Each record includes a label ID, request ID, output ID, model ID, actor asset ID, content type, visible disclosure fields, machine-readable metadata format, deterministic synthetic hashes, verifier URI, timestamps, and verification status. The demo verifier marks a label as valid when the invisible/metadata label is present and missing otherwise.

## Provenance Export

`src/provenance.py` generates one provenance manifest per request/output. Each manifest records synthetic lifecycle events: request creation, consent validation, model filing check, output generation, label attachment, content safety check, complaint check, and assessment completion. The project writes both a JSON list for readability and NDJSON for machine processing.

## Audit API

`src/audit_api.py` provides a minimal FastAPI interface over generated artifacts. It supports health checks, request evidence lookup, output label metadata lookup, output provenance lookup, control exception lookup, risk/remediation retrieval, and evidence bundle verification. The API is intentionally unauthenticated and local-only for prototype use.

## Reproducibility

Run the full pipeline with:

```bash
python -m src.cli --seed 20260625
pytest
```

The seed makes the default dataset and summary distribution reproducible for article drafting and portfolio review.

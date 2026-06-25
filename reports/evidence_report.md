# Synthetic AIGC Compliance Evidence Report

## Executive Summary

This v0.2 prototype generated a synthetic compliance assessment for a China-based AIGC actor / digital human advertising video platform. The run assessed 1000 generation requests using synthetic operational logs only.

| Outcome | Count |
| --- | ---: |
| Pass | 800 |
| Review | 120 |
| Fail | 80 |

Data classification: `synthetic_operational_logs`

No real personal data, face data, voice data, contracts, or company data are included.

## Dataset Summary

| Source | Count |
| --- | ---: |
| virtual_actors | 50 |
| actor_consents | 200 |
| model_filings | 10 |
| generation_requests | 1000 |
| outputs | 1000 |
| labeling_checks | 1000 |
| content_safety_checks | 1000 |
| complaints | 62 |

## Control Catalog Summary

| Control | Severity | Description |
| --- | --- | --- |
| CONSENT_EXISTS | high | Actor asset has an active synthetic consent record. |
| CONSENT_SCOPE_USAGE | high | Requested usage is within the allowed consent usage scope. |
| CONSENT_SCOPE_REGION | medium | Requested region is within the allowed consent region scope. |
| MODEL_FILING | high | Generation model has synthetic filing or registration metadata. |
| AIGC_VISIBLE_LABEL | medium | Generated output has a visible AIGC label. |
| AIGC_INVISIBLE_LABEL | medium | Generated output has invisible AIGC provenance metadata. |
| CONTENT_SAFETY | high | Content safety checks pass before release. |
| COMPLAINT_HANDLING | medium | Complaints are acknowledged and resolved within the demo SLA. |

## Validation Results

| Control | Severity | Pass | Review | Fail | Total |
| --- | --- | ---: | ---: | ---: | ---: |
| AIGC_INVISIBLE_LABEL | medium | 989 | 0 | 11 | 1000 |
| AIGC_VISIBLE_LABEL | medium | 934 | 66 | 0 | 1000 |
| COMPLAINT_HANDLING | medium | 985 | 6 | 9 | 1000 |
| CONSENT_EXISTS | high | 969 | 0 | 31 | 1000 |
| CONSENT_SCOPE_REGION | medium | 1000 | 0 | 0 | 1000 |
| CONSENT_SCOPE_USAGE | high | 986 | 0 | 14 | 1000 |
| CONTENT_SAFETY | high | 933 | 53 | 14 | 1000 |
| MODEL_FILING | high | 991 | 0 | 9 | 1000 |

## Key Failed Controls

| Control | Failed Items | Why It Matters |
| --- | ---: | --- |
| AIGC_INVISIBLE_LABEL | 11 | Generated output has invisible AIGC provenance metadata. |
| COMPLAINT_HANDLING | 9 | Complaints are acknowledged and resolved within the demo SLA. |
| CONSENT_EXISTS | 31 | Actor asset has an active synthetic consent record. |
| CONSENT_SCOPE_USAGE | 14 | Requested usage is within the allowed consent usage scope. |
| CONTENT_SAFETY | 14 | Content safety checks pass before release. |
| MODEL_FILING | 9 | Generation model has synthetic filing or registration metadata. |

## Risk Register Summary

| Risk | Control | Impact | Review | Fail | Owner |
| --- | --- | --- | ---: | ---: | --- |
| RISK-001 | AIGC_INVISIBLE_LABEL | high | 0 | 11 | synthetic_compliance_operations |
| RISK-002 | AIGC_VISIBLE_LABEL | medium | 66 | 0 | synthetic_compliance_operations |
| RISK-003 | COMPLAINT_HANDLING | high | 6 | 9 | synthetic_compliance_operations |
| RISK-004 | CONSENT_EXISTS | high | 0 | 31 | synthetic_compliance_operations |
| RISK-005 | CONSENT_SCOPE_USAGE | high | 0 | 14 | synthetic_compliance_operations |
| RISK-006 | CONTENT_SAFETY | high | 53 | 14 | synthetic_compliance_operations |
| RISK-007 | MODEL_FILING | high | 0 | 9 | synthetic_compliance_operations |

## Remediation Plan

| Item | Control | Priority | Action |
| --- | --- | --- | --- |
| REM-001 | AIGC_INVISIBLE_LABEL | high | Re-run metadata labeling pipeline and prevent publication until present. |
| REM-002 | AIGC_VISIBLE_LABEL | medium | Confirm visible AIGC label placement before release. |
| REM-003 | COMPLAINT_HANDLING | high | Escalate overdue complaints and record resolution evidence. |
| REM-004 | CONSENT_EXISTS | high | Refresh consent status and block use of expired or revoked actor assets. |
| REM-005 | CONSENT_SCOPE_USAGE | high | Route commercial usage outside consent scope to contract review. |
| REM-006 | CONTENT_SAFETY | high | Block high-risk outputs or route them to manual review. |
| REM-007 | MODEL_FILING | high | Suspend affected model until filing metadata is registered. |

## Per-Request Evidence Bundles

Selected per-request bundles are generated for 10 pass, 10 review, 10 fail examples, plus all complaint-related requests. Each selected bundle joins actor, consent, model, generation request, output, labeling check, content safety check, and complaint records when available.

Generated bundle count: 88

## Limitations and Legal Disclaimer

This prototype is a technical demonstration and is not legal advice. The controls are simplified and synthetic. Production use would require legal review, complete policy mapping, verified data lineage, real control ownership, secure evidence retention, and human governance procedures. This project intentionally excludes real personal data, real face data, real voice data, real contracts, and real company data.
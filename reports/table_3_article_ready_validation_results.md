# Table 3. Control-Level Validation Results

| Phase | Control | Actual | Threshold | Result |
| --- | --- | ---: | --- | --- |
| Dataset generation | Generation requests assessed | 1,000 | 1,000 synthetic requests | Met |
| Outcome calibration | Pass outcomes | 800 (80.0%) | 75–85% | Met |
| Outcome calibration | Review outcomes | 120 (12.0%) | 8–15% | Met |
| Outcome calibration | Fail outcomes | 80 (8.0%) | 5–10% | Met |
| Pre-generation | Consent existence exceptions | 31 | Captured as review/fail | Captured |
| Pre-generation | Consent scope exceptions | 14 | Captured as review/fail | Captured |
| Deployment | Model filing metadata exceptions | 9 | Captured as review/fail | Captured |
| Publication | Visible AIGC label exceptions | 66 | Captured as review/fail | Captured |
| Publication | Invisible / metadata label exceptions | 11 | Captured as review/fail | Captured |
| Publication | Content safety exceptions | 67 | Captured as review/fail | Captured |
| Monitoring | Complaint handling exceptions | 15 | Captured as review/fail | Captured |
| Evidence packaging | Selected per-request evidence bundles | 88 | Pass + review + fail + complaint-related requests | Met |

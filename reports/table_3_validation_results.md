# Table 3. Validation Results

| Phase | Control | Actual | Threshold | Result |
| --- | --- | ---: | --- | --- |
| Dataset generation | Generation requests assessed | 1000 | 1,000 synthetic requests | Met |
| Outcome calibration | Pass outcomes | 800 (80.0%) | 75-85% | Met |
| Outcome calibration | Review outcomes | 120 (12.0%) | 8-15% | Met |
| Outcome calibration | Fail outcomes | 80 (8.0%) | 5-10% | Met |
| Control validation | AIGC_INVISIBLE_LABEL | 11 | Exceptions captured as review/fail | Captured |
| Control validation | AIGC_VISIBLE_LABEL | 66 | Exceptions captured as review/fail | Captured |
| Control validation | COMPLAINT_HANDLING | 15 | Exceptions captured as review/fail | Captured |
| Control validation | CONSENT_EXISTS | 31 | Exceptions captured as review/fail | Captured |
| Control validation | CONSENT_SCOPE_USAGE | 14 | Exceptions captured as review/fail | Captured |
| Control validation | CONTENT_SAFETY | 67 | Exceptions captured as review/fail | Captured |
| Control validation | MODEL_FILING | 9 | Exceptions captured as review/fail | Captured |
| Evidence packaging | Selected per-request bundles | 88 | 10 pass + 10 review + 10 fail + all complaints | Met |

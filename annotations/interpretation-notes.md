# Interpretation Notes

This project does not ask software to interpret law by itself. The machine-readable controls are based on author-reviewed structured interpretations of selected legal provisions. Independent qualified legal expert review has not yet been recorded.

## Transformation Chain

```text
Formal Chinese legal provision
-> Normative sentence identification
-> Legal semantic decomposition
-> Human interpretation
-> Control objective
-> Evidence requirement
-> Machine-readable test
-> Review status and traceability
```

## Automation Levels

- `fully_automatable`: The control can be evaluated from structured evidence with limited legal judgment, such as whether required metadata fields are present.
- `partially_automatable`: Structured evidence can support evaluation, but legal or contextual review may still be needed, such as whether a visible label is sufficiently prominent.
- `human_review_required`: The legal standard is open-textured or context-dependent, such as whether "effective measures" were sufficient.

## Reviewer Notes

- Label existence is easier to automate than label prominence or user comprehension.
- Filing applicability can depend on service type, deployment mode, and regulator guidance.
- Consent records can be checked mechanically only after a human-reviewed interpretation of the required consent type.
- Content safety and "effective measures" obligations should not be collapsed into a single Boolean result.
- Complaint handling is mapped to Article 15 of the Interim Measures, not Article 17.
- Model filing is mapped to Article 17 of the Interim Measures and requires reviewed applicability fields before filing status is checked.
- Deep synthesis confusion-risk labeling is mapped to Article 17 of the Deep Synthesis Provisions; Article 14 is separately modeled for face and voice editing consent.

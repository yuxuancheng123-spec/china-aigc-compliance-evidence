# Interpretation Notes

This project does not ask software to interpret law by itself. The machine-readable controls are based on human-reviewed structured interpretations of selected legal provisions.

## Transformation Chain

```text
Original legal provision
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

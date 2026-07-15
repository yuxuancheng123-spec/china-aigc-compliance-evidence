# Methodology

## Overview

This repository now centers on legal-clause-to-control transformation. The main research object is not a compliance assessment product, dashboard, or case-review workflow. The main object is the method used to transform selected Chinese AIGC legal provisions into traceable, reviewable, and machine-readable controls.

The transformation chain is:

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

## Clause Selection

The corpus is intentionally small. It selects provisions that are directly relevant to synthetic actor, digital human, and AIGC content-generation scenarios:

- generative AI service governance;
- deep synthesis labeling;
- explicit AIGC labeling;
- implicit or metadata labeling;
- GB 45438-2025 metadata-label methods;
- sensitive personal information and biometric-like data;
- complaint and reporting mechanisms;
- model filing or applicability review.

The project does not attempt full coverage of Chinese AI law.

## Semantic Decomposition

Each selected clause is decomposed into fields such as:

- source document and article;
- original clause summary;
- normative fragment;
- regulated actor;
- modality;
- required action;
- regulated object;
- trigger condition;
- exception;
- timing;
- required evidence;
- control objective;
- test logic;
- automation level;
- ambiguity level;
- reviewer note;
- source effective date;
- interpretation version;
- legal review status.

These fields are stored in `annotations/clause-decomposition.csv` and reflected in the schemas and mappings.

## Human Interpretation

Machine-readable does not mean machine-interpreted. The repository assumes a human reviewer has selected the clause, identified the normative fragment, interpreted the legal meaning, and classified the automation level. The evaluator executes only that reviewed representation.

## Schema Validation

`schema/legal-norm-schema.json` validates the structure of human-reviewed legal norms. `schema/control-schema.json` validates executable controls derived from those norms. The validator checks required fields, source traceability, test logic, automation-level declaration, and legal review status.

## Control Evaluation

`src/evaluator.py` supports a narrow expression subset and returns:

- `pass`;
- `fail`;
- `review`;
- `not_applicable`.

Controls marked `human_review_required` are routed to review when applicable. Missing evidence also routes to review. Trigger conditions determine whether a control is applicable.

## Validation Set

`examples/validation-cases.yml` contains a compact validation set rather than a large random dataset. The cases cover:

- applicable rules with sufficient evidence;
- applicable rules with missing evidence;
- clear failures;
- non-applicable rules;
- human-review-required obligations;
- multiple rules applying to the same use case.

The validation focus is methodological consistency, not a statistical pass/fail distribution.

## Supplementary Proof of Concept

The legacy synthetic request pipeline remains available through:

```bash
python -m src.cli --seed 20260625
```

It generates synthetic operational artifacts under `outputs/`. These outputs are supplementary proof of concept only. They show that structured controls can be read and executed by software, but the project's main contribution is the legal-clause-to-control transformation method.

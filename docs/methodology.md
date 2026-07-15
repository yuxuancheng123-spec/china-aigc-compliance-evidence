# Methodology

## Overview

This repository now centers on legal-clause-to-control transformation. The main research object is not a compliance assessment product, dashboard, or case-review workflow. The main object is the method used to transform selected Chinese AIGC legal provisions into traceable, reviewable, and machine-readable controls.

The transformation chain is:

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

## Regulatory Corpus Selection

The corpus is intentionally small. It selects provisions that are directly relevant to synthetic actor, digital human, and AIGC content-generation scenarios:

- generative AI service governance;
- deep synthesis labeling;
- explicit AIGC labeling;
- implicit or metadata labeling;
- GB 45438-2025 metadata-label methods;
- sensitive personal information and biometric-like data;
- complaint and reporting mechanisms;
- model filing or applicability review.

The selected sources are representative rather than exhaustive. They were chosen because they cover the main legal-to-technical boundary in China-facing AIGC services: service-provider duties, deep synthesis scenarios, generated-content labeling, technical metadata labels, model filing triggers, complaint handling, and personal information protection. Clauses are included when they can be decomposed into a source, actor, modality, action, object, trigger, exception, evidence requirement, automation level, and review status. Clauses are excluded when they are too broad for this prototype, sector-specific, unrelated to synthetic actor or digital human services, or impossible to represent without extensive legal interpretation.

Where a general rule and a special rule overlap, both are preserved. For example, PIPL Article 29 is retained as a general sensitive-personal-information separate-consent rule, while Article 14 of the Deep Synthesis Provisions is retained as a special rule for face and voice editing functions.

## Semantic Decomposition

Each selected clause is decomposed into fields such as:

- source document and article;
- formal Chinese source text;
- working English translation;
- official source URL;
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
- author review status;
- legal expert review status.

These fields are stored in `annotations/clause-decomposition.csv` and reflected in the schemas and mappings.

## Interpretation Protocol

Machine-readable does not mean machine-interpreted. The repository assumes that a human researcher first selects the clause, identifies the normative fragment, records a working translation, interprets the legal meaning, defines the control objective, and classifies the automation level. The evaluator executes only that reviewed representation.

The initial interpretation is performed by the project author as a research exercise. The interpretation record must identify the source, article, source text, working translation, control objective, evidence requirement, ambiguity level, automation level, and interpretation version. A legal expert review should be required when a clause depends on open-textured terms, sector-specific regulator practice, sensitive personal information classification, public-opinion or social-mobilization capacity, label prominence, or the adequacy of "effective measures."

`Reviewed` currently means internally reviewed by the researcher unless a qualified legal expert review is separately recorded. The schemas therefore distinguish `author_review_status` from `legal_expert_review_status`. Conflicting interpretations should be represented by a new interpretation version or marked as `disputed`; superseded interpretations should remain traceable rather than silently overwritten.

## Schema Validation

`schema/legal-norm-schema.json` validates the structure of human-reviewed legal norms. It requires Chinese source text, working English translation, official source URL, promulgation date, effective date, and retrieval date. `schema/control-schema.json` validates executable controls derived from those norms. The validator checks required fields, source traceability, test logic, automation-level declaration, and separated author/legal-expert review status.

The validator now reports three top-level layers:

- `schema_valid`;
- `cross_file_valid`;
- `legal_source_metadata_complete`.

Cross-file checks compare `legal-corpus/source-index.csv`, `annotations/clause-decomposition.csv`, `mappings/traceability-matrix.csv`, `mappings/clause-to-control.yml`, and the example YAML files.

## Control Evaluation

`src/evaluator.py` supports a narrow expression subset and returns:

- `pass`;
- `fail`;
- `review`;
- `not_applicable`.

Fully automatable controls can reach final `pass` or `fail` directly when evidence is complete. Partially automatable controls return both a machine result and a final status: a machine expression may pass, but final status remains `review` unless required human confirmation is provided. Human-review-required controls default to `review` unless an explicit human review result is supplied. This prevents evidence fields such as `visible_label_present == true` from being treated as a complete legal conclusion about label prominence or statutory sufficiency.

## Validation Set

`examples/validation-cases.yml` contains a compact validation set rather than a large random dataset. The cases cover:

- applicable rules with sufficient evidence;
- applicable rules with missing evidence;
- clear failures;
- non-applicable rules;
- human-review-required obligations;
- multiple rules applying to the same use case.
- incorrect source mappings;
- missing source text;
- undeclared expression fields;
- explicit-label exception paths;
- model filing non-applicability and unreviewed applicability;
- simultaneous application of PIPL and Deep Synthesis consent rules;
- metadata aggregate flags that are true while required underlying fields are missing.

The validation focus is methodological consistency, not a statistical pass/fail distribution. The method checks schema completeness, source traceability, cross-file consistency, executable coverage, review-routing accuracy, and error behavior.

## Supplementary Proof of Concept

The legacy synthetic request pipeline remains available through:

```bash
python -m src.cli --seed 20260625
```

It generates synthetic operational artifacts under `outputs/`. These outputs are supplementary proof of concept only. They show that structured controls can be read and executed by software, but the project's main contribution is the legal-clause-to-control transformation method.

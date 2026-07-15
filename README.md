# China AIGC Legal-Clause-to-Control Framework

A research framework for transforming selected Chinese AIGC legal provisions into traceable, reviewable, and machine-readable compliance controls.

This repository studies how natural-language provisions from Chinese AIGC laws, regulations, and technical standards can be decomposed into structured legal norms and then translated into machine-readable controls. It does **not** try to be a user-facing compliance assessment product. The companion project [`ai-generated-actor-compliance`](https://github.com/yuxuancheng123-spec/ai-generated-actor-compliance) demonstrates how already-defined rules can be applied to concrete AI actor, digital human, and synthetic media cases. This repository focuses on the upstream research question: **where do the rules come from, and how can their legal interpretation be traced back to source clauses?**

All examples are synthetic or paraphrased for research use. The project does not use real personal data, face data, voice data, biometric data, contracts, company records, customer records, or production media.

## Research Focus

The central transformation chain is:

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

The machine-readable layer does not interpret law on its own. It executes structured legal interpretations that have been written and reviewed by a human.

## Research Questions

- **RQ1:** Chinese AIGC legal and regulatory provisions can be decomposed into which semantic elements for machine-readable representation?
- **RQ2:** How can traceable mappings be established between source clauses, legal interpretations, control objectives, evidence requirements, and executable tests?
- **RQ3:** Which categories of legal obligations are fully automatable, partially automatable, or dependent on human legal review?
- **RQ4:** Can the proposed transformation method generate consistent and executable controls for a synthetic actor and digital human use case?

## What This Repository Produces

- A small legal corpus of selected Chinese AIGC-related clauses.
- Clause decomposition annotations with semantic fields such as actor, modality, action, object, trigger, exception, timing, evidence, automation level, ambiguity level, and review status.
- JSON Schemas for legal norms and traceable controls.
- Clause-to-control mappings with source traceability.
- Example controls for consent, visible labeling, and model filing.
- A compact evaluator that can execute reviewed machine-readable tests and return `pass`, `fail`, `review`, or `not_applicable`.
- A small validation set that checks whether controls are traceable, executable, and correctly routed to human review when needed.

The previous synthetic request pipeline remains available as a supplementary proof of concept. It shows that structured controls can be read by software and exercised against synthetic operational records, but it is no longer the main research contribution.

## Repository Structure

```text
china-aigc-compliance-evidence/
├── legal-corpus/          # Source index and selected clause summaries
├── annotations/           # Legal semantic decomposition and interpretation notes
├── schema/                # Legal norm and control JSON Schemas
├── mappings/              # Clause-to-control mapping and traceability matrix
├── examples/              # Compact rule examples and validation cases
├── src/
│   ├── validator.py       # Schema and traceability validation for norms/controls
│   ├── evaluator.py       # Small reviewed-rule evaluator
│   └── ...                # Supplementary synthetic proof-of-concept pipeline
├── tests/                 # Regression and transformation-method tests
├── paper/                 # Refocused paper draft
├── article/               # Earlier article-support artifacts
├── outputs/               # Supplementary generated proof-of-concept outputs
├── README.md
└── references.md
```

## Minimal Example

```text
Source clause:
  Public-facing AI-generated synthetic content should carry explicit labels.

Structured legal norm:
  regulated_actor = generative_ai_service_provider
  modality = must
  action = add_explicit_label
  object = user_facing_generated_content
  trigger = output_is_user_facing and output_is_ai_generated

Control objective:
  User-facing generated content should carry a visible AIGC disclosure label before publication.

Required evidence:
  output_id, visible_label_present, checked_at

Machine-readable test:
  visible_label_present == true

Outcome:
  pass, fail, review, or not_applicable
```

## Automation Levels

Each mapped rule declares one of three automation levels:

- `fully_automatable`: The structured evidence can be checked mechanically, such as whether metadata fields exist.
- `partially_automatable`: Software can check some evidence, but legal or contextual review may still be needed, such as visible-label prominence.
- `human_review_required`: The obligation depends on open-textured legal judgment, such as whether "effective measures" were sufficient.

The evaluator supports four outcomes:

- `pass`: reviewed evidence satisfies the machine-readable test.
- `fail`: reviewed evidence contradicts the machine-readable test.
- `review`: evidence is missing, ambiguous, or legal judgment is required.
- `not_applicable`: the trigger conditions for the clause are not met.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.validator
python -m src.evaluator
python -m pytest
```

Supplementary proof-of-concept pipeline:

```bash
python -m src.cli --seed 20260625
```

That command regenerates synthetic request-level artifacts under `outputs/`. Those artifacts are useful for demonstrating that controls can be executed, but they are not the core research contribution.

## Selected Clause Scope

The selected corpus is intentionally limited. It covers representative clauses related to:

- consent and separate consent for sensitive personal information;
- actor, voice, face, or biometric-like material classification;
- visible AIGC labels;
- machine-readable or metadata labels;
- model filing or applicability review;
- content safety measures;
- complaint and reporting mechanisms.

The project does not attempt full coverage of Chinese AI law, sector-specific obligations, or production compliance workflows.

## Relationship To The Actor Compliance Demo

This repository produces machine-readable rules and traceability artifacts. It is not a user-facing compliance assessment product.

The separate `ai-generated-actor-compliance` project is the product-style demo that receives business facts, runs rules, and produces risk reports and remediation suggestions for concrete cases. In contrast, this repository studies how a rule is transformed from a legal clause into a reviewed, traceable, executable control.

## Limitations

- The clause summaries are research annotations, not official translations.
- The mappings are illustrative and require qualified legal review before operational use.
- The evaluator executes only human-reviewed structured interpretations.
- Several obligations are intentionally classified as `partially_automatable` or `human_review_required`.
- The synthetic proof-of-concept data do not demonstrate real-world legal compliance.
- No real personal, biometric, face, voice, contract, company, customer, or production media data are used.

## Legal Disclaimer

This project is for research, technical demonstration, and portfolio use only. It is not legal advice, does not certify compliance, and does not establish that any real system satisfies any law, regulation, standard, filing obligation, or regulator expectation.

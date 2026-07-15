# China AIGC Legal-Clause-to-Control Framework

A research framework for transforming selected Chinese AIGC legal provisions into traceable, reviewable, and machine-readable compliance controls.

This repository studies how natural-language provisions from Chinese AIGC laws, regulations, and technical standards can be decomposed into structured legal norms and then translated into machine-readable controls. It does **not** try to be a user-facing compliance assessment product. The companion project [`ai-generated-actor-compliance`](https://github.com/yuxuancheng123-spec/ai-generated-actor-compliance) demonstrates how already-defined rules can be applied to concrete AI actor, digital human, and synthetic media cases. This repository focuses on the upstream research question: **where do the rules come from, and how can their legal interpretation be traced back to source clauses?**

Current paper draft: [paper/main.tex](paper/main.tex). Its formal bibliography is maintained in [paper/references.bib](paper/references.bib); its planned independent-review materials are in [paper/review/](paper/review/).

Earlier supplementary prototype paper, superseded by the current legal-clause-to-control paper draft: [Making China AIGC Compliance Evidence Machine-Readable: A Governance Pipeline Prototype for Synthetic Actor and Digital Human Platforms](article/china-aigc-compliance-evidence-paper.pdf). The archived LaTeX package under `article/latex.zip` is likewise retained as a superseded prototype artifact.

All examples are synthetic or paraphrased for research use. The project does not use real personal data, face data, voice data, biometric data, contracts, company records, customer records, or production media.

## Research Focus

The central transformation chain is:

```text
Formal Chinese legal provision
-> Complete legal norm artifact
-> Human-confirmed interpretation and applicability
-> Machine-readable control
-> Evaluator execution
-> Machine result and human final conclusion
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
- One complete YAML legal norm artifact for every mapped `norm_id`.
- Clause-to-control mappings with source traceability.
- Example controls for consent, visible labeling, and model filing.
- A compact evaluator that can execute reviewed machine-readable tests and return `pass`, `fail`, `review`, or `not_applicable`.
- A small validation set that checks whether controls are traceable, executable, and correctly routed to human review when needed.

The previous synthetic request pipeline remains available as a supplementary proof of concept. It shows that structured controls can be read by software and exercised against synthetic operational records, but it is no longer the main research contribution.

## Legal Source Accuracy Updates

The current mapping corrects several source references and narrows automation boundaries:

- Complaint handling maps to Article 15 of the Interim Measures for the Management of Generative AI Services.
- Model filing maps to Article 17 of the Interim Measures and requires reviewed applicability fields before checking filing status.
- Deep synthesis confusion-risk labeling maps to Article 17 of the Deep Synthesis Provisions.
- Deep synthesis face and voice editing consent is modeled separately under Article 14 of the Deep Synthesis Provisions.
- Visible AIGC labeling is split into existence and prominence controls, and the Article 9 no-explicit-label exception path is represented as reviewable evidence rather than an automatic failure.
- An Article 9 exception result is limited to `provider_delivery`; it does not determine later public publication, user declarations, or dissemination-platform obligations.
- Deep Synthesis Article 14 is split between a direct provider prompt duty and a separately labelled derived organizational consent-assurance control.
- Metadata labeling checks underlying fields such as generated-content attribute, provider name or code, and content ID instead of relying only on an aggregate flag.

`Reviewed` currently means internally reviewed by the researcher unless a qualified legal expert review is separately recorded. The mapping files distinguish `author_review_status` from `legal_expert_review_status`.

## Repository Structure

```text
china-aigc-compliance-evidence/
├── legal-corpus/          # Source index and selected clause summaries
├── annotations/           # Legal semantic decomposition and interpretation notes
├── norms/                 # Canonical complete legal norm YAML artifacts
├── schema/                # Legal norm and control JSON Schemas
├── mappings/              # Clause-to-control mapping and traceability matrix
├── examples/              # Compact rule examples and validation cases
├── src/
│   ├── validator.py       # Schema and traceability validation for norms/controls
│   ├── evaluator.py       # Small reviewed-rule evaluator
│   └── ...                # Supplementary synthetic proof-of-concept pipeline
├── tests/                 # Regression and transformation-method tests
├── paper/                 # Refocused paper draft
│   ├── figures/            # TikZ research-method figure source
│   └── review/             # Planned independent-review protocol and templates
├── article/               # Earlier article-support artifacts
├── outputs/               # Supplementary generated proof-of-concept outputs
├── README.md
└── references.md
```

## Minimal Example

```text
Formal Chinese source clause
-> Structured norm: CN-AIGC-LABEL-001
-> Human-confirmed applicability
-> Visible-label existence control
-> Article 9 provider-delivery exception path
-> Prominence review control
-> Machine result
-> Final reviewed status

applicability:
  output_is_ai_generated: true
  output_is_user_facing: true
  output_matches_explicit_label_scenario: true

human_confirmations:
  output_matches_explicit_label_scenario:
    confirmed: true
    value: true
    reviewer_role: compliance_reviewer
    reviewed_at: "2026-07-15"

machine_result: pass
final_status: review
review_reason: label prominence still requires human review
```

The label-existence control can produce a machine result after the scenario has been human-confirmed. The separate prominence control remains `review` until a keyed human review record is completed. Article 9 only records whether provider-delivery exception evidence is complete; it does not decide downstream publication or dissemination obligations.

## Automation Levels

The repository distinguishes three layers of automation:

1. applicability determination;
2. evidence-test execution;
3. final compliance conclusion.

A machine-readable evidence test may be fully automatable even when legal applicability or the final conclusion requires human confirmation. Each control therefore carries an `automation_profile` with `applicability`, `evidence_test`, and `final_decision`; `automation_level` remains a compatibility summary of the final control posture.

Each mapped rule declares one of three automation levels:

- `fully_automatable`: The structured evidence can be checked mechanically, such as whether metadata fields exist.
- `partially_automatable`: Software can check some evidence, but final status remains `review` until the declared human-review key is completed.
- `human_review_required`: The obligation depends on open-textured legal judgment, such as whether "effective measures" were sufficient.

The evaluator supports four outcomes:

- `pass`: machine evidence satisfies a fully automatable control, or a required human review records a pass conclusion.
- `fail`: reviewed evidence contradicts the machine-readable test.
- `review`: evidence is missing, ambiguous, or legal judgment is required.
- `not_applicable`: the trigger conditions for the clause are not met.

## Runtime Evidence Validation

[evaluation-evidence-schema.json](schema/evaluation-evidence-schema.json) validates runtime `human_confirmations` and keyed `human_reviews` before validation cases enter the evaluator. The schema validates record structure; the evaluator separately checks semantic facts such as whether a confirmed value matches business evidence and whether the declared review key is complete.

Each norm also stores `source_excerpt_sha256`, the SHA-256 digest of `source_text_zh.strip().encode("utf-8")`. This detects changes to the repository's excerpt. Its `metadata_only` snapshot status does not assert that the excerpt has been independently verified word-for-word against the current official webpage.

## Paper Companion And Review Design

The paper companion distinguishes completed repository validation from planned independent validation. `paper/main.tex` cites primary legal, standards, and research sources from `paper/references.bib`; `paper/figures/transformation-pipeline.tex` renders the legal-clause-to-control method; and `paper/review/` provides blank templates for a second coder, a qualified legal reviewer, and transparent adjudication.

No independent second-coder agreement or qualified legal-expert conclusion is claimed. The proposed protocol reviews all 11 norms from the formal Chinese sources and preserves disagreements rather than overwriting them.

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
- Source validation confirms field completeness and repository consistency; it does not automatically prove that stored text is identical to the current official webpage.
- Article 9 handling is limited to provider delivery. The project does not automatically determine downstream public-distribution obligations.
- The evaluator executes only human-reviewed structured interpretations.
- Several obligations are intentionally classified as `partially_automatable` or `human_review_required`.
- The synthetic proof-of-concept data do not demonstrate real-world legal compliance.
- No real personal, biometric, face, voice, contract, company, customer, or production media data are used.

## Legal Disclaimer

This project is for research, technical demonstration, and portfolio use only. It is not legal advice, does not certify compliance, and does not establish that any real system satisfies any law, regulation, standard, filing obligation, or regulator expectation.

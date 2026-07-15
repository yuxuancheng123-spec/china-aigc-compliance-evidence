# Planned Independent Review Protocol

## Status

This is a proposed future-validation protocol. No independent second-coder or qualified legal-expert review has been completed for the current repository. All `legal_expert_review_status` values remain `not_reviewed` unless a future review record says otherwise.

## Scope

The corpus contains 11 canonical norm artifacts. A second coder should independently review all 11 rather than sample them. The reviewer should begin with the formal Chinese source and should not see the author's decomposition until the independent coding record is complete.

## Review A: Second-Coder Review

For each norm, the second coder records the source article, normative fragment, regulated actor, modality, action, object, trigger, exception, timing, ambiguity level, automation profile, control derivation type, and required evidence fields. The coder uses `second-coder-template.csv`; one row is completed for each field being compared.

Planned decision rules:

- Source and article match must reach 100% before the artifact is accepted for further study.
- Categorical fields are compared by exact agreement.
- Modality, automation profile, and derivation type may be summarized with Cohen's kappa.
- Trigger, exception, and evidence-field sets may be summarized with Jaccard similarity.
- A target exact agreement of at least 80% is a planning threshold for other structured fields, not a result currently achieved.
- Krippendorff's alpha may be reported only with a clear note that a corpus of 11 norms makes the estimate unstable.

## Review B: Legal-Expert Review

A qualified reviewer familiar with Chinese data protection, platform governance, or AI compliance should review the formal Chinese text and the proposed transformation. The review addresses:

- source article and source excerpt;
- fidelity of direct legal requirements;
- labelling of derived organizational controls;
- Article 9 provider-delivery scope;
- Article 14 provider-prompt and evidence-retention boundary;
- model-filing applicability;
- biometric and sensitive-personal-information classification;
- open-textured terms such as prominent labels and effective measures; and
- whether working translations introduce a material difference.

## Adjudication and Versioning

Every disagreement is recorded in `adjudication-log-template.csv`. Original author and reviewer values are retained; the project does not overwrite the historical record. Valid adjudication statuses are `accepted_author`, `accepted_reviewer`, `revised_by_consensus`, `needs_legal_expert_review`, and `disputed`. A substantive change increments the interpretation version and records its rationale. Unresolved issues remain `disputed` or `needs_legal_expert_review`.

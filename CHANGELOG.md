# Changelog

## Review-boundary fixes (after commit 9694fb3)

Targeted counterexamples (`examples/boundary-diagnostics.yml`) exposed defects that the designed validation cases did not. Each is now pinned by `tests/test_review_boundaries.py`.

- **Confirmed applicability.** A human confirmation was only checked for agreement with the business record, never against the value the trigger requires. A scenario confirmed as `false` therefore passed. The evaluator now returns `not_applicable` when a confirmed value does not satisfy the trigger.
- **Exception lifecycle scope.** `exception_path.lifecycle_stage` was descriptive only. The Article 9 exception now applies only when the runtime record's `lifecycle_stage` matches; a missing stage routes to `review`, and a different stage leaves the ordinary label test in force.
- **Human review attribution.** A completed human review now needs `reviewer_role` and `reviewed_at` before it can close a control; otherwise the control stays in `review`. The runtime evidence schema enforces this for completed reviews.
- **Metadata values.** Metadata expressions now reject empty strings as well as null values.
- **Deep Synthesis Article 14(2) prompt.** The provider-prompt control now requires evidence that the prompt covers obtaining the edited person's separate consent, not only informing them.
- **Source fidelity.** `CN-AIGC-SAFETY-001` previously stored a condensed paraphrase as `source_text_zh`. It now stores the verbatim lead sentence and item (1) of Article 4 from the official CAC text, with a new excerpt hash.
- **Annotation drift.** Eight `clause-decomposition.csv` entries had drifted from the canonical norm artifacts (actor, action, object). They are synchronised, and the validator now checks these fields.

## Legal design decisions (interpretation version 1.2 where changed)

- **Complaint duty split (GENAI Article 15).** `CTRL-AIGC-COMPLAINT-MECHANISM` now covers the standing duty (entry point, published process and feedback time limit) and applies whether or not a complaint has arrived; convenience (便捷) goes to keyed review. The new `CTRL-AIGC-COMPLAINT-HANDLING` covers acceptance, handling, and feedback for each complaint; timeliness (及时) goes to keyed review.
- **GB 45438-2025 fields.** `content_production_elements` was removed. Labeling Measures Article 5 uses 制作要素信息 as the umbrella term for attribute, provider, and content ID, not as a separate element. The control now checks five non-empty elements mapped to Label, ContentProducer, ProduceID, ContentPropagator, and PropagateID. At `metadata_write_stage: first_write`, the propagator fields must repeat the producer fields; this follows the author's reading of Appendix E Note 1 and should be re-verified against the standard text.
- **Filing scope (GENAI Article 17).** The control is explicitly limited to initial algorithm-filing status. Security assessment and change or cancellation filings are outside it, and the timing field no longer claims "before launch".
- **Negative-result policy.** On a control whose final decision requires human review, a failed evidence test now yields `machine_result: fail, final_status: review` until the keyed reviewer confirms the negative finding. A reviewer "pass" cannot overturn a failed evidence test; the evidence record must be corrected instead. Fully automatable and confirmation-gated controls still fail directly.

Still open: string encoding and serialisation of GB metadata are not checked; dissemination-stage rewrites beyond first write are not modelled.

## Legal source accuracy updates

The current mapping corrects several source references and narrows automation boundaries:

- Complaint handling maps to Article 15 of the Interim Measures for the Management of Generative AI Services.
- Model filing maps to Article 17 of the Interim Measures and requires reviewed applicability fields before checking filing status.
- Deep synthesis confusion-risk labeling maps to Article 17 of the Deep Synthesis Provisions.
- Deep synthesis face and voice editing consent is modeled separately under Article 14 of the Deep Synthesis Provisions.
- Visible AIGC labeling is split into existence and prominence controls, and the Article 9 no-explicit-label exception path is represented as reviewable evidence rather than an automatic failure.
- An Article 9 exception result is limited to `provider_delivery`; it does not determine later public publication, user declarations, or dissemination-platform obligations.
- Deep Synthesis Article 14 is split between a direct provider prompt duty and a separately labelled derived organizational consent-assurance control.
- Metadata labeling checks underlying fields such as generated-content attribute, provider name or code, and content ID instead of relying only on an aggregate flag.


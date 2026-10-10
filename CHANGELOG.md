# Changelog

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


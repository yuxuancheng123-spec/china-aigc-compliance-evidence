# Paper Draft

This folder contains the refocused paper draft for the legal-clause-to-control transformation framework.

Title:

`From Legal Provisions to Machine-Readable Controls: A Transformation Framework for China AIGC Governance`

The paper intentionally treats the legacy synthetic request pipeline as supplementary proof of concept rather than the central research result.

The paper companion now includes:

- `references.bib`: verified primary, official, standards, and preprint references used by `main.tex`;
- `figures/transformation-pipeline.tex`: a TikZ source diagram for the legal-clause-to-control pipeline;
- `review/`: a planned independent-review protocol and blank second-coder, legal-review, and adjudication templates.

The independent review is proposed future work. No second-coder agreement statistic or qualified legal-expert conclusion is reported in the current draft.

## Overleaf Compilation

Set the Overleaf compiler to **XeLaTeX**. `main.tex` uses `fontspec` and `xeCJK` with `FandolSong-Regular` so formal Chinese source text and Chinese bibliography titles render correctly. The archive preserves the `paper/` directory; set `paper/main.tex` as the project's main document after upload.

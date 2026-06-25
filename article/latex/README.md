# LaTeX Technical Paper Draft

This folder contains a technical-paper-style LaTeX draft for the **China AIGC Compliance Evidence Generator**.

## Files

- `main.tex` -- main paper source.
- `references.bib` -- BibTeX references.
- `figures/architecture_pipeline_fixed.pdf` -- readable three-layer architecture diagram.
- `tables/validation_results.tex` -- control-level validation results table.
- `tables/evidence_profile.tex` -- evidence profile table.
- `tables/regulatory_mapping.tex` -- regulatory mapping table.
- `OVERLEAF_INSTRUCTIONS.md` -- upload and compile instructions for Overleaf.

## Compile

The draft is configured for XeLaTeX on Overleaf.

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

The paper is a technical prototype draft. It does not claim to certify legal compliance.

# JURIX 2026 Short-Paper Version

This directory contains the JURIX 2026 short-paper submission version of the research paper.

- The file at paper/main.tex is the extended IEEE/portfolio research-paper version.
- The file at paper/jurix2026/main.tex is the JURIX 2026 short-paper submission version.

## Format

- Template: official IOS Press Book Article template.
- Class: unmodified IOS-Book-Article.cls copied from the official vtex-soft/texsupport.IOS-Book-Article repository.
- Bibliography style: unmodified official vancouver.bst.
- Review mode: single blind; the author name is intentionally retained.
- Compiler: XeLaTeX with BibTeX.

Compile from this directory:

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

The target is a five-page main text, with references beginning on page six or later. The local machine used to prepare this package does not have a complete XeLaTeX/BibTeX runtime, so page count and PDF generation must be verified in Overleaf or another full TeX installation before submission.

Current validated repository figures: 5 sources, 11 canonical norm artifacts, 12 scoped controls, 21 designed validation cases, and 46 passing automated tests.

This is a research submission draft. It reports no completed independent second-coder or qualified legal-expert review, and it does not claim legal compliance certification.

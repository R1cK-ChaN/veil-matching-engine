# Veil Matching Engine

This repository contains the CS5232 project work for formalising a simplified
price-time-priority matching engine in Veil.

The repository is organized into three main parts:

- `MatchingEngine.lean`, `MatchingEngine/`, `lakefile.toml`, `lean-toolchain`:
  the Lean and Veil verification project
- `docs/`: pseudo-spec, research notes, and working project plan
- `report/`: proposal source, paper source, and split paper sections

## Documentation

- [`docs/veil_pseudospec.md`](docs/veil_pseudospec.md): pseudo-spec for the
  matching engine state, transitions, and first proof targets
- [`docs/plan.md`](docs/plan.md): current project plan and verification status
- [`docs/deep-research-report.md`](docs/deep-research-report.md): background
  research notes used to shape the report

## Report Sources

- [`report/proposal.tex`](report/proposal.tex): project proposal source
- [`report/build_proposal_pdf.py`](report/build_proposal_pdf.py): proposal PDF
  builder
- [`report/paper.tex`](report/paper.tex): main paper entry file
- [`report/sections`](report/sections): split paper sections

## Building the Proposal PDF

Run:

```bash
python3 report/build_proposal_pdf.py
```

This generates `report/proposal.pdf` from `report/proposal.tex`.

## Building the Paper PDF

Run:

```bash
cd report
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
```

This generates `report/paper.pdf`.

## License

Released under the MIT License. See `LICENSE`.

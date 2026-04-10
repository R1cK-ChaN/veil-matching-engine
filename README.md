# Veil Matching Engine

This repository contains the CS5232 project work for formalising a simplified
price-time-priority matching engine in Veil.

The current repository includes:

- `proposal.tex`: the project proposal source
- `build_proposal_pdf.py`: a small script that renders the proposal PDF
- `docs/veil_pseudospec.md`: a proof-friendly Veil-flavored pseudo-spec for the
  minimal verified core

The formal development will be added here as the project progresses, including
the Veil model, proof artifacts, and supporting notes.

## Documentation

- [`docs/veil_pseudospec.md`](docs/veil_pseudospec.md): pseudo-spec for the
  matching engine state, transitions, and first proof targets

## Building the proposal PDF

Run:

```bash
python3 build_proposal_pdf.py
```

This generates `proposal.pdf` from `proposal.tex`.

## License

Released under the MIT License. See `LICENSE`.

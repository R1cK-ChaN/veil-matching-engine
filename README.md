# Formalising a Price-Time-Priority Matching Engine in Veil

CS5232 project -- a formally verified specification of a simplified electronic
limit-order matching engine, written in Lean 4 using the
[Veil](https://github.com/verse-lab/veil) framework for transition-system
verification.

## What this is

The specification models a single-asset, limit-order-only matching engine as a
relational transition system. Three actions define the system: `submit_buy` and
`submit_sell` place orders on the book, and `doMatch` executes a trade between
the best bid and best ask when their prices cross.

Seven safety properties are proved via Veil's SMT-based deductive checking,
supported by thirteen invariants:

| Property | Statement |
|---|---|
| Positive quantities | Active orders carry `qty > 0` |
| Trade traceability | Recorded trades have positive price and quantity |
| Trade provenance | Trade price traces to the ask; trade quantity traces to the bid |
| No self-dealing | Buyer and seller of every trade are distinct |
| Balance conservation | Traders uninvolved in any trade retain their initial balances |

All 84 deductive preservation checks pass (7 safety + 13 invariants + 1
doesNotThrow, across initialisation and 3 actions). A bounded model check over
2 traders and 3 order IDs finds no violations.

## Repository layout

    MatchingEngine/Engine.lean   Veil specification (main file)
    MatchingEngine.lean          import root
    lakefile.toml                Lean build configuration
    lean-toolchain               Lean toolchain version
    report/paper.tex             project report (LaTeX)
    report/sections/             report sections
    docs/                        pseudo-spec, research notes, project plan

## Building the specification

Requires Lean 4 and Lake. The Veil dependency is fetched automatically.

```bash
lake build
```

This type-checks the specification and runs `#check_invariants` and
`#model_check`.

## Building the report

```bash
cd report
pdflatex paper.tex
```

## License

Released under the MIT License. See `LICENSE`.

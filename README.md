# Formalising a Price-Time-Priority Matching Engine in Veil

CS5232 project — a formally verified specification of a simplified electronic
limit-order matching engine, written in Lean 4 using the
[Veil](https://github.com/verse-lab/veil) framework for transition-system
verification.

**Tagged release for submission:**
[`v1.0`](https://github.com/R1cK-ChaN/veil-matching-engine/releases/tag/v1.0)
&nbsp;·&nbsp;
**Repository:** public at <https://github.com/R1cK-ChaN/veil-matching-engine>

## What this is

The specification models a single-asset, limit-order-only matching engine as a
relational transition system. Three actions define the system: `submit_buy`
and `submit_sell` place orders on the book, and `doMatch` executes a trade
between the best bid and best ask when their prices cross.

Seven safety properties are proved via Veil's SMT-based deductive checking,
supported by thirteen invariants:

| Property | Statement |
|---|---|
| Positive quantities | Active orders carry `qty > 0` |
| Trade traceability | Recorded trades have positive price and quantity |
| Trade provenance | Trade price traces to the ask; trade quantity traces to the bid |
| No self-dealing | Buyer and seller of every trade are distinct |
| Balance conservation | Traders uninvolved in any trade retain their initial balances |

All 84 deductive preservation checks pass: 7 safety properties + 13 supporting
invariants + 1 generated `doesNotThrow` obligation, evaluated across
initialisation and the three actions (`submit_buy`, `submit_sell`, `doMatch`).
The deductive checker covers the **unbounded** model.

Bounded model checking (`#model_check`) is intentionally disabled — see
[Limitations](#limitations) below.

## Repository layout

    MatchingEngine/Engine.lean   Veil specification (main file)
    MatchingEngine.lean          import root
    lakefile.toml                Lean build configuration
    lean-toolchain               Lean toolchain version
    report/paper.tex             project report (LaTeX)
    report/sections/             report sections
    docs/veil_pseudospec.md      proof-friendly pseudo-spec (companion to Engine.lean)

## Building and verifying

Requires Lean 4 (toolchain pinned in `lean-toolchain`) and Lake. The Veil
dependency and its transitive deps (mathlib, cvc5, smt, …) are fetched
automatically on first build.

```bash
lake build
```

This type-checks the specification and runs `#check_invariants` (the SMT-based
deductive checker). Successful build means all 84 obligations passed.

### How long does verification take?

Times below are wall-clock on a Linux laptop (no special hardware).

| Step | Approximate time |
|---|---|
| First-time dependency fetch + build (mathlib, cvc5, Veil, …) | 15–30 minutes |
| Cold rebuild of `MatchingEngine.Engine` (84 SMT checks via cvc5) | ~1 minute |
| Incremental `lake build` with warm cache (no source change) | ~1 second |

A fresh re-elaboration via `lake lean MatchingEngine/Engine.lean` (which
bypasses lake's caching and replays everything) takes around **9 minutes**
on the same hardware; the difference is mostly olean reload overhead.

If the first build feels stuck on `mathlib` or `cvc5`, that is normal — those
two packages dominate the cold cache. Subsequent edits to `Engine.lean` only
re-run the local file.

## Examples and what to expect

The specification itself **is** the example. Open
`MatchingEngine/Engine.lean` and read top-to-bottom; the file is
self-contained and heavily commented.

The verification command at the bottom of the file does the work:

* `#check_invariants` &mdash; SMT-based deductive verification. On success
  Veil prints, for each of `init`, `submit_buy`, `submit_sell`, and `doMatch`,
  one line per declared `safety` / `invariant` plus a `doesNotThrow`
  obligation. **Expected output**: 84 green check marks, no failures.

If you want to *break* the spec to see what a failed check looks like, try
removing one of the supporting invariants (for example the `bid_ask_disjoint`
line) and rebuild — `#check_invariants` will then flag the safety property
that depended on it.

### Worked execution trace

A concrete sequence the model accepts:

1. `submit_buy(T1, oid=1, px=10, qty=5)` adds order 1 to the bid book.
2. `submit_sell(T2, oid=2, px=8, qty=5)` adds order 2 to the ask book.
3. `doMatch(1, 2)` fires: prices cross (10 ≥ 8), quantities match, traders
   differ, balances suffice → trade record `(1, 2, px=8, qty=5)` is
   appended; T1 loses 40 cash and gains 5 asset; T2 gains 40 cash and loses
   5 asset.

The proven safety properties pin down exactly this behaviour: the recorded
quantity equals the bid quantity, the recorded price equals the ask price,
buyer and seller differ, and any trader who never appears in a trade keeps
their initial balance.

## Limitations

* **Bounded model checking is disabled.** Veil's `#model_check` requires a
  `Veil.Enumeration` instance for each action's argument tuple. Both
  `submit_buy` and `submit_sell` carry `Nat`-typed price and quantity
  arguments, and `Nat` has no finite enumeration. To allow `#gen_spec` (which
  derives `Enumeration` for the action-label sum) to succeed, the
  specification declares a *stub* `Enumeration Nat` instance whose `complete`
  field is filled by `sorry`. The stub is never evaluated — `#model_check` is
  commented out and `#check_invariants` does not need it. Re-enabling the
  bounded check would require restricting price and quantity to a bounded
  type (e.g. `Fin N`), which would narrow the abstract model. The deductive
  result already covers the unbounded model.
* **No partial fills, no cancellations, no market orders.** The model covers
  full-quantity matches between equal-quantity bid/ask pairs.
* **Frame conservation only.** The accounting invariant says traders not
  involved in any trade keep their initial balances; a global sum-conservation
  theorem (`sum cash = sum initCash`) cannot be expressed in the first-order
  fragment Veil targets.
* **Single asset.**

## Building the report

```bash
cd report
pdflatex paper.tex
```

Pre-built: `report/paper.pdf`.

## License

Released under the MIT License. See `LICENSE`.

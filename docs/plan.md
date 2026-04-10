# Project Plan: Verified Price-Time-Priority Matching Engine

## Goal

Build a clean, formally verified core of a simplified electronic matching
engine in Veil.

The project goal is to prove that a single-asset, limit-order-only matching
engine:

- respects price-time priority
- preserves cash and asset conservation
- only records trades that come from real live orders
- maintains a well-formed bid and ask book

This project is about correctness, not low-latency production engineering.

## Current Scope

The current baseline is the minimal verified core from
[`veil_pseudospec.md`](veil_pseudospec.md):

- single asset
- limit orders only
- buy book sorted by price descending, then time ascending
- sell book sorted by price ascending, then time ascending
- transitions:
  - `submit_buy`
  - `submit_sell`
  - `match`
- no cancellation in v1
- no partial fills in v1
- `match` only when the head bid and head ask have equal quantity

This scope is intentionally narrow so the core theorems are finishable by the
course deadline.

## Non-Goals

The following are explicitly out of scope for the first complete version:

- market orders
- multiple assets
- protocol-level exchange connectivity
- low-latency optimisation
- fault-tolerant distributed architecture
- production regulatory controls
- complex priority overlays
- benchmarking focused on throughput or tail latency

These can be discussed in background and future work, but they should not drive
the formal model now.

## Main Proof Targets

The first proof targets are:

- `submit_buy_preserves_wf`
- `submit_sell_preserves_wf`
- `match_preserves_wf`
- `submit_transitions_preserve_conserved`
- `match_preserves_conserved`
- `match_uses_best_bid`
- `match_uses_best_ask`
- `match_trade_is_traceable`

Interpretation:

- `wf` means both books are sorted, side-correct, and contain only positive
  quantities
- `conserved` means total cash and total asset quantity stay equal to their
  initial totals
- head-selection theorems are the local proof form of price-time priority
- traceability means each trade log entry is justified by the pre-state

## Workstreams

### 1. Veil Model

Implement the abstract state and transitions:

- core types: `Order`, `Trade`, `Balance`, `State`
- ordering predicates: `better_bid`, `better_ask`
- state predicates: `bid_book_sorted`, `ask_book_sorted`, `wf`, `conserved`
- transitions: `submit_buy`, `submit_sell`, `match`

Deliverable:

- a runnable Veil specification for the minimal model

### 2. Lean Helper Lemmas

Use Lean for obligations that are awkward to discharge directly in Veil:

- insertion preserves sortedness for bids
- insertion preserves sortedness for asks
- head of sorted bid book has highest priority
- head of sorted ask book has highest priority
- updating two balances preserves total cash
- updating two balances preserves total asset

Deliverable:

- a Lean file containing the helper lemmas required by the Veil invariants

### 3. Verification Experiments

Run bounded checks to find specification mistakes early, then use invariant
checking for the main results.

Deliverable:

- a short results section summarising what was checked, at what bounds, and
  what passed or failed

### 4. Report Writing

Build the paper around the actual verified core rather than around speculative
stretch goals.

Deliverable:

- a complete paper with system model, formalisation, experiments, and
  limitations

## Milestone Plan

### Milestone 1: Stable Formal Core

Target output:

- pseudo-spec frozen
- Veil state and transition signatures written
- basic well-formedness predicates written

Definition of done:

- the model compiles or parses cleanly enough to start bounded checking
- no unresolved design decision remains about state shape or transition shape

### Milestone 2: Book Invariants

Target output:

- sortedness and side-correctness encoded
- submission transitions preserve `wf`

Definition of done:

- `submit_buy_preserves_wf`
- `submit_sell_preserves_wf`

### Milestone 3: Matching Correctness

Target output:

- `match` transition encoded
- local best-order selection theorems stated and proved
- trade traceability stated and proved

Definition of done:

- `match_preserves_wf`
- `match_uses_best_bid`
- `match_uses_best_ask`
- `match_trade_is_traceable`

### Milestone 4: Accounting Invariants

Target output:

- balances fully integrated into the proof
- conservation invariant proved for all core transitions

Definition of done:

- `submit_transitions_preserve_conserved`
- `match_preserves_conserved`

### Milestone 5: Experiments and Write-Up

Target output:

- bounded model-checking results documented
- invariant-checking results documented
- paper sections aligned with what was actually proved

Definition of done:

- experiment notes are written
- paper has concrete results, not placeholder claims

## Experiment Plan

This project needs verification experiments, not systems-performance
benchmarks.

### Experiment 1: Small-Instance Model Checking

Purpose:

- catch specification bugs before investing in full proofs

Inputs to vary:

- number of accounts
- maximum outstanding orders
- bounded price range
- bounded quantity range

Checks:

- crossed-book violations
- FIFO or best-price violations
- impossible trades
- quantity inconsistencies
- missing side conditions on transitions

Outputs to record:

- largest bounds explored
- whether a counterexample was found
- what property failed
- whether the issue was a spec bug or a missing invariant

### Experiment 2: Invariant Checking

Purpose:

- determine whether the chosen invariants are strong enough to make the core
  safety results inductive

Inputs to vary:

- candidate invariant set
- helper lemmas enabled or required

Checks:

- whether `#check_invariants` succeeds
- what counterexamples to induction appear
- which invariants had to be strengthened

Outputs to record:

- final invariant set
- failed proof attempts and their cause
- helper lemmas imported from Lean

### Experiment 3: Optional Executable Cross-Check

Only do this if the core Veil proof is stable early.

Purpose:

- compare a Velvet-style matching loop against the abstract transition relation

Inputs to vary:

- short bounded event traces
- different book shapes within the supported scope

Checks:

- whether the executable loop produces the same residual books and trades as
  the abstract step relation

Outputs to record:

- number of traces checked
- mismatches, if any
- supported subset of the full model

## Data Plan

This project does not need real market data.

### Data Sources

Use only synthetic or bounded formal inputs:

- small account universes
- bounded prices
- bounded quantities
- short event traces
- hand-written corner cases

### Why Synthetic Data Is Enough

The goal is to verify semantic correctness of the model, not fit or replay a
real market. Real exchange data would add complexity without improving the
proof argument for the current scope.

### Required Data Sets

Prepare at least these input categories:

- empty-book submission cases
- same-price FIFO cases
- best-bid and best-ask crossing cases
- impossible-match guard cases
- conservation-sensitive cases with different account balances

### Recommended Trace Shapes

Use small deterministic traces such as:

1. single buy then single matching sell
2. two buys at same price with different timestamps, then one sell
3. two buys at different prices, then one sell
4. unmatched orders that should remain in the book
5. insufficient balance or asset cases blocked by guards

### Result Artifacts to Save

Save experiment outputs in a reproducible way:

- model-checking bounds used
- seeds, if randomness is introduced
- counterexample traces
- theorem checklist with pass or fail state
- notes on each invariant added or strengthened

## Report Plan

The paper should follow the current section layout in `paper.tex` and
`paper_sections/`.

Recommended emphasis by section:

- Introduction:
  - define the problem and explain the narrow scope
- Background and Related Work:
  - explain continuous double auctions, price-time priority, and why Veil fits
- System Model:
  - define state, scope, and transitions
- Formal Specification:
  - explain the representation choices and execution rule
- Safety Properties:
  - define exactly what is proved
- Verification Strategy:
  - explain Veil plus Lean division of labour
- Experiment Skeleton:
  - replace placeholders with actual bounded-check results
- Limitations:
  - state clearly what is omitted and why
- Conclusion:
  - summarise the verified core and stretch goals

## Suggested Repository Outputs

Expected key artifacts by the end:

- `docs/veil_pseudospec.md`
- `docs/plan.md`
- Veil source files for the model and invariants
- Lean helper lemma files
- paper source under `paper.tex` and `paper_sections/`
- a small note or table of experiment results

Suggested future result locations:

- `results/model-checking.md`
- `results/invariants.md`
- `results/counterexamples/`

These paths do not need to be created immediately, but the results should be
kept separate from the paper draft.

## Risks and Fallbacks

### Main Risk: State-Space Explosion

Problem:

- two ordered books, balances, and a trade log can make bounded checking grow
  quickly

Fallback:

- reduce account count
- reduce price and quantity ranges
- keep no-cancellation and no-partial-fill restrictions
- prove the local step property first: each `match` chooses the current best
  bid and ask

### Main Risk: Invariants Not Inductive

Problem:

- the obvious top-level properties may fail unless helper invariants are added

Fallback:

- strengthen `wf`
- add explicit uniqueness and positivity predicates
- move arithmetic or ordering facts into Lean lemmas

### Main Risk: Stretch Goals Disrupt the Core

Problem:

- cancellation or partial fills can derail the schedule

Fallback:

- freeze the minimal verified core first
- treat stretch goals as optional and only attempt them after the core proof is
  stable

## Acceptance Criteria

The project counts as successful if it produces:

- a precise Veil model of the minimal matching engine
- at least one checked safety theorem over the reachable state space
- a convincing argument for price-time head selection
- a conservation argument over cash and assets
- a trade-provenance result
- a short paper that reports the actual verified scope and actual experiments

The project does not need to include:

- cancellation
- partial fills
- real market data
- production performance evaluation

## Immediate Next Steps

1. Freeze the minimal model in Veil source form based on `veil_pseudospec.md`.
2. Encode `wf` and `conserved` first.
3. Prove the two submission preservation theorems before touching stretch
   features.
4. Add bounded checks for tiny instances as soon as the state and transitions
   exist.
5. Record counterexamples and invariant changes as you go, so the report is
   written from real evidence instead of reconstruction later.

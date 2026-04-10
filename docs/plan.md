# Project Plan: Verified Price-Time-Priority Matching Engine

## Goal

Build and document a formally verified core of a simplified electronic matching
engine in Veil.

The project goal is to show that a single-asset, limit-order-only matching
engine:

- maintains a well-formed bid and ask book
- respects price-time best-order selection
- only records trades with valid provenance fields
- preserves balance-related safety properties in the fragment that Veil can
  express directly

This project is about correctness, not low-latency production engineering.

## Current Status

The repository already contains a working Lean and Veil project:

- `MatchingEngine/Engine.lean`: verified matching-engine model
- `MatchingEngine.lean`: root import
- `lean-toolchain`: Lean 4.27.0
- `lakefile.toml`: Veil and mathlib dependencies
- `docs/veil_pseudospec.md`: proof-friendly pseudo-spec
- `report/paper.tex` and `report/sections/`: paper source
- `report/proposal.tex`: proposal source

Current verified result:

- `lake build` succeeds
- `#check_invariants` passes for all declared properties
- `#model_check { trader := Fin 2, orderId := Fin 3 }` reports no violation

Verified counts from the current engine source:

- 3 actions:
  - `submit_buy`
  - `submit_sell`
  - `doMatch`
- 7 safety properties
- 13 invariants
- 21 properties checked per verification block:
  - 1 `doesNotThrow`
  - 7 safety properties
  - 13 invariants
- 4 verification blocks:
  - initialization
  - `doMatch`
  - `submit_sell`
  - `submit_buy`
- total reported checks:
  - 84 invariant/safety preservation checks
  - 1 bounded model check
  - 85 total checks

## Actual Model in the Repo

The current implementation is slightly different from the original
list-oriented pseudo-spec.

Implemented design:

- relational encoding rather than explicit sorted sequences
- ghost predicates `betterBid`, `betterAsk`, `isBestBid`, `isBestAsk`
- no cancellation
- no partial fills
- `doMatch` requires equal buy and sell quantities
- `doMatch` forbids self-trade
- balances are mutable, with immutable `initCash` and `initAsset` used for
  frame-style conservation properties

This design is more SMT-friendly than a list-based encoding and is the version
that currently verifies.

## Scope

Current baseline scope:

- single asset
- limit orders only
- no cancellation
- no partial fills
- best bid and best ask selected by first-order predicates
- bounded model checking over a tiny finite instance

Out of scope for the first complete version:

- market orders
- multiple assets
- protocol-level exchange connectivity
- throughput or tail-latency benchmarking
- distributed or fault-tolerant architecture
- production regulatory controls
- venue-specific priority overlays

## What Is Proved Now

### Safety Properties

The current engine proves these 7 safety properties:

- `bid_positive_qty`
- `ask_positive_qty`
- `trade_has_qty`
- `trade_has_px`
- `trade_qty_from_bid`
- `trade_px_from_ask`
- `trade_no_self_deal`

Interpretation:

- active orders have positive quantities
- every recorded trade has positive quantity and price
- trade quantity comes from the bid side
- trade price comes from the ask side
- buyer and seller are distinct

### Invariants

The current engine proves these 13 invariants:

- `bid_ask_disjoint`
- `ts_mono_bid`
- `ts_mono_ask`
- `ts_unique_bid`
- `ts_unique_ask`
- `no_reuse_bid`
- `no_reuse_ask`
- `traded_not_in_ask`
- `traded_not_in_bid`
- `bid_positive_px`
- `ask_positive_px`
- `cash_conserved_no_trade`
- `asset_conserved_no_trade`

Interpretation:

- an order ID cannot be live on both sides
- active orders have timestamps below `next_ts`
- active timestamps are unique per side
- matched orders are not reused in the live books
- active prices stay positive
- traders uninvolved in all trades keep their initial balances

## Mapping to Original Pseudo-Spec Goals

The current verification result partially realizes the pseudo-spec targets in
`docs/veil_pseudospec.md`.

Already covered in the current model:

- submission preserves positivity and disjointness properties
- matching preserves the declared well-formedness-style invariants
- best-order selection is encoded as a precondition through `isBestBid` and
  `isBestAsk`
- trade fields are tied back to the matched orders
- balance updates satisfy the current frame-style conservation statements

Not yet fully realized in the stronger pseudo-spec sense:

- no explicit list-based `wf` predicate
- no global sum-based conservation theorem over all traders
- no explicit theorem naming layer matching the pseudo-spec theorem names
- no cancellation
- no partial fills

This is acceptable for the current milestone, but the report should state this
difference clearly instead of overstating what is proved.

## Workstreams

### 1. Verified Core

Status: complete for the current milestone.

Implemented:

- abstract types for traders and order IDs
- mutable state for books, balances, trades, and timestamps
- ghost ordering predicates
- `submit_buy`, `submit_sell`, and `doMatch`
- deductive verification and bounded model checking

### 2. Experiment and Validation Notes

Status: partially complete.

Already available:

- build success
- invariant-check success
- bounded model-check success on `Fin 2` traders and `Fin 3` order IDs

Still needed:

- write the experiment results into the paper
- record the meaning of the 85 checks in a report-friendly table
- document the model-check bound explicitly in prose

### 3. Report Writing

Status: in progress.

Already available:

- `report/paper.tex`
- split section files under `report/sections/`

Still needed:

- replace “skeleton” wording with final prose
- update the experiment section from plan to actual results
- explain the gap between pseudo-spec conservation and implemented
  frame-style conservation
- add a short implementation section describing the relational encoding choice

### 4. Stretch Extensions

Status: not started, and should stay blocked until the report of the current
verified core is stable.

Potential extensions:

- explicit theorem wrappers with names closer to the pseudo-spec
- cancellation
- partial fills
- stronger accounting theorem if expressible in a richer setting
- optional Velvet executable matching loop

## Experiment Plan

This project needs verification experiments, not systems-performance
benchmarks.

### Experiment 1: Deductive Invariant Checking

Purpose:

- establish that initialization and each action preserve the full declared
  safety and invariant set

Current result:

- passes for initialization, `doMatch`, `submit_sell`, and `submit_buy`

What to report:

- number of safety properties
- number of invariants
- number of action-preservation blocks
- total checks

### Experiment 2: Bounded Model Checking

Purpose:

- search for concrete counterexamples in a tiny finite instance

Current bound:

- `trader := Fin 2`
- `orderId := Fin 3`
- `initCash := 100`
- `initAsset := 100`

Current result:

- no violation found
- explored 1 state

What to report:

- exact bound
- theory values supplied to the model checker
- whether any violation was found
- how limited the explored state space is

### Experiment 3: Trace-Based Manual Scenarios

Purpose:

- provide simple human-readable examples in the paper even if they are not part
  of the formal proof output

Recommended scenarios:

1. a single buy followed by a matching sell
2. two competing bids with one designated best bid
3. a blocked match due to insufficient cash or asset
4. a no-self-trade example

These can be described informally in the report even if not encoded as a
separate executable test harness.

## Data Plan

This project does not need real market data.

Use only synthetic or bounded formal inputs:

- finite trader universes
- finite order-ID universes
- bounded price and quantity values
- hand-written scenario descriptions

Why this is sufficient:

- the goal is to verify the model semantics
- real market data would not strengthen the current deductive proof result
- the current model-checking setup is already finite and synthetic by design

Result artifacts worth preserving:

- build success notes
- verification counts
- exact model-check bounds
- any future counterexamples if the model changes
- paper-ready summary tables

## Immediate Next Steps

1. Update the paper sections so the experiment section reports the actual 85
   checks and the bounded model-check result.
2. Add a short section explaining why the implementation uses relational
   `isBestBid` and `isBestAsk` instead of explicit sorted lists.
3. State clearly in the paper that the current conservation result is a
   frame-style property, not full global sum conservation.
4. Decide whether to stop at the current verified core or attempt one stretch
   feature after the report text is stable.

## Acceptance Criteria

The project counts as successful if it contains:

- a precise Veil model of the minimal matching engine
- a successful `lake build`
- a complete safety and invariant story for the current engine
- a bounded model-check result documented with explicit bounds
- a paper that accurately describes what is actually proved

The project does not need to contain:

- cancellation
- partial fills
- real market data
- production-style performance evaluation
- stronger claims than the current verified model supports

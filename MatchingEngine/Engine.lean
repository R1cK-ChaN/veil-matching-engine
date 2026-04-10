import Veil

/-!
# Verified Price-Time-Priority Matching Engine

A formally verified core of a single-asset, limit-order-only matching engine.
Based on the pseudo-specification in `docs/veil_pseudospec.md`.

## Design Decisions

- **Relational encoding**: State uses `relation` and `function` (not `List`-typed
  `individual`) so that `#check_invariants` (SMT-based deductive verification) works.
- **Best-bid/ask predicates**: Instead of encoding sorted lists and checking heads,
  we define "best bid/ask" directly as first-order predicates over the relation.
  This is equivalent but SMT-friendly.
- **Separate `cash`/`asset` functions**: Avoids structure field access issues in
  Veil's DSL and lets SMT reason about each independently.
- **No self-trade**: `doMatch` requires `bidWho b ≠ askWho a` to simplify the
  universal balance assignment (avoids buyer = seller overlap).

## Scope

- Single asset, limit orders only
- No cancellation, no partial fills
- `doMatch` requires equal quantities at the head
-/

veil module MatchingEngine

-- ═══════════════════════════════════════════════════════════════════════════
-- Abstract types
-- ═══════════════════════════════════════════════════════════════════════════

type trader
type orderId

-- ═══════════════════════════════════════════════════════════════════════════
-- State declarations (relational encoding)
-- ═══════════════════════════════════════════════════════════════════════════

-- Bid book: membership and per-order fields
relation inBid : orderId → Bool
function bidWho : orderId → trader
function bidPx  : orderId → Nat
function bidQty : orderId → Nat
function bidTs  : orderId → Nat

-- Ask book: membership and per-order fields
relation inAsk : orderId → Bool
function askWho : orderId → trader
function askPx  : orderId → Nat
function askQty : orderId → Nat
function askTs  : orderId → Nat

-- Balances (mutable, updated by doMatch)
function cash  : trader → Nat
function asset : trader → Nat

-- Initial balances (immutable, for conservation invariants)
immutable function initCash  : trader → Nat
immutable function initAsset : trader → Nat

-- Trade log (indexed by buy-orderId × sell-orderId)
relation tradeExists : orderId → orderId → Bool
function tradePx     : orderId → orderId → Nat
function tradeQty    : orderId → orderId → Nat

-- Monotonic timestamp counter
individual next_ts : Nat

#gen_state

-- ═══════════════════════════════════════════════════════════════════════════
-- Initial state
-- ═══════════════════════════════════════════════════════════════════════════

after_init {
  inBid O := false
  inAsk O := false
  -- Order fields are nondeterministic for inactive orders.
  -- Invariants only constrain these when inBid/inAsk is true.
  cash T := initCash T
  asset T := initAsset T
  tradeExists B A := false
  tradePx B A := 0
  tradeQty B A := 0
  next_ts := 0
}

-- ═══════════════════════════════════════════════════════════════════════════
-- Ghost relations: ordering predicates
-- ═══════════════════════════════════════════════════════════════════════════

-- Bid priority: higher price wins; ties broken by earlier timestamp (FIFO)
ghost relation betterBid (o1 o2 : orderId) :=
  bidPx o1 > bidPx o2 ∨
  (bidPx o1 = bidPx o2 ∧ bidTs o1 < bidTs o2)

-- Ask priority: lower price wins; ties broken by earlier timestamp (FIFO)
ghost relation betterAsk (o1 o2 : orderId) :=
  askPx o1 < askPx o2 ∨
  (askPx o1 = askPx o2 ∧ askTs o1 < askTs o2)

-- Best bid: in the book and no other active bid has higher priority
ghost relation isBestBid (b : orderId) :=
  inBid b ∧ ∀ o, (inBid o ∧ o ≠ b) → betterBid b o

-- Best ask: in the book and no other active ask has higher priority
ghost relation isBestAsk (a : orderId) :=
  inAsk a ∧ ∀ o, (inAsk o ∧ o ≠ a) → betterAsk a o

-- ═══════════════════════════════════════════════════════════════════════════
-- Actions (transitions)
-- ═══════════════════════════════════════════════════════════════════════════

-- Submit a buy (bid) order with an explicit limit price and quantity.
action submit_buy (who_param : trader) (oid : orderId) (px qty : Nat) {
  require ¬ inBid oid
  require ¬ inAsk oid
  require ∀ x, ¬ tradeExists oid x
  require ∀ x, ¬ tradeExists x oid
  require px > 0
  require qty > 0
  inBid oid := true
  bidWho oid := who_param
  bidPx oid := px
  bidQty oid := qty
  bidTs oid := next_ts
  next_ts := next_ts + 1
}

-- Submit a sell (ask) order with an explicit limit price and quantity.
action submit_sell (who_param : trader) (oid : orderId) (px qty : Nat) {
  require ¬ inBid oid
  require ¬ inAsk oid
  require ∀ x, ¬ tradeExists oid x
  require ∀ x, ¬ tradeExists x oid
  require px > 0
  require qty > 0
  inAsk oid := true
  askWho oid := who_param
  askPx oid := px
  askQty oid := qty
  askTs oid := next_ts
  next_ts := next_ts + 1
}

-- Match the best bid against the best ask.
action doMatch (b a : orderId) {
  -- Best-order selection
  require isBestBid b
  require isBestAsk a
  -- Price crossing
  require bidPx b ≥ askPx a
  -- Equal quantity (v1: no partial fills)
  require bidQty b = askQty a
  -- No self-trade
  require bidWho b ≠ askWho a
  -- Sufficient balances
  require cash (bidWho b) ≥ askPx a * bidQty b
  require asset (askWho a) ≥ bidQty b

  let p := askPx a
  let q := bidQty b
  let buyer := bidWho b
  let seller := askWho a

  -- Remove matched orders from books
  inBid b := false
  inAsk a := false

  -- Update balances (universal assignment; buyer ≠ seller guaranteed)
  cash T := if T = buyer then cash T - p * q
            else if T = seller then cash T + p * q
            else cash T
  asset T := if T = buyer then asset T + q
             else if T = seller then asset T - q
             else asset T

  -- Record trade
  tradeExists b a := true
  tradePx b a := p
  tradeQty b a := q

  next_ts := next_ts + 1
}

-- ═══════════════════════════════════════════════════════════════════════════
-- Safety properties (main proof targets from pseudospec)
-- ═══════════════════════════════════════════════════════════════════════════

-- Well-formedness: active orders have positive quantities
safety [bid_positive_qty] inBid O → bidQty O > 0
safety [ask_positive_qty] inAsk O → askQty O > 0

-- Trade traceability: every recorded trade has valid price and quantity
safety [trade_has_qty] tradeExists B A → tradeQty B A > 0
safety [trade_has_px]  tradeExists B A → tradePx B A > 0

-- Trade provenance: trade fields trace back to the original orders
safety [trade_qty_from_bid] tradeExists B A → tradeQty B A = bidQty B
safety [trade_px_from_ask]  tradeExists B A → tradePx B A = askPx A
safety [trade_no_self_deal] tradeExists B A → bidWho B ≠ askWho A

-- ═══════════════════════════════════════════════════════════════════════════
-- Invariants (supporting properties for inductive proofs)
-- ═══════════════════════════════════════════════════════════════════════════

-- An order ID cannot be simultaneously in both books
invariant [bid_ask_disjoint] ¬ (inBid O ∧ inAsk O)

-- Timestamps of active orders are strictly less than next_ts
invariant [ts_mono_bid] inBid O → bidTs O < next_ts
invariant [ts_mono_ask] inAsk O → askTs O < next_ts

-- Active orders in the same book have distinct timestamps
invariant [ts_unique_bid] inBid O1 ∧ inBid O2 ∧ O1 ≠ O2 → bidTs O1 ≠ bidTs O2
invariant [ts_unique_ask] inAsk O1 ∧ inAsk O2 ∧ O1 ≠ O2 → askTs O1 ≠ askTs O2

-- Matched orders are no longer in either book
invariant [no_reuse_bid] tradeExists B A → ¬ inBid B
invariant [no_reuse_ask] tradeExists B A → ¬ inAsk A

-- Traded order IDs were never resubmitted to either book
invariant [traded_not_in_ask] tradeExists O A → ¬ inAsk O
invariant [traded_not_in_bid] tradeExists B O → ¬ inBid O

-- Active orders have positive prices
invariant [bid_positive_px] inBid O → bidPx O > 0
invariant [ask_positive_px] inAsk O → askPx O > 0

-- Conservation: a trader not involved in any trade retains initial balances.
-- Global sum-based conservation (total_cash = INIT_CASH) cannot be expressed
-- in FOL; this frame property is the strongest statement in Veil's fragment.
invariant [cash_conserved_no_trade]
  (∀ B A, tradeExists B A → bidWho B ≠ T) →
  (∀ B A, tradeExists B A → askWho A ≠ T) →
  cash T = initCash T
invariant [asset_conserved_no_trade]
  (∀ B A, tradeExists B A → bidWho B ≠ T) →
  (∀ B A, tradeExists B A → askWho A ≠ T) →
  asset T = initAsset T

-- ═══════════════════════════════════════════════════════════════════════════
-- Specification generation and verification
-- ═══════════════════════════════════════════════════════════════════════════

#gen_spec

-- SMT-based deductive verification
#check_invariants

-- Bounded model checking (2 traders, 3 order IDs)
-- Theory components (immutable functions) must be provided for model checking.
#model_check { trader := Fin 2, orderId := Fin 3 }
  { initCash := fun _ => 100, initAsset := fun _ => 100 }

end MatchingEngine

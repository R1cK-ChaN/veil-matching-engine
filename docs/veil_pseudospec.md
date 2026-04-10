# Veil Matching Engine Pseudo-Spec

This document gives a proof-friendly, Veil-flavored pseudo-spec for the
minimal verified core of the matching engine project.

Design choices:

- single asset
- bid and ask books represented as sorted sequences
- no cancellation
- matching only at the heads of the two books
- no partial fills in the first version: `match` requires equal quantities

## Core Types

```text
type Trader
type OrderId
type Price
type Qty
type Time

datatype Side = Buy | Sell

record Order {
  oid  : OrderId
  who  : Trader
  side : Side
  px   : Price
  qty  : Qty
  ts   : Time
}

record Balance {
  cash  : Nat
  asset : Nat
}

record Trade {
  buy_oid  : OrderId
  sell_oid : OrderId
  buy_who  : Trader
  sell_who : Trader
  px       : Price
  qty      : Qty
  ts       : Time
}

record State {
  bids     : Seq Order
  asks     : Seq Order
  balances : Map Trader Balance
  trades   : Seq Trade
  next_ts  : Time
}
```

## Order Priority and Sortedness

```text
pred better_bid(o1, o2) :=
  o1.px > o2.px ||
  (o1.px = o2.px && o1.ts < o2.ts)

pred better_ask(o1, o2) :=
  o1.px < o2.px ||
  (o1.px = o2.px && o1.ts < o2.ts)

pred bid_book_sorted(bs) :=
  forall i j.
    0 <= i < j < len(bs) -> better_bid(bs[i], bs[j])

pred ask_book_sorted(as) :=
  forall i j.
    0 <= i < j < len(as) -> better_ask(as[i], as[j])
```

## Well-Formedness Invariant

```text
pred wf(s) :=
  bid_book_sorted(s.bids) &&
  ask_book_sorted(s.asks) &&
  forall i. 0 <= i < len(s.bids) -> s.bids[i].side = Buy  && s.bids[i].qty > 0 &&
  forall i. 0 <= i < len(s.asks) -> s.asks[i].side = Sell && s.asks[i].qty > 0
```

## Conservation Invariant

```text
fun total_cash(s)  := sum_t s.balances[t].cash
fun total_asset(s) := sum_t s.balances[t].asset

const INIT_CASH  : Nat
const INIT_ASSET : Nat

pred conserved(s) :=
  total_cash(s) = INIT_CASH &&
  total_asset(s) = INIT_ASSET
```

## Abstract Insertion Helpers

These are helper functions whose preservation lemmas will be proved separately.

```text
function insert_bid(bs : Seq Order, o : Order) : Seq Order
function insert_ask(as : Seq Order, o : Order) : Seq Order
```

## Submit Buy

```text
transition submit_buy(s, s' : State, who : Trader, oid : OrderId, px : Price, qty : Qty)
requires
  wf(s) && qty > 0 && oid notin ids(s.bids ++ s.asks)
ensures
  let o = Order { oid = oid, who = who, side = Buy, px = px, qty = qty, ts = s.next_ts } in
  s'.bids = insert_bid(s.bids, o) &&
  s'.asks = s.asks &&
  s'.balances = s.balances &&
  s'.trades = s.trades &&
  s'.next_ts = s.next_ts + 1
```

## Submit Sell

```text
transition submit_sell(s, s' : State, who : Trader, oid : OrderId, px : Price, qty : Qty)
requires
  wf(s) && qty > 0 && oid notin ids(s.bids ++ s.asks)
ensures
  let o = Order { oid = oid, who = who, side = Sell, px = px, qty = qty, ts = s.next_ts } in
  s'.asks = insert_ask(s.asks, o) &&
  s'.bids = s.bids &&
  s'.balances = s.balances &&
  s'.trades = s.trades &&
  s'.next_ts = s.next_ts + 1
```

## Match

This first version only matches when the two head orders have equal quantity.
That keeps the proof obligations smaller.

```text
transition match(s, s' : State)
requires
  wf(s) &&
  len(s.bids) > 0 &&
  len(s.asks) > 0 &&
  s.bids[0].px >= s.asks[0].px &&
  s.bids[0].qty = s.asks[0].qty &&
  s.balances[s.bids[0].who].cash  >= s.asks[0].px * s.bids[0].qty &&
  s.balances[s.asks[0].who].asset >= s.bids[0].qty
ensures
  let bid = s.bids[0] in
  let ask = s.asks[0] in
  let q   = bid.qty in
  let p   = ask.px in
  let tr  = Trade {
    buy_oid = bid.oid, sell_oid = ask.oid,
    buy_who = bid.who, sell_who = ask.who,
    px = p, qty = q, ts = s.next_ts
  } in
  s'.bids = tail(s.bids) &&
  s'.asks = tail(s.asks) &&
  s'.trades = s.trades ++ [tr] &&
  s'.next_ts = s.next_ts + 1 &&
  s'.balances[bid.who].cash  = s.balances[bid.who].cash - p*q &&
  s'.balances[bid.who].asset = s.balances[bid.who].asset + q &&
  s'.balances[ask.who].cash  = s.balances[ask.who].cash + p*q &&
  s'.balances[ask.who].asset = s.balances[ask.who].asset - q &&
  forall t. t != bid.who && t != ask.who -> s'.balances[t] = s.balances[t]
```

## Initial State

```text
init(s : State) :=
  s.bids = [] &&
  s.asks = [] &&
  s.trades = [] &&
  s.next_ts = 0 &&
  wf(s) &&
  conserved(s)
```

## First Proof Targets

```text
theorem submit_buy_preserves_wf
theorem submit_sell_preserves_wf
theorem match_preserves_wf
theorem submit_transitions_preserve_conserved
theorem match_preserves_conserved
theorem match_uses_best_bid
theorem match_uses_best_ask
theorem match_trade_is_traceable
```

## Supporting Lean Lemmas

Expected Lean support:

- insertion preserves sortedness for bids
- insertion preserves sortedness for asks
- head of sorted bid book has highest priority
- head of sorted ask book has highest priority
- updating two balances preserves total cash
- updating two balances preserves total asset

## Recommended Minimal Verified Core

For the first complete milestone, keep the project at this scope:

- `submit_buy`
- `submit_sell`
- `match`
- no cancellation
- no partial fills
- prove well-formedness, price-time head selection, trade traceability, and conservation

That version is small enough to finish and still strong enough to be a solid
course project core.

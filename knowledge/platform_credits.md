# SaaS Pricing — Projection Reference

A model-agnostic reference for projecting a prospect or customer's cost across
the most common SaaS pricing structures. Use this with the `answer_pricing` skill.

> **Facts vs. assumptions.** Configured rate constants (seat price, unit price,
> included allowances) are *facts* sourced from the customer's tier or contract
> and supplied via environment variables — not committed here. Conversion ratios
> (e.g. observed usage per seat) are *assumptions*; always call them out and show
> a sensitivity range rather than a single point estimate.

## 1. SaaS pricing model taxonomy

Most SaaS products use one of three structures, or a hybrid:

### Seat-based (per-user)
A flat fee per active user per month. Simple to forecast; cost scales linearly
with headcount. Common in collaboration, productivity, and security tools.

```
cost = seats × seat_price_per_month
```

Env vars: `SEAT_PRICE` (price per seat/month), `SEATS` (current seat count).

### Usage-based (consumption / metered)
Charged per unit consumed — API calls, tokens, compute hours, GB transferred,
events processed, etc. Cost tracks actual use; harder to budget for customers
without usage history.

```
cost = usage_units × unit_price
```

Env vars: `USAGE_UNIT_PRICE` (price per unit), `USAGE_UNIT_NAME` (e.g. "API
calls", "compute-hours", "GB"), `PRICE_PER_1K_UNITS` (if priced per thousand).

### Hybrid (seat + usage overage)
A base seat fee covers a bundled usage allowance; consumption above the
inclusion is billed at an overage rate. Most enterprise SaaS tiers work this way.

```
included_units = seats × included_units_per_seat
overage_units  = max(0, actual_usage - included_units)
cost           = (seats × seat_price) + (overage_units × overage_unit_price)
```

Env vars: `SEAT_PRICE`, `INCLUDED_UNITS_PER_SEAT`, `OVERAGE_UNIT_PRICE`.

### Tiered / volume pricing
Unit price drops as volume crosses thresholds (e.g. first 10K units at $X,
next 90K at $Y, above 100K at $Z). Quote against the customer's expected tier
or show a cost at each tier boundary.

Env vars: `TIER_1_LIMIT`, `TIER_1_PRICE`, `TIER_2_LIMIT`, `TIER_2_PRICE`, etc.

---

> **Which model applies?** Confirm with the pricing sheet or contract before
> running a projection. Many products blend models (e.g. seat license + metered
> API overage). When in doubt, run projections for both and show the range.

## 2. Rate configuration

> **Configure via environment.** All rate constants are read from environment
> variables — no values are committed to this repo. Set them in your shell or
> secret manager to match the customer's negotiated tier before running.

Common variables (set the ones relevant to your pricing model):

| Variable | Description |
|---|---|
| `SEAT_PRICE` | Price per seat per month |
| `SEATS` | Current seat count (POC baseline) |
| `TARGET_SEATS` | Target seat count (for scaling projection) |
| `USAGE_UNIT_NAME` | Human-readable unit name ("API calls", "compute-hours", "GB") |
| `USAGE_UNIT_PRICE` | Price per unit |
| `PRICE_PER_1K_UNITS` | Price per 1,000 units (alternative to per-unit) |
| `INCLUDED_UNITS_PER_SEAT` | Units bundled per seat before overage |
| `OVERAGE_UNIT_PRICE` | Price per unit above the included allowance |
| `PRICE_GRID` | Comma-separated price points for sensitivity analysis |
| `USAGE_GRID` | Comma-separated usage volumes for sensitivity analysis |

For a sensitivity grid, set `PRICE_GRID` and/or `USAGE_GRID` to compare
several scenarios at once; when unset, the projection uses only the base values.

## 3. Key conversion assumptions

For usage-based or hybrid models you often need to convert from one observed
metric to the billable unit. Common conversions:

- **Inference spend → compute hours:** divide total inference cost by an
  assumed $/hr; this ratio varies widely by workload type.
- **Events/requests → seats:** divide total events by events-per-seat-per-month;
  useful for sizing from API data.
- **Historical window → annual run-rate:** `value × 365 ÷ window_days`.

Always state which ratio you used and why. Higher assumed usage-per-unit ⇒
fewer implied units ⇒ lower projected cost — note the direction of the lever.

> **Uncertainty caveat:** usage-based projections typically carry ±30–50% error
> without a full usage history. Always show a sensitivity range.

## 4. The projection model

### Seat-based
```
monthly_cost = seats × seat_price
annual_cost  = monthly_cost × 12
```

### Usage-based
```
period_cost      = usage_units × unit_price          # or ÷ 1000 × price_per_1k
monthly_run_rate = period_cost × 30 ÷ window_days
annual_run_rate  = period_cost × 365 ÷ window_days
```

### Hybrid
```
included          = seats × included_units_per_seat
overage           = max(0, usage_units - included)
monthly_cost      = (seats × seat_price) + (overage × overage_unit_price)
```

### Seat scaling
Scale any per-seat cost linearly: multiply by `target_seats ÷ poc_seats`.
**Caveat:** if platform usage is driven by a fixed number of service/bot
accounts rather than per-user activity, it will not scale with headcount —
flag this and adjust before quoting.

### Self-hosted / BYOC
If the customer supplies their own compute, billed compute = $0. Show the
avoided infrastructure cost separately if you can estimate it, to make the
savings concrete.

Use `.warp/skills/answer_pricing/scripts/project_credits.py` to run the
arithmetic — don't do it by hand. Pass `--pricing-model` (seat / usage /
hybrid) and the relevant env vars or flags. The script outputs a sensitivity
grid across 7-day / monthly / quarterly / annual horizons.

## 5. Pitfalls

- **Confirm the pricing model first.** Seat vs. usage vs. hybrid changes the
  formula entirely; projecting against the wrong model can be off by an order
  of magnitude.
- **Tier-specific rates.** Customers on negotiated enterprise tiers often have
  non-list pricing. Always check the contract or AE notes before quoting and
  set env vars accordingly.
- **Included allowances reset rules.** Some products reset allowances monthly,
  others annually. Know the cadence before modeling overage.
- **Service/bot accounts vs. named users.** Seat counts from an email domain
  filter miss non-human accounts that still consume usage; source from the
  billing or admin API when possible.
- **Stale rate comparisons.** When comparing to prior projections, confirm
  which rate was in effect at the time so the numbers reconcile.

---
name: answer_pricing
description: Projects a customer's cost from prior usage data across seat-based, usage-based, and hybrid SaaS pricing models. Use when asked to "project cost", "estimate BYO cost", "estimate spend", "how much will this cost", "size a deal", or to build an enterprise-style usage/cost projection.
---

# Answer Pricing Skill

> **Setup required:** Before using this skill, update `knowledge/platform_credits.md` with your product's pricing model (seat-based, usage-based, or hybrid), your rate constants, and any tier-specific details. The scripts ship with no hardcoded values — you supply them via environment variables or CLI flags.

Use this skill to project a prospect or customer's cost from their prior usage data. It standardizes the projection math across seat-based, usage-based, and hybrid pricing models.

**Always read `knowledge/platform_credits.md` first** — it holds the pricing
model taxonomy, rate configuration, conversion options, and projection
formulas. Cite it in your answer.

## Prerequisites

- **`METABASE_API_KEY`** in the environment — only needed for Step 0 (pulling a
  customer's usage from a data warehouse). If you already have usage numbers, skip it.
- **Rate config** — set the relevant env vars from `knowledge/platform_credits.md`
  for your pricing model (e.g. `SEAT_PRICE`, `USAGE_UNIT_PRICE`,
  `INCLUDED_UNITS_PER_SEAT`). No rates ship in the repo.
- Python 3 (the scripts are stdlib-only; no `pip install` needed).

## Inputs

The user typically provides:
1. **Pricing model** — seat-based, usage-based, or hybrid. Confirm from
   the pricing sheet or contract if not stated. *(Required.)*
2. **Current usage or spend** and the **window** it covers (e.g. "10,000 API
   calls over 7 days", "$3,000 inference spend last month"). If given a
   team/account ID instead, pull it with Step 0. *(Required.)*
3. **Rate constants** — set via env vars (see `knowledge/platform_credits.md`).
   No defaults ship in the repo. *(Required.)*
4. **Conversion assumption** — if you need to convert from one metric to the
   billable unit (e.g. inference spend → compute hours), state the ratio and
   its source explicitly. *(Required if applicable.)*
5. **Seats** — POC seat count + target seat count, for scaling projections. *(Optional.)*
6. Whether they **self-host / BYOC** — if so, billed compute = $0; optionally
   quantify the avoided infrastructure cost.

If an optional input is missing, use the documented approach and **state the
assumption**. Rate inputs have no built-in defaults — set them via env vars
or CLI flags before running.

## Workflow

### Step 0 (optional): Pull usage by account/team ID
If you only have a customer name or account ID, fetch their usage from the
data warehouse first. This gives you observed usage numbers — the best anchor
for any conversion assumption.

```bash
python3 .warp/skills/answer_pricing/scripts/fetch_usage.py --account-id <id> --days <n>
```

**Always scope by account/team ID, not email domain** — domain filters miss
service accounts and bots that still consume usage.
Requires `METABASE_API_KEY`.

### Step 1: Confirm the pricing model and gather rate constants
Read `knowledge/platform_credits.md` to identify the applicable model
(seat-based, usage-based, or hybrid). Set the relevant env vars for the
customer's tier — no rates are committed to the repo. If the user references
older figures, confirm which rate was in effect so the numbers reconcile.

### Step 2: Identify and state any conversion assumptions
If you need to convert from an observed metric to the billable unit (e.g.
inference tokens → compute hours, API calls → seats), this is the biggest
uncertainty lever (±30–50% typical error). **Prefer the customer's own observed
ratio** from Step 0. Otherwise choose and state an assumption explicitly —
pass it via CLI flag or env var. Note the direction of the lever.

### Step 3: Run the projector
Don't do the math by hand. Set rate env vars first (or pass flags); the script
ships with no hardcoded values:

```bash
python3 .warp/skills/answer_pricing/scripts/project_credits.py \
  --pricing-model <seat|usage|hybrid> \
  --usage <value> --window-days <days> \
  [--seat-price <price>] [--seats <n>] [--target-seats <n>] \
  [--unit-price <price>] [--included-per-seat <n>] [--overage-price <price>] \
  [--conversion-ratio <ratio>] [--json]
```

It prints a one-line headline and a compact monthly/annual grid across the
configured scenarios. Set `PRICE_GRID` / `USAGE_GRID` to compare several
price/volume points. Use `--json` for full multi-horizon detail, or
`--self-test` to confirm model arithmetic after any edit.

### Step 4: Write the answer
Use the output format below. Lead with the pricing model used, the key numbers,
and any savings vs. an alternative (e.g. current spend vs. projected, or
self-hosted vs. managed). State the conversion assumption in one line.
Keep it short — don't dump every horizon or sanity-check row.

## Output Format

Keep the reply short and scannable: one headline (pricing model + key inputs),
the projection result, a savings/comparison line if applicable, and one basis
line. Default to the monthly horizon (annual in parens). Offer other horizons
or price points only if asked.

---BEGIN FORMAT---

**[Customer] — Cost Projection ([Pricing Model])**
[Usage] / [W] days → monthly run-rate: ~$[mo]/mo (~$[yr]/yr)[ Self-hosted, so compute = $0.]

Scenario comparison:
- [Scenario A, e.g. "10 seats @ $X/seat"] → ~$[mo]/mo
- [Scenario B, e.g. "20 seats @ $X/seat"] → ~$[mo]/mo
- [Alternative, e.g. "usage-based @ $Y/unit"] → ~$[mo]/mo

→ [Scenario A] is ~[S]% [cheaper/more expensive] than [alternative].
Basis: [conversion ratio and source]; directional (±~30–50% without full history).

---END FORMAT---

## Guidelines

- **Keep the reply presentable.** Short headline, neutral scenario options, one
  comparison line, one basis line. Don't dump every horizon or sanity-check row.
- **Show scenarios plainly.** When comparing multiple price points or models,
  present them neutrally without labeling any as preferred.
- **Never quote a single point estimate** for usage-derived costs — show a
  range or multiple scenarios so uncertainty is visible.
- **Use account/team ID, not email domain**, when sourcing usage data (service
  accounts hide behind non-customer domains).
- **Be evidence-driven.** Base rates on `knowledge/platform_credits.md`; keep
  facts (configured rates) vs. assumptions (conversion ratios) clearly separated.

## After Completing
For a one-off answer, reply inline. For a deliverable, save a markdown brief to
`reports/pricing/pricing_<customer>_<YYYY-MM-DD>.md` and create a PR. For a
formatted deck/xlsx, the skill produces the numbers and brief —
deck formatting is out of scope.

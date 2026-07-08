#!/usr/bin/env python3
"""Pull a customer's usage by account/team ID for a pricing projection.

This is Step 0 of the answer_pricing skill: it fetches the inputs that
project_credits.py needs straight from your data warehouse, instead of having
someone eyeball a dashboard.

Scope every query by the customer's ACCOUNT/TEAM ID, never by email domain.
Domain filters miss service accounts and bots that still consume usage, which
understates real usage. Always project off the account/team ID.

The table and column names below are placeholders — replace them with your own
warehouse schema. Requires METABASE_API_KEY. Output feeds project_credits.py.

Example:
    python3 fetch_usage.py --account-id 12345 --days 7
    python3 fetch_usage.py --account-id 12345 --days 7 --json
"""
from __future__ import annotations

import argparse
import json
import sys

from metabase_client import PROJECT_ID, DATASET, metabase_query, rows_as_dicts

# Placeholders — point these at your own warehouse schema.
TBL_USAGE = f"`{PROJECT_ID}.{DATASET}.your_usage_events_table`"
ID_COLUMN = "account_id"       # the account/team identifier column
UNITS_COLUMN = "usage_units"   # the billable usage metric column
DATE_COLUMN = "usage_date"     # the event date column
TYPE_COLUMN = "usage_type"     # optional: a category column for the breakdown


def _num(v, default=0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def fetch_totals(account_id: int, days: int) -> dict:
    """Total usage over the window (the basis for the projection)."""
    sql = f"""
    SELECT
        COUNT(*)                        AS events,
        SUM({UNITS_COLUMN})             AS usage_units,
        MIN({DATE_COLUMN})              AS first_date,
        MAX({DATE_COLUMN})              AS last_date,
        COUNT(DISTINCT {DATE_COLUMN})   AS active_days
    FROM {TBL_USAGE}
    WHERE {ID_COLUMN} = {account_id}
      AND {DATE_COLUMN} >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    """
    rows = rows_as_dicts(metabase_query(sql))
    return rows[0] if rows else {}


def fetch_breakdown(account_id: int, days: int) -> list:
    """Optional usage breakdown by category (drop if your schema has no type column)."""
    sql = f"""
    SELECT
        {TYPE_COLUMN}                   AS usage_type,
        ROUND(SUM({UNITS_COLUMN}), 0)   AS usage_units
    FROM {TBL_USAGE}
    WHERE {ID_COLUMN} = {account_id}
      AND {DATE_COLUMN} >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    GROUP BY {TYPE_COLUMN}
    ORDER BY usage_units DESC
    """
    return rows_as_dicts(metabase_query(sql))


def build(account_id: int, days: int) -> dict:
    totals = fetch_totals(account_id, days)
    try:
        breakdown = fetch_breakdown(account_id, days)
    except RuntimeError:
        breakdown = []  # breakdown is optional; ignore if the type column is absent
    return {
        "account_id": account_id,
        "window_days": days,
        "totals": totals,
        "usage_units": _num(totals.get("usage_units")),
        "breakdown": breakdown,
    }


def render_text(data: dict) -> str:
    t = data["totals"]
    lines = []
    lines.append("=" * 60)
    lines.append(f"USAGE PULL — account_id {data['account_id']} (last {data['window_days']}d)")
    lines.append("=" * 60)
    lines.append("Source: account/team ID (NOT email domain — captures service accounts).")
    lines.append("")
    lines.append("Totals (your_usage_events_table):")
    lines.append(
        f"  events={_num(t.get('events')):,.0f}  "
        f"usage_units={_num(t.get('usage_units')):,.0f}  "
        f"active_days={_num(t.get('active_days')):,.0f}"
    )
    if data["breakdown"]:
        lines.append("")
        lines.append("Breakdown by usage_type:")
        for row in data["breakdown"]:
            lines.append(f"  {row.get('usage_type', 'unknown')}: {_num(row.get('usage_units')):,.0f}")
    lines.append("")
    lines.append("Next — run the projection:")
    lines.append(
        "  python3 project_credits.py --pricing-model usage \\\n"
        f"      --usage {data['usage_units']:.0f} --window-days {data['window_days']} \\\n"
        "      --unit-price <your-unit-price>   # or --price-per-1k-units"
    )
    lines.append("")
    lines.append(
        "Tip: scope by account/team ID, not email domain. Usage often scales with "
        "seats, but usage driven by a few service accounts may not — flag it before "
        "projecting seat growth."
    )
    return "\n".join(lines)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Fetch a customer's usage by account/team ID for a pricing projection."
    )
    p.add_argument("--account-id", type=int, required=True,
                   help="The customer's account/team ID (NOT email domain).")
    p.add_argument("--days", type=int, default=7,
                   help="Look-back window in days (default 7).")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        data = build(args.account_id, args.days)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(render_text(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

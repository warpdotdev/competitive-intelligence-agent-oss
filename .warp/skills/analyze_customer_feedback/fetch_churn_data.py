#!/usr/bin/env python3
"""Fetch subscription cancellation comments via the Metabase API."""

import argparse
import json
import sys
from typing import List, Dict, Any

from metabase_client import metabase_query, PROJECT_ID, DATASET

TABLE = "your_subscriptions_table"


def fetch_churn_responses(days: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch subscription cancellation comments from the last N days via the Metabase API.

    Requires the METABASE_API_KEY environment variable to be set.

    Args:
        days: Number of days to look back (default: 7)

    Returns:
        List of cancellation dictionaries with keys: plan_type, cancellation_comment
    """
    sql = f"""
    SELECT
        plan_type,
        cancellation_comment
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    WHERE
        date(canceled_at) BETWEEN date_sub(current_date(), INTERVAL {days} DAY) AND current_date()
        AND cancellation_comment IS NOT NULL
    """

    try:
        print(f"  Querying Metabase for churn responses (last {days} days)...", file=sys.stderr)
        result = metabase_query(sql)

        if "error" in result:
            print(f"Metabase query error: {result['error']}", file=sys.stderr)
            return []

        cols = [c["name"] for c in result["data"]["cols"]]
        rows = result["data"]["rows"]

        col_idx = {name: i for i, name in enumerate(cols)}

        responses = []
        for row in rows:
            responses.append({
                "plan_type": row[col_idx["plan_type"]],
                "cancellation_comment": row[col_idx["cancellation_comment"]],
            })

        print(f"  Fetched {len(responses)} churn responses", file=sys.stderr)
        return responses

    except RuntimeError as e:
        print(f"Error fetching churn data: {e}", file=sys.stderr)
        return []
    except (KeyError, IndexError) as e:
        print(f"Error parsing Metabase response: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error fetching churn data: {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description="Fetch subscription cancellation comments via Metabase API")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    responses = fetch_churn_responses(days=args.days)

    if args.json:
        output = {
            "total_cancellations": len(responses),
            "cancellations": responses,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"Subscription Cancellation Comments (last {args.days} days)\n")
        print(f"Total Cancellations with Comments: {len(responses)}\n")

        # Group by plan type
        by_plan = {}
        for r in responses:
            plan = r.get("plan_type", "unknown")
            by_plan.setdefault(plan, []).append(r)

        for plan, items in sorted(by_plan.items(), key=lambda x: -len(x[1])):
            print(f"### {plan} ({len(items)} cancellations)")
            for item in items[:20]:  # Limit output per plan
                comment = (item["cancellation_comment"] or "")[:200]
                ellipsis = "..." if len(item["cancellation_comment"] or "") > 200 else ""
                print(f"  - {comment}{ellipsis}")
            if len(items) > 20:
                print(f"  ... and {len(items) - 20} more")
            print()


if __name__ == "__main__":
    main()

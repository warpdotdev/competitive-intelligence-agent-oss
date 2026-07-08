#!/usr/bin/env python3
"""Fetch NPS survey responses via the Metabase API."""

import argparse
import json
import sys
from typing import List, Dict, Any

from metabase_client import metabase_query, PROJECT_ID, DATASET

TABLE = "your_nps_survey_responses_table"


def fetch_nps_responses(days: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch NPS survey responses from the last N days via the Metabase API.

    Requires the METABASE_API_KEY environment variable to be set.

    Args:
        days: Number of days to look back (default: 7)

    Returns:
        List of NPS response dictionaries with keys:
        event_date, event_timestamp, score, comment, user_id, anonymous_id, os
    """
    sql = f"""
    SELECT
        event_date,
        event_timestamp,
        score,
        comment,
        user_id,
        anonymous_id,
        os_name
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY event_timestamp DESC
    """

    try:
        print(f"  Querying Metabase for NPS responses (last {days} days)...", file=sys.stderr)
        result = metabase_query(sql)

        if "error" in result:
            print(f"Metabase query error: {result['error']}", file=sys.stderr)
            return []

        cols = [c["name"] for c in result["data"]["cols"]]
        rows = result["data"]["rows"]

        # Map column positions
        col_idx = {name: i for i, name in enumerate(cols)}

        responses = []
        for row in rows:
            responses.append({
                "event_date": row[col_idx["event_date"]],
                "event_timestamp": row[col_idx["event_timestamp"]],
                "score": row[col_idx["score"]],
                "comment": row[col_idx["comment"]],
                "user_id": row[col_idx["user_id"]],
                "anonymous_id": row[col_idx["anonymous_id"]],
                "os": row[col_idx["os_name"]],
            })

        print(f"  Fetched {len(responses)} NPS responses", file=sys.stderr)
        return responses

    except RuntimeError as e:
        print(f"Error fetching NPS data: {e}", file=sys.stderr)
        return []
    except (KeyError, IndexError) as e:
        print(f"Error parsing Metabase response: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error fetching NPS data: {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description="Fetch NPS survey responses via Metabase API")
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
    parser.add_argument(
        "--with-comments",
        action="store_true",
        help="Include only responses with comments",
    )

    args = parser.parse_args()

    responses = fetch_nps_responses(days=args.days)

    if args.with_comments:
        responses = [r for r in responses if r.get("comment")]

    if args.json:
        output = {
            "total_responses": len(responses),
            "responses": responses,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"NPS Survey Responses (last {args.days} days)\n")
        print(f"Total Responses: {len(responses)}")

        responses_with_comments = [r for r in responses if r.get("comment")]
        print(f"Responses with comments: {len(responses_with_comments)}\n")
        if responses_with_comments:
            for r in responses_with_comments[:20]:  # Limit output
                print(f"Score: {r['score']} | Date: {r['event_date']} | OS: {r.get('os', 'unknown')}")
                print(f"  Comment: {(r['comment'] or '')[:200]}{'...' if len(r['comment'] or '') > 200 else ''}\n")


if __name__ == "__main__":
    main()

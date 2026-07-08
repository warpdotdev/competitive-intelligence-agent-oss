#!/usr/bin/env python3
"""Shared Metabase API client for executing native SQL queries.

Mirrors .warp/skills/analyze_customer_feedback/metabase_client.py so the
answer_pricing skill is self-contained. Requires METABASE_API_KEY.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict


# Metabase configuration
METABASE_URL = "https://your-metabase-instance.metabaseapp.com"
METABASE_DATABASE_ID = 0  # Replace with your Metabase database ID
API_KEY_ENV = "METABASE_API_KEY"

# BigQuery project reference
PROJECT_ID = "your-gcp-project-id"
DATASET = "prod"


def metabase_query(sql: str) -> Dict[str, Any]:
    """Execute a native SQL query via the Metabase API.

    Args:
        sql: The SQL query to execute.

    Returns:
        The full Metabase API response as a dictionary.

    Raises:
        RuntimeError: If the API key is missing or the request fails.
    """
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"{API_KEY_ENV} environment variable is not set. "
            "Set it in your shell or secret manager."
        )

    payload = json.dumps({
        "database": METABASE_DATABASE_ID,
        "type": "native",
        "native": {"query": sql},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{METABASE_URL}/api/dataset",
        data=payload,
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Metabase API error (HTTP {e.code}): {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Metabase connection error: {e.reason}") from e


def rows_as_dicts(result: Dict[str, Any]) -> list[dict]:
    """Convert a Metabase dataset response into a list of column->value dicts."""
    if "error" in result:
        raise RuntimeError(f"Metabase query error: {result['error']}")
    cols = [c["name"] for c in result["data"]["cols"]]
    return [dict(zip(cols, row)) for row in result["data"]["rows"]]

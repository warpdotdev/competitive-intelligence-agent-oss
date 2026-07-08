#!/usr/bin/env python3
"""
Fetch external customer meetings and transcripts from the Grain REST API.

Usage:
    python3 fetch_grain_data.py [--days 7] [--output grain_data.json]

Requires GRAIN_TOKEN environment variable.

Outputs a JSON file with:
  - meetings: list of meeting metadata (id, title, date, participants with IDs/scope/email)
  - transcripts: dict of recording_id -> list of transcript segments (with participant_id)

The participant `id` field in meeting metadata matches the `participant_id` field
in transcript segments, enabling reliable internal/external speaker attribution.

API Reference:
  Base URL: https://api.grain.com/_/public-api/v2
  Auth: Bearer token (Personal Access Token or Workspace Access Token)
  Header: Public-Api-Version: 2025-10-31
  Endpoints:
    POST /recordings  — list recordings with filters (participant_scope, date range)
    GET  /recordings/{id}/transcript — get transcript segments for a recording
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("Error: 'requests' package required. Install with: pip3 install requests", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://api.grain.com/_/public-api/v2"
API_VERSION = "2025-10-31"


def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Public-Api-Version": API_VERSION,
    }


def fetch_recordings(token: str, after_dt: str, before_dt: str) -> list:
    """Fetch all external recordings in the date range, with pagination."""
    headers = get_headers(token)
    all_recordings = []
    cursor = None
    page = 0

    while True:
        page += 1
        payload = {
            "filter": {
                "after_datetime": after_dt,
                "before_datetime": before_dt,
                "participant_scope": "external",
            },
            "include": {"participants": True},
        }
        if cursor:
            payload["cursor"] = cursor

        resp = requests.post(f"{BASE_URL}/recordings", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        recs = data.get("recordings", [])
        all_recordings.extend(recs)
        print(f"  Page {page}: {len(recs)} recordings (total: {len(all_recordings)})", file=sys.stderr)

        cursor = data.get("cursor")
        if not cursor:
            break

    return all_recordings


def fetch_transcript(token: str, recording_id: str) -> list | None:
    """Fetch transcript segments for a single recording."""
    headers = get_headers(token)
    resp = requests.get(f"{BASE_URL}/recordings/{recording_id}/transcript", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return None


def main():
    parser = argparse.ArgumentParser(description="Fetch Grain meetings and transcripts")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path (default: stdout)")
    args = parser.parse_args()

    token = (os.environ.get("GRAIN_TOKEN") or "").strip()
    if not token:
        print("Error: GRAIN_TOKEN environment variable not set.", file=sys.stderr)
        print("Set it with: export GRAIN_TOKEN=grain_pat_...", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc)
    after_dt = (now - timedelta(days=args.days)).strftime("%Y-%m-%dT00:00:00Z")
    before_dt = now.strftime("%Y-%m-%dT23:59:59Z")

    print(f"Fetching external meetings from {after_dt} to {before_dt}...", file=sys.stderr)

    # 1. Fetch recordings
    recordings = fetch_recordings(token, after_dt, before_dt)
    print(f"\nTotal external recordings: {len(recordings)}", file=sys.stderr)

    # 2. Extract meeting metadata (preserving participant IDs for speaker attribution)
    meetings = []
    for rec in recordings:
        meetings.append({
            "id": rec["id"],
            "title": rec.get("title"),
            "start_datetime": rec.get("start_datetime"),
            "end_datetime": rec.get("end_datetime"),
            "duration_ms": rec.get("duration_ms"),
            "url": rec.get("url"),
            "meeting_type": (rec.get("meeting_type") or {}).get("name"),
            "participants": [
                {
                    "id": p.get("id"),       # <-- matches transcript participant_id
                    "name": p.get("name"),
                    "email": p.get("email"),
                    "scope": p.get("scope"),  # "internal", "external", or "unknown"
                }
                for p in rec.get("participants", [])
            ],
        })

    # 3. Fetch transcripts
    transcripts = {}
    for i, rec in enumerate(recordings):
        rec_id = rec["id"]
        title = rec.get("title", "Untitled")
        transcript = fetch_transcript(token, rec_id)
        if transcript is not None:
            transcripts[rec_id] = transcript
            seg_count = len(transcript) if isinstance(transcript, list) else 0
            print(f"  [{i+1}/{len(recordings)}] {title}: {seg_count} segments", file=sys.stderr)
        else:
            print(f"  [{i+1}/{len(recordings)}] {title}: no transcript", file=sys.stderr)

    # 4. Output
    result = {"meetings": meetings, "transcripts": transcripts}
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to {args.output}", file=sys.stderr)
    else:
        json.dump(result, indent=2, fp=sys.stdout)


if __name__ == "__main__":
    main()

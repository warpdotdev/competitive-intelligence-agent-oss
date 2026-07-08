#!/usr/bin/env python3
"""
Analyze Grain transcript data for VoTC themes.

Usage:
    python3 analyze_transcripts.py <grain_data.json> [--output analysis.json]

Input: JSON file produced by fetch_grain_data.py
Output: JSON with categorized quotes from external speakers only.

Speaker attribution uses participant_id matching:
  - Meeting metadata includes participant `id`, `name`, `scope`, `email`
  - Transcript segments include `participant_id`
  - These IDs match, enabling reliable internal/external classification
"""

import argparse
import json
import sys

# Search categories and keywords
CATEGORIES = {
    "pain_points": [
        "frustrated", "bug", "issue", "problem", "not working", "broken",
        "error", "crash", "slow", "confusing", "difficult", "hard to",
    ],
    "pricing": [
        "expensive", "pricing", "cost", "budget", "credits", "price",
    ],
    "competitive": [
        "cursor", "copilot", "windsurf", "claude code", "codex", "devin",
        "vs code", "jetbrains", "intellij", "vim", "neovim",
    ],
    "feature_requests": [
        "wish", "would be great", "need the ability", "feature request",
        "roadmap", "love to see", "missing", "doesn't support",
    ],
    "security": [
        "security", "compliance", "governance", "self-hosted", "on-prem",
        "air-gapped", "private", "soc2", "hipaa",
    ],
    "integrations": [
        "integration", "mcp", "plugin", "extension",
    ],
    "churn_risk": [
        "switching to", "considering alternative", "moving away", "cancel",
    ],
    "positive": [
        "love", "amazing", "impressed", "awesome", "great", "game changer",
        "incredible", "saving time", "productivity", "10x",
    ],
    "agents": [
        "cloud agent", "multi-agent", "autonomous", "ai agent",
    ],
}


def build_participant_lookup(meetings: list) -> dict:
    """Build (meeting_id, participant_id) -> {name, scope, email} lookup."""
    lookup = {}
    for m in meetings:
        for p in m.get("participants", []):
            pid = p.get("id")
            if pid:
                lookup[(m["id"], pid)] = {
                    "name": p.get("name", "Unknown"),
                    "scope": p.get("scope", "unknown"),
                    "email": p.get("email"),
                }
    return lookup


def analyze(data: dict) -> dict:
    meetings = data["meetings"]
    transcripts = data["transcripts"]
    meeting_lookup = {m["id"]: m for m in meetings}
    pid_lookup = build_participant_lookup(meetings)

    results = {cat: [] for cat in CATEGORIES}

    for mid, segments in transcripts.items():
        if not isinstance(segments, list):
            continue
        meeting = meeting_lookup.get(mid, {})
        title = meeting.get("title", "Unknown")
        date = (meeting.get("start_datetime") or "")[:10]
        ext_participants = [
            p for p in meeting.get("participants", []) if p.get("scope") == "external"
        ]

        for seg in segments:
            text_lower = seg.get("text", "").lower()
            text_raw = seg.get("text", "")
            pid = seg.get("participant_id", "")

            # Look up speaker info via participant_id
            info = pid_lookup.get((mid, pid), {})
            if info.get("scope") != "external":
                continue  # Only external speakers

            # Skip very short segments (less signal)
            if len(text_raw) < 40:
                continue

            for cat, keywords in CATEGORIES.items():
                for kw in keywords:
                    if kw in text_lower:
                        results[cat].append({
                            "meeting_title": title,
                            "date": date,
                            "speaker": info.get("name", "Unknown"),
                            "email": info.get("email"),
                            "text": text_raw,
                            "keyword": kw,
                            "external_participants": [
                                p.get("name") for p in ext_participants
                            ],
                            "meeting_type": meeting.get("meeting_type"),
                        })
                        break  # One match per category per segment

    # Deduplicate by (meeting_title, text prefix)
    output = {}
    for cat, matches in results.items():
        seen = set()
        unique = []
        for m in matches:
            key = (m["meeting_title"], m["text"][:80])
            if key not in seen:
                seen.add(key)
                unique.append(m)
        output[cat] = unique

    return output


def print_summary(output: dict):
    """Print a human-readable summary to stderr."""
    for cat, matches in output.items():
        meetings_set = set(m["meeting_title"] for m in matches)
        print(
            f"\n=== {cat.upper()} ({len(matches)} external quotes, "
            f"{len(meetings_set)} meetings) ===",
            file=sys.stderr,
        )
        for m in matches[:5]:
            print(
                f"  [{m['date']}] {m['meeting_title']} — {m['speaker']}:",
                file=sys.stderr,
            )
            print(f'    "{m["text"][:250]}"', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Analyze Grain transcripts for VoTC themes")
    parser.add_argument("input", help="Path to grain_data.json from fetch_grain_data.py")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    output = analyze(data)
    print_summary(output)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved analysis to {args.output}", file=sys.stderr)
    else:
        json.dump(output, indent=2, fp=sys.stdout)


if __name__ == "__main__":
    main()

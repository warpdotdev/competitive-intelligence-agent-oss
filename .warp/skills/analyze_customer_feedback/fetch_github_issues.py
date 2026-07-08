#!/usr/bin/env python3
"""Fetch recent GitHub issues from a public GitHub repository."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any


def fetch_issues(days: int = 7, repo: str = "YOUR_ORG/YOUR_REPO", include_prs: bool = True) -> List[Dict[str, Any]]:
    """
    Fetch GitHub issues (and optionally PRs) created in the last N days.
    
    Args:
        days: Number of days to look back (default: 7)
        repo: Repository in format owner/repo
        include_prs: Include pull requests in results (default: True)
        
    Returns:
        List of issue/PR dictionaries
    """
    since_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Use gh api to fetch issues
    # Note: 'since' parameter filters by updated time, so we filter by created_at afterward
    cmd = [
        'gh', 'api',
        '--method', 'GET',
        f'/repos/{repo}/issues',
        '--paginate',
        '-f', 'state=all',
        '-f', 'per_page=100',
        '-f', f'since={since_date}'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the JSON output
        raw_output = result.stdout.strip()
        if not raw_output:
            return []
        
        # gh api --paginate returns a single JSON array
        try:
            issues = json.loads(raw_output)
            if not isinstance(issues, list):
                issues = [issues]
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}", file=sys.stderr)
            return []
        
        # Filter to only issues created in the time window (not PRs)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered_issues = []
        
        for issue in issues:
            # Optionally skip pull requests (they have a pull_request key)
            if not include_prs and 'pull_request' in issue:
                continue
                
            created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            if created_at >= cutoff:
                filtered_issues.append({
                    'number': issue['number'],
                    'title': issue['title'],
                    'body': issue.get('body', '')[:2000] if issue.get('body') else '',  # Truncate long bodies
                    'labels': [label['name'] for label in issue.get('labels', [])],
                    'state': issue['state'],
                    'created_at': issue['created_at'],
                    'url': issue['html_url'],
                    'user': issue['user']['login'] if issue.get('user') else None,
                    'comments': issue.get('comments', 0)
                })
        
        return filtered_issues
        
    except subprocess.CalledProcessError as e:
        print(f"Error fetching issues: {e.stderr}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description="Fetch recent GitHub issues")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)"
    )
    parser.add_argument(
        "--repo",
        default="YOUR_ORG/YOUR_REPO",
        help="Repository in format owner/repo"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    
    args = parser.parse_args()
    
    issues = fetch_issues(days=args.days, repo=args.repo)
    
    if args.json:
        print(json.dumps(issues, indent=2))
    else:
        print(f"Found {len(issues)} issues from the last {args.days} days:\n")
        for issue in issues:
            labels_str = f" [{', '.join(issue['labels'])}]" if issue['labels'] else ""
            print(f"#{issue['number']}: {issue['title']}{labels_str}")
            print(f"  State: {issue['state']} | Created: {issue['created_at']}")
            print(f"  URL: {issue['url']}\n")


if __name__ == "__main__":
    main()

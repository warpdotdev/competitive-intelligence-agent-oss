#!/usr/bin/env python3
"""
Customer Feedback Data Fetcher

Fetches customer feedback from multiple sources and outputs raw data
for LLM analysis:
- GitHub issues (YOUR_ORG/YOUR_REPO)
- Gmail (feedback address configured via FEEDBACK_EMAIL)
- Metabase NPS survey responses

The script outputs structured data that should be analyzed by an LLM
rather than using heuristic categorization.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

# Import GitHub fetcher (always available)
from fetch_github_issues import fetch_issues



def format_feedback_for_llm(
    github_issues: List[Dict],
    nps_responses: List[Dict],
    emails: List[Dict],
    churn_responses: List[Dict],
    days: int
) -> str:
    """Format all feedback data for LLM analysis."""
    output = []
    output.append(f"# Customer Feedback Data")
    output.append(f"**Period:** Last {days} days")
    output.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    output.append("")
    
    # Summary counts
    output.append("## Summary")
    output.append(f"- GitHub Issues: {len(github_issues)}")
    output.append(f"- NPS Responses: {len(nps_responses)}")
    output.append(f"- Email Feedback: {len(emails)}")
    output.append(f"- Churn Cancellations: {len(churn_responses)}")
    output.append("")
    
    # Churn Cancellation Comments - grouped by plan type (before verbose sections to avoid truncation)
    output.append("## Churn Cancellation Comments")
    if churn_responses:
        output.append(f"{len(churn_responses)} cancellations with comments.")
        output.append("")
        
        # Group by plan type
        by_plan = {}
        for r in churn_responses:
            plan = r.get('plan_type', 'unknown')
            by_plan.setdefault(plan, []).append(r)
        
        for plan, items in sorted(by_plan.items(), key=lambda x: -len(x[1])):
            output.append(f"### {plan} ({len(items)} cancellations)")
            for item in items:
                comment = item.get('cancellation_comment', '')
                output.append(f"- {comment}")
            output.append("")
    else:
        output.append("No churn cancellation comments in this period.")
        output.append("")
    
    # GitHub Issues - full data
    output.append("## GitHub Issues")
    if github_issues:
        for issue in github_issues:
            output.append(f"### #{issue['number']}: {issue['title']}")
            output.append(f"- **URL:** {issue['url']}")
            output.append(f"- **State:** {issue['state']}")
            output.append(f"- **Created:** {issue['created_at']}")
            output.append(f"- **Comments:** {issue['comments']}")
            if issue.get('labels'):
                output.append(f"- **Labels:** {', '.join(issue['labels'])}")
            if issue.get('body'):
                output.append(f"- **Body:**")
                output.append(f"```")
                output.append(issue['body'])
                output.append(f"```")
            output.append("")
    else:
        output.append("No GitHub issues in this period.")
        output.append("")
    
    # NPS Responses - only those with comments
    output.append("## NPS Comments")
    responses_with_comments = [r for r in nps_responses if r.get('comment')]
    output.append(f"{len(responses_with_comments)} responses with comments out of {len(nps_responses)} total.")
    output.append("")
    if responses_with_comments:
        for resp in responses_with_comments:
            score = resp.get('score', 'N/A')
            comment = resp.get('comment', '')
            os_info = resp.get('os', 'unknown')
            date = resp.get('submitted_at', 'unknown')
            
            output.append(f"### Score: {score}")
            output.append(f"- **OS:** {os_info}")
            output.append(f"- **Date:** {date}")
            output.append(f"- **Comment:** {comment}")
            output.append("")
    else:
        output.append("No NPS responses with comments in this period.")
        output.append("")
    
    # Email Feedback - full data
    output.append("## Email Feedback")
    if emails:
        for email in emails:
            subject = email.get('subject', '(no subject)')
            sender = email.get('from', 'unknown')
            date = email.get('date', 'unknown')
            body = email.get('body', email.get('snippet', ''))
            
            output.append(f"### {subject}")
            output.append(f"- **From:** {sender}")
            output.append(f"- **Date:** {date}")
            if body:
                output.append(f"- **Content:**")
                output.append(f"```")
                output.append(body)
                output.append(f"```")
            output.append("")
    else:
        output.append("No email feedback in this period.")
        output.append("")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch customer feedback data for LLM analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_feedback.py                    # Fetch last 7 days
  python analyze_feedback.py --days 14          # Fetch last 14 days
  python analyze_feedback.py --json             # Output as JSON
  python analyze_feedback.py --skip-gmail       # Skip Gmail (if not configured)
        """
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text"
    )
    parser.add_argument(
        "--skip-github",
        action="store_true",
        help="Skip GitHub issues"
    )
    parser.add_argument(
        "--skip-nps",
        action="store_true",
        help="Skip NPS data"
    )
    parser.add_argument(
        "--skip-gmail",
        action="store_true",
        help="Skip Gmail feedback"
    )
    parser.add_argument(
        "--skip-churn",
        action="store_true",
        help="Skip churn cancellation comments"
    )
    
    args = parser.parse_args()
    
    print(f"Fetching customer feedback from the last {args.days} days...\n", file=sys.stderr)
    
    # Fetch data from each source
    github_issues = []
    nps_responses = []
    emails = []
    churn_responses = []
    
    if not args.skip_github:
        print("Fetching GitHub issues...", file=sys.stderr)
        github_issues = fetch_issues(days=args.days)
        print(f"  Found {len(github_issues)} issues", file=sys.stderr)
    
    if not args.skip_nps:
        print("Fetching NPS data...", file=sys.stderr)
        try:
            from fetch_nps_data import fetch_nps_responses
            nps_responses = fetch_nps_responses(days=args.days)
            print(f"  Found {len(nps_responses)} NPS responses", file=sys.stderr)
        except ImportError as e:
            print(f"  NPS module not available: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  Error fetching NPS data: {e}", file=sys.stderr)
    
    if not args.skip_gmail:
        print("Fetching Gmail feedback...", file=sys.stderr)
        try:
            from fetch_gmail_feedback import fetch_gmail_feedback
            emails = fetch_gmail_feedback(days=args.days)
            print(f"  Found {len(emails)} emails", file=sys.stderr)
        except ImportError as e:
            print(f"  Gmail module not available: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  Error fetching emails: {e}", file=sys.stderr)
    
    if not args.skip_churn:
        print("Fetching churn cancellation comments...", file=sys.stderr)
        try:
            from fetch_churn_data import fetch_churn_responses
            churn_responses = fetch_churn_responses(days=args.days)
            print(f"  Found {len(churn_responses)} cancellation comments", file=sys.stderr)
        except ImportError as e:
            print(f"  Churn module not available: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  Error fetching churn data: {e}", file=sys.stderr)
    
    print("", file=sys.stderr)
    
    if args.json:
        output = {
            'period_days': args.days,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'github_issues': github_issues,
            'nps_responses': nps_responses,
            'emails': emails,
            'churn_responses': churn_responses
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        report = format_feedback_for_llm(
            github_issues, nps_responses, emails, churn_responses, args.days
        )
        print(report)


if __name__ == "__main__":
    main()

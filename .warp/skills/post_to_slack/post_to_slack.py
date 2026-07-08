#!/usr/bin/env python3
"""
Post a message to Slack webhook.
"""
import argparse
import json
import os
import sys
from urllib.parse import urlparse
import requests


def post_to_slack(webhook_url: str, text: str) -> bool:
    """
    Post a message to a Slack webhook.

    Args:
        webhook_url: The Slack webhook URL (must be hooks.slack.com)
        text: The message text to post

    Returns:
        True if successful, False otherwise
    """
    parsed = urlparse(webhook_url)
    if parsed.netloc != "hooks.slack.com":
        print(f"Error: refusing to POST to non-Slack URL: {parsed.netloc}", file=sys.stderr)
        return False

    payload = {"text": text}

    try:
        response = requests.post(
            webhook_url,
            headers={"Content-type": "application/json"},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        print(f"Message posted successfully: {text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error posting to Slack: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Post a message to Slack webhook")
    parser.add_argument("text", help="The message text to post")
    parser.add_argument(
        "--webhook-url",
        default=os.environ.get("SLACK_WEBHOOK_URL"),
        help="Slack webhook URL (default: $SLACK_WEBHOOK_URL)"
    )
    
    args = parser.parse_args()
    
    if not args.webhook_url:
        print(
            "Error: no webhook URL provided. Pass --webhook-url or set SLACK_WEBHOOK_URL.",
            file=sys.stderr,
        )
        sys.exit(1)

    success = post_to_slack(args.webhook_url, args.text)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

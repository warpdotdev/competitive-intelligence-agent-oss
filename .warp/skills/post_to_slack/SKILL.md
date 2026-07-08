---
name: post_to_slack
description: Posts messages to Slack via webhook.
---

# Post to Slack Skill

Use this skill to post messages to the team's Slack channel via webhook.

## When to Use

- After completing a research task, to share findings with the team
- When another skill suggests posting results to Slack
- When the user explicitly asks to share something on Slack

## How to Use

Run the `post_to_slack.py` script with the message text:

```bash
python3 .warp/skills/post_to_slack/post_to_slack.py "Your message here"
```

### Custom Webhook URL

To post to a different Slack channel or workspace, use the `--webhook-url` argument:

```bash
python3 .warp/skills/post_to_slack/post_to_slack.py "Your message here" --webhook-url "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

If no webhook URL is provided, the script reads the `SLACK_WEBHOOK_URL` environment variable.

## Message Formatting

- Slack webhook messages support basic formatting
- Keep messages concise and actionable
- For longer reports, summarize key points rather than posting the full content

## Guidelines

- Only post when explicitly requested or when another skill suggests it
- Keep messages professional and relevant to the team
- Include context about what analysis or task the message relates to

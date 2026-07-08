---
name: analyze_customer_feedback
description: analyzes customer feedback across Email, GitHub, NPS, and churn cancellations.
---

# Customer Feedback Analysis Skill

Use this skill to analyze and summarize customer feedback from multiple sources over the last 7 days (or a custom time period). The skill fetches raw data from GitHub issues, NPS survey responses, email feedback, and subscription cancellation comments for you to analyze.

**Important:** For all tasks in this skill, use `METABASE_API_KEY` from the environment for NPS data (Metabase API) and `GOOGLE_OAUTH_TOKEN` for Gmail.

## Instructions for the Agent

This skill fetches raw feedback data. You (the agent) are responsible for organizing it into a factual report. Your job is to identify themes, count their frequency, and cite specific sources. Do NOT editorialize, speculate on root causes, assign severity/priority, or make recommendations.

1. **Filter out noise** — Ignore feedback that is not substantive:
   - Auto-reply/out-of-office messages (e.g., "自动回复", "This is an automated response")
   - Spam or promotional content
   - Internal test messages
   - Bounce-back emails
   - Generic "thank you" acknowledgments without substance

2. **Identify themes** — Scan all four channels (GitHub issues, NPS comments, emails, churn cancellations) and group feedback items that describe the same topic into themes. A theme is any topic mentioned by 2+ users or across 2+ channels. Single-mention items should be listed under "Other" at the end.

3. **Count frequency** — For each theme, report:
   - Total number of mentions across all channels
   - Breakdown by channel (e.g., "3 GitHub issues, 2 NPS comments, 1 email")
   - Order themes by total mention count, highest first

4. **Cite sources** — For every item in a theme:
   - GitHub issues: include issue number as a link (e.g., `[#123](https://github.com/YOUR_ORG/YOUR_REPO/issues/123)`) and the issue title
   - NPS comments: quote the comment verbatim and include the score
   - Emails: include the sender name and a brief description of the content
   - Churn cancellations: quote the comment verbatim and include the plan type, e.g., `Cancellation (build): "[verbatim quote]"`

5. **Note cross-channel convergence** — When a theme appears in 2+ channels, state that as a fact (e.g., "This theme appeared in 3 GitHub issues and 2 NPS detractor comments"). Do not interpret what the convergence means.

6. **Track week-over-week changes** — Read the most recent previous report from `reports/customer_feedback_summaries/` and compare:
   - Which themes are new (not in the previous report)
   - Which themes from the previous report recurred (with updated counts)
   - Which themes from the previous report did not recur
   - Report counts only. Do not use trend arrows, severity labels, or words like "improving," "worsening," or "resolved."

7. **Format your report** — Structure your output as described in the Output Format section below. Do not add sections beyond what is specified. Do not use emoji severity markers (🔴🟡🟢). Do not include sections titled "Recommended Actions," "Risks," "Open Questions," "Interpretation," or "Key Insight."

## When to Use

Use this skill when you need to:
- Get a weekly summary of customer feedback
- Identify trending issues or complaints
- Track NPS scores and sentiment over time
- Understand why users are canceling subscriptions
- Prepare for product reviews or planning sessions
- Understand customer pain points across multiple channels

## Data Sources

1. **GitHub Issues** (YOUR_ORG/YOUR_REPO) - Bug reports and feature requests from public users
2. **NPS Survey Responses** (Metabase API) - Net Promoter Score data with user comments
3. **Email Feedback** (Gmail) - Emails sent to your feedback address (set `FEEDBACK_EMAIL`)
4. **Subscription Cancellations** (Metabase API) - Cancellation comments from `prod.your_subscriptions_table`, grouped by plan type. Uses the same `METABASE_API_KEY` as NPS.

## Prerequisites

### 1. GitHub CLI
The `gh` CLI must be authenticated with access to `YOUR_ORG/YOUR_REPO`.

```bash
# Check authentication status
gh auth status

# Login if needed
gh auth login
```

### 2. Metabase API (for NPS data)

The `METABASE_API_KEY` environment variable should be set in your ennvironment.

The script queries `your-gcp-project-id.prod.your_nps_survey_responses_table` via the Metabase API at `https://your-metabase-instance.metabaseapp.com`.

### 3. Gmail API

Gmail uses `GOOGLE_OAUTH_TOKEN`. The token needs `gmail.readonly` scope.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Note: The NPS fetcher uses only Python standard library (`urllib.request`), so no additional packages are needed for NPS data.

## Usage

### Basic Usage (analyze last 7 days)

```bash
cd skills/analyze_customer_feedback
python analyze_feedback.py
```

### Custom Time Period

```bash
python analyze_feedback.py --days 14    # Last 14 days
python analyze_feedback.py --days 30    # Last 30 days
```

### JSON Output (for programmatic use)

```bash
python analyze_feedback.py --json
```

### Skip Sources (if not configured)

```bash
python analyze_feedback.py --skip-gmail     # Skip Gmail if not set up
python analyze_feedback.py --skip-nps       # Skip NPS if BigQuery not configured
python analyze_feedback.py --skip-github    # Skip GitHub issues
python analyze_feedback.py --skip-churn     # Skip churn cancellation comments
```

### Run Individual Fetchers

```bash
# GitHub issues only
python fetch_github_issues.py --days 7 --json

# NPS data only
python fetch_nps_data.py --days 7 --json

# Gmail feedback only
python fetch_gmail_feedback.py --days 7 --json

# Churn cancellations only
python fetch_churn_data.py --days 7 --json
```

## Script Output

The script outputs raw feedback data in a structured format:

1. **Summary** - Counts of feedback items from each source
2. **GitHub Issues** - Full issue data (title, body, labels, comments, URL)
3. **NPS Comments** - Score, OS, date, and verbatim comment for responses that included a comment
4. **Email Feedback** - Subject, sender, date, and full content
5. **Churn Cancellation Comments** - Plan type and verbatim cancellation comment, grouped by plan type

You (the agent) should organize this data into the report format below.

## Report Output Format

Your report must follow this structure exactly. Do not add extra sections.

```
# Customer Feedback Report — [Date Range]

**Period:** [time period]
**Generated:** [date]

---

## Summary

- GitHub issues filed: [N]
- NPS responses with comments: [N] out of [N] total
- Emails received: [N] ([N] after filtering noise)
- Churn cancellations with comments: [N]

---

## Themes (ordered by total mention count)

### 1. [Theme Name] — [N] mentions
**Channels:** [N] GitHub issues, [N] NPS comments, [N] emails
**Previous report:** [Yes — N mentions / No]

- [#NNNN](link): [issue title] ([N] comments)
- [#NNNN](link): [issue title]
- NPS (score [N]): "[verbatim quote]"
- Email from [sender]: [brief description]
- Cancellation ([plan_type]): "[verbatim quote]"

### 2. [Theme Name] — [N] mentions
...

### Other (single-mention items)
- [#NNNN](link): [issue title]
- NPS (score [N]): "[verbatim quote]"
- ...

---

## NPS Comments

List all NPS responses that included a written comment, grouped by score band. Only include responses with non-empty comments. Include the score for context but do not calculate or report the NPS score itself.

### Scores 9-10
- (Score [N]): "[verbatim quote]"
- (Score [N]): "[verbatim quote]"

### Scores 7-8
- (Score [N]): "[verbatim quote]"

### Scores 0-6
- (Score [N]): "[verbatim quote]"
- (Score [N]): "[verbatim quote]"

---

## Churn Cancellation Comments

List all cancellation comments, grouped by plan type. Include only subscriptions canceled in the reporting period that have a non-empty comment.

### [plan_type] ([N] cancellations)
- "[verbatim quote]"
- "[verbatim quote]"

### [plan_type] ([N] cancellations)
- "[verbatim quote]"

---

## Email Summary

[N] emails received. [N] after filtering auto-replies, spam, and non-substantive messages.

1. **[sender name]** — [brief factual description of content]
2. **[sender name]** — [brief factual description of content]
...

---

## Week-over-Week

### New themes (not in previous report)
- [Theme Name] — [N] mentions
- [Theme Name] — [N] mentions

### Recurring themes (also in previous report)
- [Theme Name] — [N] mentions this week, [N] last week
- [Theme Name] — [N] mentions this week, [N] last week

### Themes from previous report that did not recur
- [Theme Name] — [N] mentions last week, 0 this week
```

## Integration with Other Skills

After generating the report, you can:

## Troubleshooting

### Metabase API Errors
```bash
# Verify METABASE_API_KEY is set
echo $METABASE_API_KEY | head -c 10

# Test the API connection
curl -s -w "\nHTTP_CODE:%{http_code}" -H "x-api-key: $METABASE_API_KEY" "https://your-metabase-instance.metabaseapp.com/api/user/current"
```

### GitHub CLI Errors
```bash
# Check token scopes
gh auth status

# Re-authenticate with required scopes
gh auth login --scopes read:org,repo
```

## Example Script Output

The script outputs raw structured data like this (you then organize it into the Report Output Format above):

```markdown
# Customer Feedback Data
**Period:** Last 7 days
**Generated:** 2026-02-02 17:30 UTC

## Summary
- GitHub Issues: 23
- NPS Responses: 89
- Email Feedback: 30
- Churn Cancellations: 144

## GitHub Issues
### #21234: Agent mode freezes on large files
- **URL:** https://github.com/YOUR_ORG/YOUR_REPO/issues/21234
- **State:** open
- **Created:** 2026-02-01T10:30:00Z
- **Comments:** 8
- **Labels:** bug, agent-mode
- **Body:**
```
When I open a file larger than 10MB, the agent freezes...
```

## NPS Survey Responses
### Score: 10
- **OS:** macOS
- **Date:** 2026-02-01
- **Comment:** Love the new agent mode! Makes coding so much faster.

### Score: 4
- **OS:** Windows
- **Date:** 2026-02-01
- **Comment:** SSH keeps disconnecting after a few minutes.
...

## Churn Cancellation Comments
144 cancellations with comments.

### build (72 cancellations)
- [example comment about usage frequency vs. cost]
- [example comment about switching to another tool]
...

### pro (48 cancellations)
- [example comment about pricing vs. feature usage]
...
```

## Notes

- The script outputs progress to stderr and the data to stdout, allowing easy piping
- Full feedback comments are displayed without truncation for complete context
- The Gmail module filters for emails to/from the address in `FEEDBACK_EMAIL`

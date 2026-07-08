# competitive-intelligence-agent

A reference implementation of a **PM / Competitive Intelligence Agent** built on [Warp](https://www.warp.dev/) — an AI-powered development environment with support for skills, cloud agents, and MCP integrations.

> **Disclaimer:** This is a scrubbed reference implementation. All proprietary identifiers
> (infrastructure IDs, SaaS keys, internal URLs, customer names, and actual report data)
> have been replaced with obvious placeholders. Reports in `reports/` are illustrative
> examples; actual generated reports contain confidential data and are not included.

---

## What it does

This agent gives a PM the skills to:

| Skill | Description |
|-------|-------------|
| `analyze_customer_feedback` | Fetches GitHub issues, NPS, email, and churn data; produces a weekly feedback report |
| `analyze_git_history` | Summarizes recent engineering activity from a git repository |
| `answer_pricing` | Projects a customer's cost across seat, usage, and hybrid pricing models from prior usage |
| `feature_research` | Competitive feature analysis across rival products |
| `fix_p0_issues` | Reads the weekly briefing, triages P0s, and spawns cloud coding agents |
| `post_to_slack` | Posts messages to a Slack channel via incoming webhook |
| `read_google_docs` | Reads content from a Google Doc by URL or document ID |
| `summarize_changelogs` | Summarizes competitor changelogs |
| `summarize_google_docs` | Reads and summarizes recently modified Google Docs |
| `votc_insights` | Extracts pain points, feature demand, and competitive signals from customer call transcripts (Grain) |
| `weekly_sentiment_analysis` | Weekly social-mention sentiment report via Octolens |
| `weekly_wynk` | Compiles all weekly reports into a "What You Need to Know" Notion page |
| `write_google_docs` | Creates and populates Google Docs |
| `write_notion` | Interacts with Notion via REST API |
| `write_prd` | Drafts Product Requirement Documents |

---

## Integrations

| Service | Used for | Auth method |
|---------|----------|-------------|
| **Google Workspace** (Drive, Docs, Gmail, BigQuery) | Reading/writing docs; NPS & churn queries via Metabase; email feedback | OAuth2 token (`GOOGLE_OAUTH_TOKEN`) |
| **Metabase** | Querying your data warehouse for NPS and subscription data | API key (`METABASE_API_KEY`) |
| **Grain** | Fetching customer meeting transcripts | PAT (`GRAIN_TOKEN`) |
| **Notion** | Writing weekly WYNK pages | Integration token (`NOTION_API_KEY`) |
| **Slack** | Posting reports | Incoming webhook (`SLACK_WEBHOOK_URL`) |
| **GitHub CLI (`gh`)** | Fetching public issues for feedback analysis | `gh auth login` |
| **Warp Oz** | Spawning cloud coding agents for P0 fixes | API key (`WARP_API_KEY`) |
| **Octolens** | Social-mention sentiment data | Octolens MCP server |

---

## Requirements

- Python 3.11+
- [Warp](https://www.warp.dev/) (for running skills as an agent)
- [GitHub CLI (`gh`)](https://cli.github.com/) — authenticated
- [Warp `oz` CLI](https://docs.warp.dev/) — for the `fix_p0_issues` skill

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/warpdotdev/competitive-intelligence-agent-oss.git
cd competitive-intelligence-agent-oss

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env and fill in your values (see Placeholders to replace below)

# 4. Authenticate GitHub CLI
gh auth login

# 5. Create Google OAuth credentials (for Docs/Gmail/Drive/BigQuery)
#    a. In Google Cloud Console, create or select a project and enable the
#       Google Docs, Google Drive, Gmail, and BigQuery APIs.
#    b. Create an OAuth 2.0 Client ID of type "Desktop app".
#    c. Download the client JSON and save it as credentials.json in the repo root.
#    (Both credentials.json and token.json are gitignored.)

# 6. Generate a read-only Google OAuth token (opens a browser; writes token.json)
python3 generate_readonly_token.py
```

> **Google auth note:** `generate_readonly_token.py` requires `credentials.json`
> from step 5 and exits with `Error: credentials.json not found` if it is missing.
> It writes `token.json`; for remote/cloud runs, set `GOOGLE_OAUTH_TOKEN` to the
> contents of that file.

---

## Placeholders to replace

Before using this, find and replace these placeholders in the codebase:

| Placeholder | What to replace it with | Files affected |
|-------------|------------------------|----------------|
| `YOUR_ORG/YOUR_REPO` | Your GitHub org and repo (e.g. `acme/myapp`) | `fetch_github_issues.py`, `analyze_feedback.py`, `analyze_customer_feedback/SKILL.md`, `votc_insights/SKILL.md`, `fix_p0_issues/SKILL.md`, `weekly_wynk/SKILL.md` |
| `YOUR_PRODUCT_CHANGELOG_URL` | Your product's public changelog URL | `summarize_changelogs/SKILL.md` |
| `YOUR_PRODUCT_DOCS_URL` | Your product's public docs URL | `feature_research/SKILL.md` |
| `your-gcp-project-id` | Your Google Cloud project ID | both `metabase_client.py` files, `set_oauth_token.sh` |
| `https://your-metabase-instance.metabaseapp.com` | Your Metabase URL | both `metabase_client.py` files |
| `METABASE_DATABASE_ID = 0` | Your Metabase database ID (integer) | both `metabase_client.py` files |
| `your_nps_survey_responses_table` | Your NPS survey table name in BigQuery | `fetch_nps_data.py` |
| `your_subscriptions_table` | Your subscriptions/churn table name | `fetch_churn_data.py` |
| `your_usage_events_table` | Your usage/consumption table and its `account_id`/`usage_units`/`usage_date`/`usage_type` columns | `answer_pricing/scripts/fetch_usage.py` |
| `YOUR_WORKSPACE_SLUG` | Your Notion workspace slug (in the WYNK parent page URL) | `weekly_wynk/SKILL.md` |
| `YOUR_OZ_ENVIRONMENT_ID` | Your Warp Oz cloud environment ID | `fix_p0_issues/SKILL.md` |
| `YOUR_NOTION_PARENT_PAGE_ID` | Notion page ID for the weekly WYNK parent | `weekly_wynk/SKILL.md` |
| `YOUR_CONTINUOUS_PLANNING_PAGE_ID` | Notion page ID for continuous planning | `weekly_wynk/SKILL.md` |
| `YOUR_NOTION_DATA_SOURCE_ID` | Notion data source ID for planning DB | `weekly_wynk/SKILL.md` |
| `https://hooks.slack.com/services/YOUR/WEBHOOK/URL` | Set the `SLACK_WEBHOOK_URL` env var (read automatically by `post_to_slack.py`) | `.env.example` |
| `your-app-client` | Path to your client application repo | `fix_p0_issues/SKILL.md`, `analyze_git_history/SKILL.md` |
| `your-app-server` | Path to your server repo | `fix_p0_issues/SKILL.md`, `analyze_git_history/SKILL.md` |

> A few skill docs also use illustrative example IDs — `YOUR_GOOGLE_DOC_ID`
> (`read_google_docs/`) and `YOUR_GOOGLE_DRIVE_FOLDER_ID` (`write_google_docs/`,
> `write_prd/`). These are runtime arguments you pass per invocation, not values
> to hardcode.

---

## Usage

Once configured, open the project in Warp and interact with the PM agent:

```
Analyze customer feedback for the last 7 days
```

```
Create a WYNK for this week
```

```
Fix the P0 issues from the latest briefing
```

Warp will automatically select the appropriate skill and execute the workflow.

---

## Repository structure

```
.
├── AGENTS.md                     # PM agent system prompt
├── generate_readonly_token.py    # Helper to generate Google OAuth token
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── .warp/
│   └── skills/                   # Warp agent skills
│       ├── analyze_customer_feedback/
│       ├── analyze_git_history/
│       ├── answer_pricing/
│       ├── feature_research/
│       ├── fix_p0_issues/
│       ├── post_to_slack/
│       ├── read_google_docs/
│       ├── summarize_changelogs/
│       ├── summarize_google_docs/
│       ├── votc_insights/
│       ├── weekly_sentiment_analysis/
│       ├── weekly_wynk/
│       ├── write_google_docs/
│       ├── write_notion/
│       └── write_prd/
├── knowledge/                    # Context documents for the agent
│   └── platform_credits.md
└── reports/                      # Generated report output (illustrative examples only)
    ├── customer_feedback_summaries/
    ├── competitor_changelog_reports/
    ├── votc_insights/
    ├── weekly_product_briefings/
    ├── weekly_wynk/
    ├── weekly_sentiment_analysis/
    ├── git_history_analysis/
    ├── feature_research/
    ├── prds/
    ├── pricing/
    └── release_notes_drafts/
```

---

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Denver Technologies, Inc.

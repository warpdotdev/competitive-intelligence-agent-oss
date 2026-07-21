---
name: setup
description: Sets up the competitive-intelligence-agent from scratch — clones the repo (or works from an existing clone), installs dependencies, configures .env credentials, authenticates GitHub and Google, and replaces codebase placeholders with the user's real values. Use when asked to "set up this agent", "run the setup skill", "deploy this agent", "configure this repo", or when a user has just cloned the repo and wants it working.
---

# Setup Skill

Use this skill to take a user from nothing (or a fresh clone) to a fully working PM / competitive-intelligence agent. Work through the phases in order, but skip anything that is already done — every step is idempotent. The user may only want a subset of integrations; ask early and only configure what they need, since each integration is independent.

## Phase 0: Locate or clone the repo

Check whether you are already inside the repo (look for `.warp/skills` and `AGENTS.md` in the current directory or a parent). If not:

```bash
git clone https://github.com/warpdotdev/competitive-intelligence-agent-oss.git
cd competitive-intelligence-agent-oss
```

If a clone already exists somewhere the user points you at, `cd` into it instead of re-cloning. Run all later commands from the repo root.

## Phase 1: Check prerequisites

Verify and report; offer install instructions for anything missing:

- **Python 3.11+** — `python3 --version`
- **GitHub CLI** — `gh --version` (needed for `analyze_customer_feedback` and report PRs)
- **Warp** — the user is presumably already running the agent in Warp
- **Oz CLI** — `oz whoami` (needed for `fix_p0_issues` and any Oz cloud runs):
  - **Command not found** → if the [Warp app](https://docs.warp.dev/getting-started/installation-and-setup) is already installed, the CLI ships with it. Otherwise, prefer the standalone Oz CLI — there is no need to install the full Warp app just for the CLI. See [Installing the CLI](https://docs.warp.dev/reference/cli#installing-the-cli); on macOS: `brew tap warpdotdev/warp && brew install --cask oz`.
  - **Not authenticated** → run `oz login` (interactive), or for CI/headless environments export `WARP_API_KEY`.

## Phase 2: Ask which integrations the user wants

Not every skill needs every credential. Ask the user which capabilities they care about, then only configure the corresponding integrations:

- **Google Workspace** (Docs, Drive, Gmail, BigQuery) → `analyze_customer_feedback`, `read/write/summarize_google_docs`, `write_prd`
- **Metabase** → NPS/churn queries in `analyze_customer_feedback`, usage pulls in `answer_pricing`
- **Grain** → `votc_insights`
- **Notion** → `weekly_wynk`, `write_notion`
- **Slack** → `post_to_slack`, `weekly_wynk`
- **Warp Oz API key** → `fix_p0_issues` (spawning cloud coding agents)
- **Octolens MCP** → `weekly_sentiment_analysis`
- **GitHub** → issue fetching in `analyze_customer_feedback`

Skills whose integrations are skipped will simply be unavailable until configured later — that's fine, say so.

## Phase 3: Install Python dependencies

Prefer a virtualenv — on modern macOS/Homebrew Python, bare `pip3 install` fails with an `externally-managed-environment` error:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The other skills invoke scripts with `python3`, so the venv must be active in the session where skills run. Tell the user to activate it (or ask if they prefer a global/user install where their environment allows it). `.venv` should be gitignored — add it if missing.

## Phase 4: Create and fill .env

```bash
cp -n .env.example .env
```

`.env` is gitignored; never overwrite an existing one without asking. Walk the user through each variable relevant to their chosen integrations (see the comments in `.env.example` for what each is used for):

- `GOOGLE_OAUTH_TOKEN` — filled in Phase 6
- `METABASE_API_KEY`
- `GRAIN_TOKEN`
- `NOTION_API_KEY`
- `SLACK_WEBHOOK_URL`
- `WARP_API_KEY`
- `FEEDBACK_EMAIL` — the Gmail address feedback emails arrive at
- Pricing rate variables (`SEAT_PRICE`, `USAGE_UNIT_PRICE`, etc.) — only if they want `answer_pricing`; these can also be passed as CLI flags later

**Handling secrets:** never ask the user to paste secret values into the chat, and never echo them. Ask the user to edit `.env` directly (offer to open it), then confirm which variables are set by checking for non-empty values without printing them:

```bash
awk -F= '/^[A-Z_]+=/ {sub(/[ \t]*#.*$/,""); v=substr($0, index($0,"=")+1); gsub(/[ \t]/,"",v); print $1 "=" (v=="" ? "<empty>" : "<set>")}' .env
```

Note: `SLACK_WEBHOOK_URL` and `FEEDBACK_EMAIL` ship with example values, so `<set>` for those may still mean unconfigured — confirm the user replaced `YOUR/WEBHOOK/URL` and `your-company.com`.

## Phase 5: Authenticate GitHub CLI

```bash
gh auth status || gh auth login
```

## Phase 6: Google OAuth (only if Google integrations are wanted)

1. Tell the user to do this in Google Cloud Console (you cannot do it for them):
   - Create/select a project; enable the **Google Docs, Google Drive, Gmail, and BigQuery** APIs.
   - Create an **OAuth 2.0 Client ID** of type **Desktop app**.
   - Download the client JSON and save it as `credentials.json` in the repo root (it is gitignored).
2. Then generate the token (opens a browser, writes `token.json`):

```bash
python3 generate_readonly_token.py
```

3. For local use, scripts read `token.json` via `GOOGLE_OAUTH_TOKEN`. Tell the user to set `GOOGLE_OAUTH_TOKEN` in `.env` to the contents of `token.json` (they can do this themselves; do not print the token). For remote/cloud runs, it goes in the environment's secrets instead.

## Phase 7: Replace codebase placeholders

The repo ships with obvious placeholders. Ask the user for the real values relevant to their chosen integrations, then find-and-replace across the codebase (`grep -rl '<placeholder>' .` to find affected files). **Do not replace inside `README.md` or this skill (`.warp/skills/setup/`)** — those mention the placeholders as documentation and must keep them:

- `YOUR_ORG/YOUR_REPO` — their GitHub org/repo (GitHub feedback, P0 fixes, WYNK)
- `YOUR_PRODUCT_CHANGELOG_URL` — public changelog URL (`summarize_changelogs`)
- `YOUR_PRODUCT_DOCS_URL` — public docs URL (`feature_research`)
- `your-gcp-project-id` — Google Cloud project ID (Metabase clients, `set_oauth_token.sh`)
- `https://your-metabase-instance.metabaseapp.com` — Metabase URL (both `metabase_client.py` files)
- `METABASE_DATABASE_ID = 0` — Metabase database ID, an integer (both `metabase_client.py` files)
- `your_nps_survey_responses_table` — BigQuery NPS table (`fetch_nps_data.py`)
- `your_subscriptions_table` — subscriptions/churn table (`fetch_churn_data.py`)
- `your_usage_events_table` — usage table + its column names (`answer_pricing/scripts/fetch_usage.py`)
- `YOUR_WORKSPACE_SLUG`, `YOUR_NOTION_PARENT_PAGE_ID`, `YOUR_CONTINUOUS_PLANNING_PAGE_ID`, `YOUR_NOTION_DATA_SOURCE_ID` — Notion workspace details (`weekly_wynk/SKILL.md`)
- `YOUR_OZ_ENVIRONMENT_ID` — Warp Oz cloud environment ID (`fix_p0_issues/SKILL.md`)
- `your-app-client`, `your-app-server` — paths to their application repos (`fix_p0_issues`, `analyze_git_history`)

Leave untouched: `YOUR_GOOGLE_DOC_ID` and `YOUR_GOOGLE_DRIVE_FOLDER_ID` — these are illustrative runtime arguments, not values to hardcode. Also leave placeholders for integrations the user skipped.

If they want `answer_pricing`, also remind them to describe their pricing model in `knowledge/platform_credits.md`.

## Phase 8: Verify

Run lightweight checks for the configured integrations and report a checklist of what works and what's still pending:

- Python imports: `python3 -c "import googleapiclient, google.cloud.bigquery, requests"`
- GitHub: `gh auth status`
- Google token exists: `test -f token.json`
- `.env` variables set (using the non-revealing awk check from Phase 4)
- Remaining placeholders: `grep -rn "YOUR_ORG/YOUR_REPO\|your-gcp-project-id\|your-metabase-instance" .warp --exclude-dir=setup` — expected to be empty for configured integrations

Finish with a short summary: which skills are ready to use, which are unconfigured, and one or two example prompts to try (e.g. "Analyze customer feedback for the last 7 days").

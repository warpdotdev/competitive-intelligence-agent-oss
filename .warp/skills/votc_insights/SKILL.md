---
name: votc_insights
description: Extracts customer insights from Grain meeting transcripts across all feedback channels over the last 7 days. Analyzes pain points, feature demand, and competitive signals from external customer meetings. Use when asked for "voice of the customer", "VoTC analysis", "customer call insights", or "what are customers saying."
---

# Voice of the Customer Insights Skill

Extract and synthesize customer insights from Grain meeting transcripts over the last 7 days. This skill uses the **Grain REST API** to fetch external customer meetings and their transcripts, then produces a structured report with pain point categorization, feature demand analysis, and competitive signals — all backed by specific customer quotes with verified external speaker attribution.

## When to Use

Use this skill when asked to:
- Analyze recent customer conversations for product insights
- Generate a "voice of the customer" or VoTC report
- Identify customer pain points and feature requests from calls
- Prepare customer evidence for product planning or roadmap discussions

Do NOT use this skill when:
- You need GitHub issues, NPS, or email feedback — use `analyze_customer_feedback` instead
- You need a full weekly briefing — use `weekly_product_briefing` instead

## Prerequisites

- **`GRAIN_TOKEN` environment variable** must be set with a Grain Personal Access Token (PAT) or Workspace Access Token. Tokens start with `grain_pat_...`. Get one from Grain Settings > Integration > API. In cloud agent environments, this is configured as an environment secret.
- **`requests` Python package** must be installed (`pip3 install requests`).
- The Grain MCP server is **not required** — this skill uses the REST API directly.

## Grain API Reference

- **Base URL:** `https://api.grain.com/_/public-api/v2`
- **Auth:** `Authorization: Bearer <GRAIN_TOKEN>`
- **Required header:** `Public-Api-Version: 2025-10-31`
- **Key endpoints:**
  - `POST /recordings` — list recordings with filters (date range, `participant_scope`, pagination via `cursor`)
  - `GET /recordings/{id}/transcript` — get transcript segments for a recording
- **Docs:** https://developers.grain.com

### Speaker Attribution

The participant `id` field returned in recording metadata **matches** the `participant_id` field in transcript segments. This is the key to reliable internal/external speaker attribution:

1. Request recordings with `"include": {"participants": true}` to get participant data with `id`, `name`, `scope` ("internal"/"external"/"unknown"), and `email`.
2. Each transcript segment has a `participant_id` field.
3. Join on `(recording_id, participant_id)` to determine who said what.

**Important:** You must include the participant `id` field when extracting participant data. Without it, speaker attribution will fail.

## Workflow

### Step 1: Fetch Meetings and Transcripts

Resolve the skill directory and the repo root:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
SKILL_DIR="$REPO_ROOT/.warp/skills/votc_insights"
```

The Grain token is available as the `GRAIN_TOKEN` environment variable (configured as an environment secret in remote environments).

Run the data collection script:

```bash
python3 "$SKILL_DIR/fetch_grain_data.py" \
  --days 7 \
  --output /tmp/grain_votc_data.json
```

This fetches all external customer meetings from the last 7 days with full transcripts. The script handles pagination automatically. Output is a JSON file with `meetings` (metadata + participants with IDs) and `transcripts` (segments with `participant_id`).

### Step 2: Analyze Transcripts

Run the analysis script to extract categorized quotes from external speakers:

```bash
python3 "$SKILL_DIR/analyze_transcripts.py" /tmp/grain_votc_data.json \
  --output /tmp/votc_analysis.json
```

This produces:
- Categorized quotes from **external speakers only** (filtered via `participant_id` → `scope` matching)
- Categories: pain_points, pricing, competitive, feature_requests, security, integrations, churn_risk, positive, agents
- Deduplication by meeting + text prefix
- Summary printed to stderr with counts and sample quotes

### Step 3: Review and Synthesize

Read the analysis output (`/tmp/votc_analysis.json`) and the raw data (`/tmp/grain_votc_data.json`). Use the categorized external quotes to build the report. For each category:

1. **Count distinct customers** — group quotes by company (derive from meeting title and participant email domains).
2. **Select the strongest quotes** — prioritize quotes that are specific, mention concrete pain/need, or reference competitors.
3. **Cross-reference categories** — a customer who mentions both pricing and a competitor is a churn signal.

You can also query the raw transcript data directly for additional context beyond the keyword-based categories. The analysis script is a starting point — use your judgment to identify themes the keywords may have missed.

### Step 4: Read Previous Report for Trend Comparison

```bash
ls "$REPO_ROOT/reports/votc_insights/"*.md 2>/dev/null | sort | tail -1
```

If a previous report exists, read it and compare:
- Which pain points are **new** (not in the previous report)
- Which pain points **recurred** (present in both)
- Which pain points from the previous report **did not recur**
- Same for feature requests and competitive mentions

### Step 5: Compile the Report

Write the report following the output format below. Every claim must include:
- **Customer name** and **contact name** (from meeting participant data)
- **Direct quote** from the transcript (verbatim, italicized)
- **Meeting date**
- **Quantified impact** where available (e.g., "2.8x productivity", "$500/month spend")

### Step 6: Save Report and Create PR

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
DATE=$(date +%Y-%m-%d)
BRANCH="votc-insights-$DATE"
git -C "$REPO_ROOT" checkout main
git -C "$REPO_ROOT" checkout -b "$BRANCH"
git -C "$REPO_ROOT" add reports/votc_insights/
git -C "$REPO_ROOT" commit -m "report: VoTC insights $DATE

Co-Authored-By: Oz <oz-agent@warp.dev>"
git -C "$REPO_ROOT" push -u origin "$BRANCH"
gh pr create --repo YOUR_ORG/YOUR_REPO --base main --head "$BRANCH" \
  --title "VoTC Insights Report — $DATE" \
  --body "Voice of the Customer insights report for the week ending $DATE. Generated from Grain meeting transcripts via REST API.

Co-Authored-By: Oz <oz-agent@warp.dev>"
```

## Report Output Format

```markdown
# Voice of the Customer Insights Report

**Report Date:** [date]
**Analysis Period:** [start date] – [end date] (7 days)
**Data Source:** Grain meeting transcripts (via Grain REST API) — [N] external customer meetings
**Prepared by:** Product PM Agent

---

## Executive Summary

[2-3 sentence factual overview. State the number of meetings analyzed, number of distinct customers, and the top 3 themes by frequency. No opinions or recommendations.]

---

## 1. Customer Pain Points

### 1.1 [Category Name] — [N] customers
**Frequency:** [N] quotes from external speakers across [N] meetings
**Impact:** [Factual impact: blocking deals, causing churn, workaround exists]
**Previous report:** [New / Recurring — N mentions last report / Not in previous report]

- **[Company]** ([Contact Name], [date]): *"[direct quote]"*
- **[Company]** ([Contact Name], [date]): *"[direct quote]"*

### 1.2 [Category Name] — [N] customers
...

---

## 2. Competitive Landscape

### 2.1 Competitor Mentions (by frequency)
1. **[Competitor]** — Mentioned by external speakers in [N] conversations. [Factual summary of how customers referenced it.]
2. **[Competitor]** — ...

### 2.2 Competitive Positioning Signals
- [Factual observation with customer quote]
- [Factual observation with customer quote]

---

## 3. Feature Demand Analysis

### 3.1 Most Requested Features (by frequency and urgency)

**P0:**
- **[Feature]** — [N] customers ([Company 1], [Company 2], ...). Segments: [segment list].
  - *"[representative quote]"* — [Contact], [Company]

**P1:**
- **[Feature]** — [N] customers. Segments: [segment list].

**P2:**
- ...

### 3.2 Customer Segment Patterns
- **Large Enterprise (500+ eng):** [themes] → [Company 1], [Company 2]
- **Mid-Market Tech (50–500 eng):** [themes] → [Company 1], [Company 2]
- **SMB / Startups (< 50 eng):** [themes] → [Company 1], [Company 2]
- **Non-traditional:** [themes] → [Company 1], [Company 2]

---

## 4. Success Stories & Positive Outcomes

### 4.1 Quantified Impact
- **[Company]** ([Contact]): [outcome]. *"[quote]"*
- **[Company]** ([Contact]): [outcome]. *"[quote]"*

### 4.2 Product Champions
- **[Company]** ([Contact]): [evidence of advocacy]. *"[quote]"*

---

## 5. Week-over-Week Changes

### New themes (not in previous report)
- [Theme] — [N] customers

### Recurring themes
- [Theme] — [N] customers this week, [N] last report

### Themes from previous report that did not recur
- [Theme] — [N] last report, 0 this week

---

## Appendix: Companies Referenced

[Alphabetical list of all companies mentioned in the report]

---

*Data sourced from Grain meeting transcripts via Grain REST API (public-api/v2). All quotes are from external speakers, identified via participant_id matching. All customer names and quotes should be treated as confidential.*
```

## Guidelines

- **Evidence-driven.** Every claim must cite a specific customer, quote, and meeting date. If you can't cite it, don't include it.
- **External voices only.** The analysis script filters to `scope == "external"` via participant_id matching. Only use quotes from external speakers.
- **Deduplicate across categories.** The same transcript segment may match multiple keyword categories. Count each customer mention once per theme.
- **Quantify everything.** Number of customers, number of external-speaker quotes, number of meetings. Avoid vague terms like "several" or "many."
- **Verbatim quotes.** Use exact transcript quotes, italicized. Do not paraphrase or clean up customer language.
- **No editorializing in Sections 1–4.** Report facts only. Do not use words like "alarming", "critical", "exciting". Do not make recommendations — the WYNK skill handles that.
- **Confidentiality.** All customer names and quotes are confidential internal data. Note this at the end of the report.

## Scripts

This skill includes two Python scripts in the skill directory:

- **`fetch_grain_data.py`** — Fetches external meetings and transcripts from the Grain REST API. Handles pagination, preserves participant IDs for speaker attribution.
- **`analyze_transcripts.py`** — Analyzes transcripts for VoTC themes using keyword matching. Filters to external speakers only via participant_id → scope matching. Outputs categorized quotes as JSON.

Both scripts log progress to stderr and output JSON to stdout (or a file via `--output`).

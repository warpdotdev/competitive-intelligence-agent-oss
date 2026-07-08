---
name: write_prd
description: Writes Product Requirement Documents (PRDs) by synthesizing customer feedback, competitive research, git history, and internal docs into a structured, decision-ready spec. Use when asked to "write a PRD", "create a product spec", "draft requirements for [feature]", "spec out [feature]", or "write a product requirements document."
---

# Write PRD Skill

Use this skill to produce a PRD for a proposed feature or product change. The PRD synthesizes existing data sources into a structured document ready for stakeholder review.

## Inputs

The user will provide:
1. **Feature name/description** (required) — what to spec out
2. **Target users** (optional) — who this is for
3. **Constraints** (optional) — timeline, technical, or business constraints
4. **Related URLs/docs** (optional) — Notion pages, Google Docs, GitHub issues, competitor URLs
5. **Priority level** (optional) — P0/P1/P2

## Workflow

### Step 1: Gather Context

Check `reports/` for recent, relevant data:
- `reports/customer_feedback_summaries/` — user pain points related to the feature
- `reports/competitor_changelog_reports/` or `reports/feature_research/` — competitive positioning
- `reports/git_history_analysis/` — current engineering work related to the feature
- `reports/weekly_product_briefings/` — recent briefings mentioning the feature area

If existing reports are stale (>7 days) or the user requests fresh data, run the relevant skills:
- `analyze_customer_feedback` — for user pain points and NPS data
- `feature_research` — for competitive analysis (if competitor URLs provided)
- `summarize_google_docs` — for internal doc context (if Google Doc URLs provided)
- `analyze_git_history` — for engineering priorities and current work

### Step 2: Search Notion

Use the Notion MCP (`notion-search`) to find related product docs, specs, or prior PRDs:

```
query: "<feature name> product requirements"
query_type: "internal"
```

Fetch any relevant results with `notion-fetch` and extract goals, prior decisions, constraints, or open questions that should inform the PRD.

If Notion is unavailable (auth error), skip this step and note it.

### Step 3: Draft the PRD

Fill in the output template below using the gathered context. Every claim in the Problem Statement and Technical Considerations sections must cite its source (report name, Notion page, or URL).

### Step 4: Publish

1. Save to `reports/prds/prd_<feature_slug>_YYYY-MM-DD.md`
2. Create a PR with the PRD
3. If requested, write to Google Docs using the `write_google_docs` skill:
   ```bash
   python skills/write_google_docs/write_google_doc.py --title "PRD: <Feature Name>" --folder-id YOUR_GOOGLE_DRIVE_FOLDER_ID --content-file reports/prds/prd_<feature_slug>_YYYY-MM-DD.md
   ```
4. If requested, create a Notion page using `notion-create-pages`
5. If requested, post a summary to Slack using the `post_to_slack` skill

## Output Format

---BEGIN FORMAT---

# PRD: [Feature Name]
**Author:** [Agent + user]
**Date:** [YYYY-MM-DD]
**Status:** Draft
**Priority:** [P0/P1/P2]

## TL;DR
[1-2 sentence summary of what this feature is and why it matters.]

## Problem Statement
[What user problem does this solve? Include evidence from customer feedback, NPS data, or support tickets. Cite sources.]

- **User pain points:** [specific issues from feedback reports]
- **Frequency/severity:** [how many users affected, how often]
- **Current workarounds:** [what users do today]

## Goals & Success Metrics
- **Goal 1:** [description] — Metric: [how to measure]
- **Goal 2:** [description] — Metric: [how to measure]

**Non-goals:** [what this feature explicitly does NOT aim to do]

## Target Users
- **Primary:** [user segment, with context on why]
- **Secondary:** [user segment, if applicable]

## Scope

**In scope:**
- [capability 1]
- [capability 2]

**Out of scope:**
- [explicitly excluded item 1]
- [explicitly excluded item 2]

## Proposed Solution

### Overview
[High-level description of the solution approach.]

### Key User Flows
1. [Flow 1: step-by-step description]
2. [Flow 2: step-by-step description]

## Technical Considerations
- **Dependencies:** [systems, APIs, or teams required]
- **Risks:** [technical risks with mitigation strategies]
- **Known constraints:** [performance, compatibility, or platform constraints]

## Competitive Context
[Brief summary of how competitors handle this. Cite feature_research or changelog reports if available.]

## Open Questions
- [ ] [Question 1 — owner if known]
- [ ] [Question 2]

## References
- [Link to customer feedback report]
- [Link to competitive research]
- [Link to internal docs or Notion pages]
- [Link to related GitHub issues]

---END FORMAT---

## Guidelines

- Be evidence-driven: cite the source (report name, Notion page, URL, or issue number) for every important claim
- Separate facts from assumptions from opinions — label each clearly
- Flag open questions that need a human decision with `[NEEDS DECISION]`
- Keep it concise — a PRD should be skimmable in 5 minutes
- If data is missing or unavailable, say so rather than guessing
- Prefer concrete metrics over vague goals (e.g., "reduce error rate by 50%" not "improve reliability")

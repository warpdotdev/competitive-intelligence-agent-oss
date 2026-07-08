---
name: weekly_wynk
description: Compiles the most recent reports into a weekly What You Need to Know (WYNK) Notion page with sections for Executive Summary, Customer Feedback, Engineering Investments, Competitive Landscape, and Recommendations. Use when asked to "create a WYNK", "compile weekly reports", or "what do I need to know this week."
---

# Weekly WYNK (What You Need to Know) Skill

Compile the most recent reports from `reports/` into a single, leadership-ready Notion page under the [Weekly WYNK](https://www.notion.so/YOUR_WORKSPACE_SLUG/Weekly-WYNK-YOUR_NOTION_PARENT_PAGE_ID) parent page. This skill does NOT re-run data collection — it reads existing report artifacts and synthesizes them. Sections 1–5 are strictly factual reporting; Section 6 (Recommendations (Beta)) is the only section where the agent may make judgements or strategic recommendations.

**Notion Parent Page ID:** `YOUR_NOTION_PARENT_PAGE_ID`

## When to Use

Use this skill when asked to:
- Create a weekly WYNK or "what you need to know" document
- Compile or roll up existing reports into one document
- Prepare an executive summary of recent product intelligence

Do NOT use this skill when:
- Reports haven't been generated yet — run the individual skills first (`analyze_customer_feedback`, `summarize_changelogs`, `analyze_git_history`)

## Workflow

### Step 1: Discover Latest Reports

First, resolve the repository root so report paths work regardless of the agent's working directory:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
```

Then find the most recent report in each of these directories. **Sort by filename, not filesystem modification time** — report filenames contain `YYYY-MM-DD` dates, and `ls -t` is unreliable in freshly cloned repos where all files share the same mtime:

```bash
ls "$REPO_ROOT/reports/customer_feedback_summaries/"*.md 2>/dev/null | sort | tail -1
ls "$REPO_ROOT/reports/votc_insights/"*.md 2>/dev/null | sort | tail -1
ls "$REPO_ROOT/reports/git_history_analysis/"*.md 2>/dev/null | sort | tail -1
ls "$REPO_ROOT/reports/competitor_changelog_reports/"*.md 2>/dev/null | sort | tail -1
ls "$REPO_ROOT/reports/weekly_sentiment_analysis/"*.md 2>/dev/null | sort | tail -1
```

At least 1 report must exist. If no reports are found in any directory, stop and tell the user to run the relevant data collection skills first.

Also check for a previous WYNK report for trend comparison:
```bash
ls "$REPO_ROOT/reports/weekly_wynk/"*.md 2>/dev/null | sort | tail -1
```

Also query the **Continuous Planning** Notion page for active company priorities. Fetch north star metrics from the page (ID: `YOUR_CONTINUOUS_PLANNING_PAGE_ID`) and query your planning data source (ID: `YOUR_NOTION_DATA_SOURCE_ID`) for active items.

> **Setup required:** Update the filter below to match your organization's status values and functional area (FA) taxonomy before using this skill.

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/YOUR_NOTION_DATA_SOURCE_ID/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "page_size": 100,
    "filter": {
      "and": [
        {"property": "Status", "status": {"does_not_equal": "Shipped"}},
        {"property": "Status", "status": {"does_not_equal": "Not prioritized"}}
      ]
    }
  }'
```

Paginate if `has_more` is true. Extract each item's title, `Status`, functional area, category, and target ship date. This data is used in Section 3 (Engineering Investments) to align git activity with company priorities.

**Important:** Use `$REPO_ROOT/reports/...` for ALL report paths throughout this skill, including when reading reports in Step 2 and saving the output in Step 6.

### Step 2: Read the Reports

Read the most recent file from each directory found in Step 1. Also read the previous WYNK report (if any) to track trends and follow up on prior recommendations.

### Step 3: Synthesize into 6 Sections

Write content for each section. Be **matter-of-fact and evidence-driven** — cite specific issue numbers, customer names, commit counts, and competitor names. Sections 1–5 must **report facts only**: no judgements, assumptions, interpretations, or editorializing. Save all opinions and strategic recommendations for Section 6 (Recommendations (Beta)). Each section should be self-contained and skimmable.

**Quantitative over qualitative.** Always lead with numbers (counts, percentages, week-over-week deltas) rather than qualitative characterizations. Do NOT use dramatic or inflated adjectives such as "dominated", "surged", "intensified", "skyrocketed", "exploded", "massive", "sweeping", or similar. These obscure the core information. Instead, state the fact with its number and let the reader draw conclusions.

#### Formatting & Linking Rules (apply to all sections)

**GitHub issue links:** Every GitHub issue number must be a clickable hyperlink. Format: `[#NNNN](https://github.com/YOUR_ORG/YOUR_REPO/issues/NNNN)`. The source `customer_feedback_summaries` report contains full URLs — extract the base URL from there rather than hardcoding it. Replace `YOUR_ORG/YOUR_REPO` with your actual repository.

**Cross-section references:** Do NOT write "Section 2" or "(Section 3, ...)". Use Notion `<mention-page>` inline links to the actual child pages so readers can click to navigate. Format: `<mention-page url="https://www.notion.so/{SECTION_PAGE_ID}">Customer Feedback</mention-page>`. To make this work, create all 6 section pages as empty pages first (Step 5b), capture their IDs, then populate content with correct cross-references (Step 5c).

**Source citations:** Do NOT use raw report filenames like `(feedback_analysis_2026-03-16)`. Use readable italicized citations: `*Source: Feedback Report, Mar 16*`, `*Source: VoTC Report, Mar 13*`, `*Source: Git Analysis, Mar 16*`, `*Source: Competitive Changelog, Mar 16*`. Omit citations when the source is obvious from context (e.g., competitor moves clearly come from the changelog report).

**Code formatting:** Use inline code (backticks) for branch names (e.g., `jeff/drop-tables-and-columns`), commands (e.g., `/pr`), commit hashes, and file paths.

**Your product comparison notes (Competitive Landscape only):** Italicize your product's current-state comparison for each competitor move to visually separate it from the competitor's action. Example: *[Your product] supports X but does not support Y.*

#### Section 1: Executive Summary

A skimmable, quantitative snapshot for someone who reads nothing else. Structure as **Top 3 Things to Know** across three categories, using bullet lists (not prose). Use `<mention-page>` links to point readers to the deeper sections for details.

**Strategic framing:** Use the active company priorities and north-star metrics from the Continuous Planning page (queried in Step 1) to contextualize the week's signals. Open with a 1–2 sentence strategic frame that connects the week's most important data points back to those priorities. This should feel like a CEO reminding the team what matters and why this week's data is relevant — not a generic summary. Reference specific priorities by name when the week's data directly relates to them.

Structure as follows:

1. **Strategic frame** — 1–2 sentences connecting the week's top signals to the company's current strategic priorities (drawn from the Continuous Planning page).
2. **Date range** — State the date range and data sources covered in a single line.
3. **Customer Feedback — Top 3** — Three bullet points summarizing the most important customer signals. Each bullet must lead with a quantitative fact (e.g., mention count, issue count, churn count, week-over-week delta) before any qualitative context. Use `<mention-page>` link to Customer Feedback section.
4. **Engineering Investments — Top 3** — Three bullet points summarizing the most important engineering activity. Each bullet must lead with a quantitative fact (e.g., commit count, PR count, files touched). Use `<mention-page>` link to Engineering Investments section.
5. **Competitive Landscape — Top 3** — Three bullet points summarizing the most important competitive signals. Each bullet must lead with a quantitative fact (e.g., number of releases, number of competitors shipping a feature). Use `<mention-page>` link to Competitive Landscape section.
6. **Since last WYNK** — If a previous WYNK exists, close with a short paragraph noting what changed: metrics that moved, issues opened or closed, and which items from the prior WYNK have been addressed.

No opinions, recommendations, or judgements in this section. Keep it under 300 words. Every bullet must start with a number or metric. Do not use dramatic adjectives — let the numbers speak.

#### Section 2: Customer Feedback

Synthesize `customer_feedback_summaries` (quantitative: GitHub issues, NPS, email) and `votc_insights` (qualitative: enterprise customer call transcripts). Organize as:

- **Critical Issues** — P0 problems affecting users now. Each item should lead with a bold descriptive title, then the linked issue number(s), comment count, a one-line description, and status (open/closed/resolved). Example format: `**SIGABRT crash during window drag-resize** — [#8881](url) (3 comments). Panic in ... Status: open.`
- **Trending Themes** — Themes appearing across multiple sources or growing week-over-week. Cite the specific issues, NPS responses, or email threads that form each theme.
- **NPS Signals** — What promoters are citing and what detractors are citing. Reference specific verbatim quotes and feedback IDs. Do not report the NPS score itself.
- **Enterprise Signals** — Key themes from customer calls. Cite specific customer names and direct quotes. Report what was said — do not infer intent or predict outcomes.
- **Churn Risks** — Explicit cancellations or competitive defections. Cite the specific evidence (e.g., customer name, cancellation ticket, stated reason). Only include risks backed by direct evidence, not speculation.
- **Social Sentiment** — Synthesize from `weekly_sentiment_analysis`. Include: sentiment score and mention volume with week-over-week deltas, top positive and negative themes from social mentions, and any overlap with themes from other feedback channels (GitHub, NPS, VoTC). Cite representative mention links. Include 1–2 standout testimonials if available.

Do NOT copy-paste from reports. Synthesize and cross-reference: e.g., if both NPS detractors and enterprise customers cite the same issue, note that overlap with specific references to both sources. Do NOT characterize issues as "alarming", "concerning", etc. — just report the facts.

#### Section 3: Engineering Investments

Synthesize `git_history_analysis` and the **Continuous Planning** Notion page. Focus exclusively on **what was built and what changed** — features, commits, and code. Do NOT include individual team member names, author summaries, contributor credits, or per-person breakdowns. The audience cares about what shipped and what's in progress, not who did it.

Organize as:

- **What Shipped** — Key features merged in the period, grouped by theme (e.g., Agent Orchestration, Code Review, Platform). Cite specific PRs or commit ranges.
- **What's In Progress** — Active branches and their status. Cite branch names and latest commit dates.
- **Focus Areas** — Where engineering effort is concentrated, by commit count and area. Report the numbers — do not attribute work to individuals.
- **Alignment with Company Priorities** — Cross-reference git activity against the active items from the Continuous Planning page (queried in Step 1). For each major engineering theme, note whether it maps to a prioritized Continuous Planning item and state that item's status (e.g., "1 - Prioritized", "2 - In progress", "3 - Dogfood"). Flag any significant engineering effort that does not map to an active planning item. Flag any high-priority planning items (status 1–3) with no visible engineering activity in the period. Report facts only — do not make judgements about whether engineering "should" be working on something.
- **Overlap with Customer Feedback** — Cross-reference with the Customer Feedback section (use `<mention-page>` link). For each top customer issue, state whether there is a corresponding branch, merged PR, or no visible engineering activity. Link the specific issue numbers. Do not make judgements about whether engineering "should" be working on something.
- **Cleanup & Tech Debt** — Notable refactoring, dead code removal, or infrastructure improvements. Cite specific PRs.

#### Section 4: Competitive Landscape

Synthesize `competitor_changelog_reports`. Organize as:

- **Key Competitor Moves** — The 3-5 most notable things competitors shipped. For each: what they shipped and a factual comparison to your product's current capabilities (e.g., "Competitor X shipped Y; [your product] does/does not have equivalent functionality").
- **Industry Themes** — Common patterns across multiple competitors (e.g., "3 of 5 tracked competitors shipped cloud agent features this week"). Cite the specific competitors and features.
- **Where Your Product Has Parity or Leads** — Capabilities where your product matches or exceeds competitors, with specific feature-to-feature evidence.
- **Where Competitors Have Shipped Ahead** — Capabilities competitors have that your product does not, with specific feature-to-feature evidence.
- **Notable Gaps** — Areas where no tracked competitor (including your product) has shipped. Cite the evidence for the gap (e.g., customer requests with no competitor solution).

#### Section 5: Open Questions

List unresolved questions, missing data, and areas where the reports are ambiguous or incomplete. Use a **`###` heading per question** (not bullet lists or horizontal rules) so each question is scannable and linkable in Notion's sidebar. Format:

```
### 1. Short question as heading
**Context:** cite the specific evidence using `<mention-page>` links to the relevant sections and linked issue numbers.
**What would resolve it:** what data or action would answer the question.
```

This section is strictly factual — it identifies what we don't know, not what we should do about it.

#### Section 6: Recommendations (Beta)

**This is the only section where the agent may make judgements, interpretations, and strategic recommendations.** Everything in Sections 1–5 is factual reporting; this section is where opinions live.

Cross-reference all sections to produce prioritized, actionable recommendations. Use a **`##` heading per recommendation** with sequential numbering. Format each as:

```
## N. Recommendation title
**Priority:** P0 (this week) | **Type:** Product + Engineering
**Evidence:** cite specific facts using `<mention-page>` links to sections and linked issue numbers.
**Reasoning:** explain the judgement.
**Suggested owner:** team or area
```

**Numbering must be sequential** (1, 2, 3, ...) with no gaps. Order by priority, then by strength of evidence. Aim for 5-10 recommendations total — enough to be comprehensive, few enough to be actionable.

Label this section clearly as containing agent-generated opinions, not established facts.

### Step 4: Self-Review

Before writing to Notion, review all section content against the following checklist. Fix any violations before proceeding.

1. **Facts only in Sections 1–5.** Scan each section for judgement words (e.g., "alarming", "critical priority", "should", "we need to", "concerning", "exciting", "unfortunately"). Remove or rephrase them to be neutral and factual. Move any opinions or recommendations to Section 6.
2. **Every claim has specific evidence.** Every factual statement must cite at least one of: issue number, PR/branch name, customer name, specific quote, commit count, competitor name + feature, or date. If a claim has no citation, either add one or remove the claim.
3. **No NPS score reported.** Confirm the NPS score number does not appear anywhere. NPS verbatim quotes and themes are fine.
4. **Recommendations only in Section 6.** Confirm Sections 1–5 contain zero recommendations, action items, or "should" statements. Section 6 is clearly labeled as agent-generated opinions.
5. **Open Questions section is complete.** Confirm any ambiguity or missing data surfaced during synthesis is captured in Section 5.
6. **Cross-references use `<mention-page>` links.** Confirm no raw "Section N" references remain. Every cross-reference must use a `<mention-page url="...">Title</mention-page>` link to the actual Notion child page. If a page ID is missing, flag it for update after page creation.
7. **All GitHub issue numbers are linked.** Scan for any bare `#NNNN` references and convert them to `[#NNNN](https://github.com/YOUR_ORG/YOUR_REPO/issues/NNNN)` links.
8. **No raw report filenames in citations.** Scan for strings like `feedback_analysis_`, `votc_insights_report_`, `git_analysis_`, `competitive_changelog_`. Replace with readable italicized format (e.g., `*Source: Feedback Report, Mar 16*`).
9. **Recommendation numbering is sequential.** Confirm recommendation headings are numbered 1, 2, 3, ... with no gaps.
10. **Branch names and commands use inline code.** Confirm branch names, commands, commit hashes, and file paths are wrapped in backticks.
11. **No inflated adjectives.** Scan for dramatic or inflated language ("dominated", "surged", "intensified", "skyrocketed", "exploded", "massive", "sweeping", "critical" used as emphasis). Replace with quantitative facts or neutral descriptions. Numbers convey magnitude better than adjectives.

If any violations are found, fix them before proceeding to Step 5.

### Step 5: Write to Notion

Use the `write_notion` skill to create pages in Notion. Refer to that skill for authentication and API details.

**Parent Page ID:** `YOUR_NOTION_PARENT_PAGE_ID`

The structure is: **one parent page per week** with **6 child pages** (one per section). This keeps each section navigable in Notion's sidebar.

#### 5a. Create the weekly parent page

Create an empty parent page under the Weekly WYNK page. This page serves as a container — it should have no content blocks of its own.

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "YOUR_NOTION_PARENT_PAGE_ID"},
    "icon": {"type": "emoji", "emoji": "📋"},
    "properties": {
      "title": {
        "title": [{"text": {"content": "WYNK — Week of YYYY-MM-DD"}}]
      }
    }
  }' | jq
```

Capture the returned `id` — this is the `WEEK_PAGE_ID` used as the parent for all section pages.

#### 5b. Create all 6 empty child pages and capture IDs

Create all 6 section child pages **without content** first. This gives you every page ID upfront so that cross-section `<mention-page>` links can reference the correct URLs when you populate content in Step 5c.

For each section, create an empty page under `WEEK_PAGE_ID`:

```json
{
  "parent": {"page_id": "WEEK_PAGE_ID"},
  "icon": {"type": "emoji", "emoji": "SECTION_EMOJI"},
  "properties": {
    "title": {
      "title": [{"text": {"content": "Section Title"}}]
    }
  }
}
```

Create pages in this order and capture each returned `id`:

1. 📊 Executive Summary → `EXEC_PAGE_ID`
2. 💬 Customer Feedback → `FEEDBACK_PAGE_ID`
3. 🔧 Engineering Investments → `ENG_PAGE_ID`
4. 🏁 Competitive Landscape → `COMP_PAGE_ID`
5. ❓ Open Questions → `QUESTIONS_PAGE_ID`
6. 💡 Recommendations (Beta) → `RECS_PAGE_ID`

You now have all 6 page IDs. Construct `<mention-page>` URLs as `https://www.notion.so/{PAGE_ID_WITHOUT_DASHES}`.

#### 5c. Populate section pages with content

Now write each section's content using the Notion API (or MCP Notion tool). You can use `replace_content` or append children blocks. Because you have all page IDs from Step 5b, your content can include correct `<mention-page>` cross-references.

If a section's content exceeds 100 blocks, create the first batch then append the rest:

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{section_page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d @/tmp/wynk_section_N_remaining.json | jq
```

#### 5d. Collect URLs

The weekly parent page URL is `https://www.notion.so/{WEEK_PAGE_ID}`. Use this as the main link when distributing.

### Step 6: Save and Distribute

1. **Save locally:** Combine all 6 sections into a single markdown file and save to `$REPO_ROOT/reports/weekly_wynk/wynk_YYYY-MM-DD.md` (using the `REPO_ROOT` variable from Step 1). Use this structure:
```
# WYNK — Week of YYYY-MM-DD
Generated: YYYY-MM-DD
Notion Page: [link]

---
## Executive Summary
[Section 1 content]

---
## Customer Feedback
[Section 2 content]

---
## Engineering Investments
[Section 3 content]

---
## Competitive Landscape
[Section 4 content]

---
## Open Questions
[Section 5 content]

---
## Recommendations (Beta)
[Section 6 content]
```

2. **Post to Slack:** Use the `post_to_slack` skill to post the Executive Summary + Notion page link to Slack:
   ```
   ${SLACK_WEBHOOK_URL}
   ```

3. **Create a PR** with the new report file.

## Guidelines

- **Be matter-of-fact.** Sections 1–5 report what happened. No adjectives like "alarming", "exciting", "critical". No recommendations or "should" statements. No speculation about causes or outcomes. Just the facts with specific evidence.
- **Prefer numbers over adjectives.** Do not use dramatic or inflated adjectives ("dominated", "surged", "intensified", "skyrocketed", "exploded", "massive", "sweeping"). State the quantitative fact and let the reader interpret magnitude. For example, write "60 mentions (up from 56)" instead of "mentions surged."
- **Tone of voice.** Write in a direct, technical style. The WYNK should read like it was written by someone deeply technical who respects the reader's time — direct, confident, no filler, no corporate jargon. When in doubt, prefer shorter sentences and concrete language over abstraction.
- **Synthesize, don't copy-paste.** The value of the WYNK is cross-referencing across reports, not duplicating them. Readers can click through to full reports for details.
- **Every claim needs a specific citation.** Issue numbers (linked), PR names, customer names, direct quotes, commit counts, competitor names, dates. If you can't cite it, don't include it.
- **Link everything linkable.** GitHub issues must be hyperlinks. Cross-section references must be `<mention-page>` links. Branch names and commands must use inline code. Raw report filenames must never appear in the output.
- **Opinions go in Recommendations (Beta) only.** Sections 1–5 are strictly factual. Section 6 is clearly labeled as agent-generated judgements and is the only place for interpretations, priorities, and strategic recommendations.
- **Keep it concise.** The full WYNK (all 6 sections combined) should be under 500 lines of markdown. Link to full reports for details.
- **Track trends.** If a previous WYNK exists, explicitly compare: metrics that went up or down, issues opened or closed, items from the prior WYNK that have been addressed.
- **Flag missing data.** If a report directory is empty or reports are stale (>14 days old), note this in the Executive Summary so readers know the coverage gaps.
- **No NPS score.** Do not report the NPS number. NPS verbatim quotes, themes, and promoter/detractor signals are fine.

## Prerequisites

- Reports must already exist in `reports/`. Run the data collection skills first if needed:
  - `analyze_customer_feedback` → `reports/customer_feedback_summaries/`
  - `analyze_git_history` → `reports/git_history_analysis/`
  - `summarize_changelogs` → `reports/competitor_changelog_reports/`
  - VoTC insights are generated separately → `reports/votc_insights/`
  - `weekly_sentiment_analysis` → `reports/weekly_sentiment_analysis/`
- `NOTION_API_KEY` environment variable must be set (see `write_notion` skill for auth details)
- Slack webhook access for posting (see `post_to_slack` skill)

---
name: feature_research
description: Does research on competitive features and creates a report.
---

# Feature Research Skill

Use this skill to perform competitive feature analysis. You will research specific functionality across competitor products and compare them to [YOUR PRODUCT].

## Inputs

The user will provide:
1. **Message**: A description of what features or functionality to analyze
2. **URLs**: One or more competitor URLs to research (documentation, product pages, changelogs, etc.)

## Research Workflow

### Step 1: Analyze Competitor URLs
For each URL provided:
- Use web search and fetch_web_pages to gather information about the specified features
- Extract: feature capabilities, limitations, pricing implications, and user experience details
- Note the source URL for every claim

### Step 2: Research Your Product's Equivalent Functionality
- Search your product's documentation at `YOUR_PRODUCT_DOCS_URL` for equivalent or related features
- Look for: feature parity, unique differentiators, gaps, and areas where your product exceeds competitors
- Be thorough — check multiple relevant doc pages based on your product's structure

### Step 3: Compare (if multiple URLs provided)
- Identify common capabilities across competitors
- Note differentiating features unique to each product
- Highlight where your product leads, matches, or trails

## Output Format

Return your analysis in this structured format:

---BEGIN FORMAT---

Feature Analysis: [Topic from user's message]
Date: [Current date]

TL;DR: [1-2 sentence summary of key findings]

---

[COMPETITOR NAME] (source: [URL])
- [Feature 1]: [description, capabilities, limitations]
- [Feature 2]: [description, capabilities, limitations]
- [Notable absence]: [features they don't have that are relevant]

[COMPETITOR NAME 2] (source: [URL]) — if multiple URLs provided
- [Feature 1]: [description, capabilities, limitations]
- [Feature 2]: [description, capabilities, limitations]

---

[YOUR PRODUCT] (source: YOUR_PRODUCT_DOCS_URL)
- [Feature 1]: [description, capabilities, limitations]
- [Feature 2]: [description, capabilities, limitations]
- [Unique capabilities]: [things your product has that competitors don't]

---

COMPARISON SUMMARY
- [Feature] — Competitor 1: [status] | Competitor 2: [status] | [YOUR PRODUCT]: [status]
- [Feature] — Competitor 1: [status] | Competitor 2: [status] | [YOUR PRODUCT]: [status]

(Use ✅ has feature, ⚠️ partial/limited, ❌ missing, ❓ unclear)

---

KEY INSIGHTS
- [insight 1 — what this means for product decisions]
- [insight 2]
- [insight 3]

GAPS & OPPORTUNITIES
- [gap 1 — where your product could improve or differentiate]
- [gap 2]

RISKS
- [risk 1 — competitive threats or market shifts to watch]
- [risk 2]

---END FORMAT---

## Guidelines

- Be evidence-driven: cite the source (URL/section) for every important claim
- Separate facts from assumptions from opinions
- If information is unclear or unavailable, say so rather than guessing
- Focus on the specific features/functionality the user asked about
- Keep the analysis actionable and decision-ready

## After Completing Analysis

create a markdown file in reports/feature_research with your findings, and create a PR.

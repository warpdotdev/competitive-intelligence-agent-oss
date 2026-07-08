---
name: weekly-sentiment-summary
description: >
  Weekly sentiment summary of your product's social mentions with week-over-week
  comparison using Octolens. Produces a markdown report with sentiment
  score, highlights, lowlights, notable patterns, and competitor context.
  Use when the user asks for a weekly sentiment report, weekly social summary,
  or "how did mentions look this week".
---

# Weekly Sentiment Summary

Bigger-picture view for growth, product, and devex teams. Typically run Monday morning covering the prior week.

Uses the **Octolens** MCP server.

## Workflow

### Step 1: Determine date ranges

- **This week**: the most recent completed Mon–Sun (or the user-specified range)
- **Prior week**: the 7 days immediately before this week

### Step 2: Fetch mentions for both weeks

1. Call `list_mentions_context` to get available keyword IDs and filter syntax.
2. Identify your product's keywords (look for keywords matching your product name, domain, and any known brand handles).

> **Setup required:** Configure your product's keyword identifiers in Octolens before using this skill.
3. For each week, query `list_mentions` with those keyword IDs, `relevance=[0]`, and the week's date range. Set `endDate` to the day after Sunday to ensure full coverage.
4. Set `includeAll: false` and `limit: 100`.
5. Paginate with `cursor` until exhausted or 500 mentions per week.

### Step 3: Aggregate both weeks

For each week, count:
- `pos`, `neu`, `neg` by sentiment
- `total = pos + neu + neg`
- Tag distribution (bug_report, user_feedback, competitor_mention, buy_intent, product_question, etc.)

### Step 4: Compute sentiment scores

For each week:
```
sentiment_score = ((pos - neg) / total) * 100
```

Range: -100 to +100. Round to nearest integer.

Compute deltas:
- `Δ volume = this_week_total - prior_week_total`
- `Δ score = this_week_score - prior_week_score`

Use `+` prefix for positive deltas, `-` for negative. Show as absolute numbers, not percentages.

### Step 5: Identify patterns by sentiment (this week only)

Before analyzing, filter out:
- **Employee posts** (replies from your company's team members to users)
- **Spam / reseller posts** (e.g. discounted subscription sellers, engagement bait)
- **Cross-post duplicates** (same content on Twitter and Bluesky — count once, prefer higher-reach version)

For each sentiment category (Positive, Neutral, Negative), identify **3-5 key themes or patterns** from this week. Focus on:
- What are users saying? What themes emerge?
- Are there patterns across multiple mentions?
- What's strategically meaningful vs. noise?

Writing style: same as daily skill — lead with pattern/theme, include mention count, provide 1-2 representative links.

**For Positive section only**: After pattern summaries, include 1-3 direct quotes that work as testimonials. Pick the most specific, enthusiastic quotes that show clear value. Format as:
```
_"[exact quote]"_ — <url|@username or source>
```

### Step 6: Identify notable patterns

Compare this week vs prior week. Look for:
- **Recurring themes**: topics/features/complaints that appeared multiple times this week
- **Trending tags**: tags with significant volume changes vs prior week
- **New signals**: topics that appeared this week but not last week

Max 5 patterns. Each should include a delta or comparison when possible (e.g. "AI agent mentions up from 3 → 12 this week").

### Step 7: Product feedback patterns

Scan this week's mentions tagged `user_feedback`, `bug_report`, `product_question` for **recurring product feedback themes**. Focus on specific features, workflows, or pain points mentioned multiple times.

Look for:
- Feature requests that appeared multiple times
- Specific bugs or technical issues with volume
- Pricing/credit feedback patterns
- UI/UX feedback themes

Summarize in 2–4 bullets with mention counts. Example: "Feature requests for BYOK on free plan (5 mentions)" or "UI lag complaints when long threads open (3 mentions)".

### Step 8: Write markdown report and create PR

1. Format the report as a markdown file (~500 words max) using the template below.
2. Save it to `reports/weekly_sentiment_analysis/weekly_sentiment_report_<end_date>.md` where `<end_date>` is the Sunday of the covered week in `YYYY-MM-DD` format.
3. Create a new branch, commit the report, push, and open a PR.

Markdown template:

```markdown
# Weekly Sentiment Summary — <start_date> → <end_date>

**<total>** mentions (**<Δ>** vs last week) | 🟢 <pos> · ⚪ <neu> · 🔴 <neg> | Score: **<score>** (**<Δ>**)

## Positive
- <pattern summary with count> — [link](url), [link](url)
- <pattern summary with count> — [link](url)
...

### Testimonials
> "<exact quote>" — [@username](url)
> "<exact quote>" — [@username](url)

## Neutral
- <pattern summary with count> — [link](url), [link](url)
- <pattern summary with count> — [link](url)
...

## Negative
- <pattern summary with count> — [link](url), [link](url)
- <pattern summary with count> — [link](url)
...

## Notable Patterns
- <pattern with week-over-week Δ>
- <pattern with week-over-week Δ>
...

## Product Feedback Patterns
- <specific product feedback theme with count>
- <specific product feedback theme with count>
...
```

Omit any section that has no meaningful content.

## Edge Cases

- **Low volume week** (<50 mentions): Still produce the report but note the low volume. Reduce highlight/lowlight counts proportionally.
- **First run (no prior week data)**: Skip deltas and comparisons — just report this week's absolute numbers and note that week-over-week comparison will be available next week.
- **Non-English mentions**: Include if noteworthy, with language/region context in the takeaway.
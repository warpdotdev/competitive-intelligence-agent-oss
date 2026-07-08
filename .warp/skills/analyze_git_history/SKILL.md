---
name: analyze_git_history
description: Analyzes git history from a repository to summarize recent development activity, features in progress, and engineering priorities. Use when asked about what the team is working on, recent code changes, development velocity, or to prepare for planning/roadmap discussions.
---

# Git History Analysis Skill

Use this skill to analyze git commit history and provide product-relevant insights about development activity, feature progress, and team priorities.

## Inputs

The user may provide:
- **Repository path**: defaults to `/mnt/your-app-client` and `/mnt/your-app-server`. **Only analyze your application repositories — do NOT include this agent's own repo.**
- **Time period**: defaults to last 2 weeks (14 days)
- **Filters**: optional author, path, or branch filters

## Data Collection

Run these git commands from the repository root:

### 1. Commit History
```bash
git --no-pager log --since="2 weeks ago" --pretty=format:"%h|%an|%ad|%s" --date=short --stat
```

### 2. Author Summary
```bash
git --no-pager shortlog -sn --since="2 weeks ago"
```

### 3. Active Branches (feature work in progress)
```bash
git --no-pager branch -r --sort=-committerdate | head -20
```

### 4. Recent Merges to Main (completed features)
```bash
git --no-pager log --since="2 weeks ago" --merges --pretty=format:"%h|%an|%ad|%s" --date=short main
```

Adjust the `--since` flag based on the requested time period.

## Analysis Guidelines

When analyzing the collected data:

1. **Categorize commits** by conventional commit prefixes:
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `refactor:` - Code improvements
   - `docs:` - Documentation
   - `test:` - Testing
   - `chore:` - Maintenance

2. **Identify active areas** by grouping commits by directory/component

3. **Surface patterns**:
   - Which features are getting the most attention?
   - Are there areas with high bug fix activity (potential stability issues)?
   - What's the balance between new features vs. maintenance?

4. **Note in-progress work** from active branches not yet merged

## Output Format

Return your analysis in this structured format:

---BEGIN FORMAT---

Git History Analysis: [Repository Name]
Period: [Date range]
Generated: [Current date]

TL;DR: [2-3 sentence summary of key findings - what's being built, notable patterns]

---

ACTIVE FEATURES IN PROGRESS
- [Branch name]: [Description based on commits] — [Author(s)]
- [Branch name]: [Description based on commits] — [Author(s)]

RECENTLY COMPLETED (merged to main)
- [Feature/PR description] — [Date merged]
- [Feature/PR description] — [Date merged]

---

COMMIT BREAKDOWN BY TYPE
- Features: [count] ([percentage]%)
- Bug fixes: [count] ([percentage]%)
- Refactoring: [count] ([percentage]%)
- Other: [count] ([percentage]%)

MOST ACTIVE AREAS
- [Directory/component]: [commit count] commits — [brief description of changes]
- [Directory/component]: [commit count] commits — [brief description of changes]

TEAM ACTIVITY
- [Author]: [commit count] commits — [primary focus areas]
- [Author]: [commit count] commits — [primary focus areas]

---

KEY INSIGHTS
- [Insight about development priorities or patterns]
- [Insight about feature velocity or team focus]
- [Insight relevant to product planning]

RISKS & OBSERVATIONS
- [Any concerning patterns - high bug counts, stalled branches, etc.]
- [Areas that may need product attention]

QUESTIONS FOR FOLLOW-UP
- [Questions this analysis raises for product/engineering discussion]

---END FORMAT---

## Guidelines

- Be evidence-driven: cite specific commits, branches, or metrics
- Separate facts from interpretations
- Focus on product-relevant insights, not just raw statistics
- If the repository uses different commit conventions, adapt accordingly
- Note when data is incomplete or unclear

## After Completing Analysis

Save your report to `reports/git_history_analysis/` with filename `git_analysis_YYYY-MM-DD.md`, then create a PR.

Optionally, post a summary to Slack using the `post_to_slack` skill.

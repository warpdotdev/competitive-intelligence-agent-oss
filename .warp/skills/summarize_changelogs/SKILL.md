---
name: summarize_changelog
description: Does research on competitor's changelogs.
---

Use your web search tool to create a summary of recent changelogs entries from competitors over the last 2 weeks. If there are any important themes in common, point them out.

Specifically, check these links for each competitor:

https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
https://cursor.com/changelog
https://docs.factory.ai/changelog/cli-updates
https://ampcode.com/chronicle
https://github.com/sst/opencode/releases
https://developers.openai.com/codex/changelog/
https://www.conductor.build/blog
https://github.blog/changelog/?label=copilot&opened-months=2

YOU MUST INCLUDE YOUR PRODUCT'S CHANGELOG IN YOUR ANALYSIS
Review your product's changelog at `YOUR_PRODUCT_CHANGELOG_URL` and compare your recent changes in the same time periods to competitors. Keep in mind, you don't know what was shipped previously, so in your comparison, think about the things each of the teams have shipped in that period. USE THIS CHANGELOG AS THE SOURCE OF TRUTH FOR YOUR PRODUCT'S CHANGELOG, don't rely on other web searches.

> **Setup required:** Replace `YOUR_PRODUCT_CHANGELOG_URL` with your product's public changelog URL. If the page is behind a CDN cache, use `curl` with cache-busting headers to fetch fresh content:
> ```bash
> curl -sL -H "Cache-Control: no-cache" -H "Pragma: no-cache" "YOUR_PRODUCT_CHANGELOG_URL?_=$(date +%s)"
> ```

Finally, deduplicate information. Search for previous summaries you did in the folder reports/competitor_changelog_reports/, and don't repeat changelog entries that have been covered previously. However, you can reference these reports to influence your summary and analysis.

In your summary, note the dates each feature was shipped. (e.g. is it a monthly or weekly release)

The summary should follow this format:

---BEGIN FORMAT---

Competitive Changelog Analysis - Last 2 Weeks (Date range)
TL;DR: [Summary of changes]

[Competitor] (version number)
-[Date][Feature description]
-[Date][Feature description]
-[Date][Feature description]

COMMON THEMES
[common themes]

[YOUR PRODUCT] Comparison
Shipped:
Competitors:
Opportunity:

RISKS
- [risk1]
- [risk2]
- [risk3]

---END FORMAT---

And here is an example post (note: competitor entries are real; replace the [YOUR PRODUCT] section with your own changelog data):

---BEGIN EXAMPLE---

Competitive Changelog Analysis - Last 2 Weeks (Jan 13-27, 2026)
TL;DR: Major industry push toward agent skills/customization, multi-agent collaboration, and image generation. Enterprise features expanding across all tools.

CURSOR (v2.3-2.4)
- Subagents - parallel specialized agents with custom prompts/models
- Skills system (SKILL.md) for domain-specific workflows
- Image generation
- Cursor Blame - AI attribution per line of code (Enterprise)
- CLI: Plan mode, Ask mode, Cloud Handoff

CLAUDE CODE (v2.1.x)
- Setup hooks (--init, --maintenance flags)
- MCP tool auto-search enabled by default
- Automatic skill discovery from nested directories
- /config search, /stats date filtering
- Security fix for wildcard permission bypass

FACTORY (v0.42-0.52)
- /share command for session sharing
- /create-skill command with guided flow
- Multi-option spec mode
- Custom models from settings.json

AMP
- Painter tool (image generation)
- User-invokable Skills
- Efficient MCP tool loading (on-demand context)

OPENCODE (v1.1.32-34)
- Desktop app improvements
- GitLab Duo model support
- Multi-language support (Portuguese, Norwegian, Arabic)
- Workspace startup scripts

CODEX (v0.90-0.92)
- Multi-agent collaboration with explorer role
- Dynamic tools injection
- thread/unarchive for restoring sessions
- MCP OAuth scopes in config

CONDUCTOR (v0.28-0.29)
- Checks tab for pre-merge tracking
- Claude can comment on code changes
- .context directory for agent context sharing

COMMON THEMES
1. Skills Systems - Cursor, Claude Code, Factory all investing in customizable skills
2. Multi-Agent/Subagents - Cursor, Codex, Amp focusing on parallel agent execution
3. Image Generation - Cursor and Amp added generation capabilities
4. Session Management - Sharing, handoff, forking improvements across tools
5. MCP Improvements - OAuth, on-demand loading, easier configuration
6. Enterprise Focus - AI attribution, billing groups, service accounts

[YOUR PRODUCT] COMPARISON (Jan 7-21)
Shipped: [list features your product shipped in this period]
Competitors ahead on: [areas where competitors have shipped ahead of you]
Opportunity: [gaps you could close or areas to differentiate]

RISKS
- Cursor subagent architecture could become industry standard
- Skills becoming expected baseline feature
- Image generation becoming table stakes for coding assistants

---END EXAMPLE---

Make sure to return your entire summary in the proper format to the requester, don't truncate it.

When you are finished, create a PR with the new report in the folder reports/competitor_changelog_reports/
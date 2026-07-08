---
name: fix_p0_issues
description: Reads the most recent weekly product briefing, identifies P0 issues, researches them in the codebase, and spawns cloud coding agents to fix each one. Use when asked to "fix P0s", "address critical issues", or "work on top priorities from the briefing."
---

# Fix P0 Issues Skill

Use this skill to automatically address the highest-priority customer issues by spawning cloud coding agents for each P0 problem identified in the weekly product briefing.

## Workflow

### Step 1: Find the Latest Briefing

Resolve the repository root, then find the most recent briefing by sorting filenames (which contain `YYYY-MM-DD` dates). Do **not** use `ls -t` — filesystem modification times are unreliable in freshly cloned repos.

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
ls "$REPO_ROOT/reports/weekly_product_briefings/"*.md 2>/dev/null | sort | tail -1
```

### Step 2: Extract P0 Issues

Parse the briefing for sections starting with `#### P0:`. For each P0, extract:

- **Title**: The text after `#### P0:`
- **GitHub issue numbers**: Look for `#NNNN` patterns
- **Problem description**: The paragraph(s) following the title
- **Engineering alignment**: Notes about current engineering investment

Example P0 format in briefings:
```
#### P0: Model Selection / Routing Bugs (Trust Issue)
Multiple users report... Issues #8724 and #8720 describe...

**Engineering alignment:** No commits in the last 2 weeks address model routing.
```

### Step 3: Research Each P0

For each P0 issue identified:

1. **Fetch GitHub issue details** (if issue numbers are present):
   ```bash
   gh issue view <issue_number> --repo YOUR_ORG/YOUR_REPO
   ```

2. **Search the codebase** for relevant code using keywords from the issue:
   - Use grep or semantic search to find related files
   - Look for error messages, feature names, or component names mentioned in the issue
   - Identify the likely files/modules that need changes

3. **Document findings**:
   - List relevant file paths
   - Note any existing related code or tests
   - Identify dependencies or related systems

### Step 4: Triage and Confidence Assessment

After researching each P0, categorize it into one of the following types and determine whether to spawn an agent:

#### Category 1: Inactionable Complaint
**Criteria:** The user is complaining about something without:
- A specific description of the problem
- Reproduction steps
- Any indication of how to fix it

**Action:** Skip this issue. Do not spawn an agent. Note in your final report that this issue was skipped as inactionable.

#### Category 2: Bug Fix
**Criteria:**
- Clearly scoped problem
- Has reproduction steps or clear error description
- Narrow scope (affects specific feature/component)
- Root cause is identifiable or inferable from the issue

**Action:** Spawn a coding agent. These are ideal candidates for automated fixes.

#### Category 3: Feature Request
**Criteria:** The issue requests new functionality or significant changes to existing behavior.

**Action:** Assess confidence before deciding:

1. **Estimate scope**: Small (1-2 files), Medium (3-10 files), Large (10+ files or architectural changes)
2. **Assess complexity**: Is the implementation path clear? Are there existing patterns to follow?
3. **Confidence interval**: Rate 1-5 how likely a coding agent could successfully implement this:
   - **5 (High)**: Clear requirements, existing patterns, small scope → Spawn agent
   - **4 (Medium-High)**: Mostly clear, some ambiguity, medium scope → Spawn agent with caveats
   - **3 (Medium)**: Significant ambiguity or medium-large scope → Note in report, do not spawn
   - **1-2 (Low)**: Large scope, unclear requirements, or architectural → Skip, note in report

**Output format for each P0:**
```
P0: <Title>
- Category: <Bug Fix | Feature Request | Inactionable Complaint>
- Confidence: <1-5> (for Feature Requests)
- Scope: <Small | Medium | Large> (for Feature Requests)
- Decision: <Spawn Agent | Skip>
- Reasoning: <brief explanation>
```

### Step 5: Spawn Cloud Agents

**IMPORTANT:** You MUST use exactly `oz` to spawn cloud agents. The command must be exactly as shown below.

For each P0 that passed triage (Bug Fixes and high-confidence Feature Requests), spawn a cloud coding agent:

```bash
oz agent run-cloud \
  --environment YOUR_OZ_ENVIRONMENT_ID \
  --api-key $WARP_API_KEY \
  --prompt "<constructed prompt>"
```

**Do NOT substitute any other binary.** If `oz` is not available, stop and report the error rather than using an alternative.

**Prompt construction template:**
```
Fix GitHub issue #<NUMBER>: <TITLE>

## Problem
<Problem description from briefing>

## GitHub Issue Details
<Details fetched from gh issue view>

## Relevant Code
The following files are likely relevant:
- <file path 1>
- <file path 2>

## Task
1. Investigate the issue in the codebase
2. Implement a fix
3. Add or update tests as appropriate
4. Create a PR with a clear description of the changes

## Context
This is a P0 issue affecting users. Prioritize correctness and reliability.
```

### Step 6: Track and Report

After spawning agents, output a summary:

```
=== P0 Fix Agents Spawned ===

P0: <Title 1>
- GitHub Issues: #NNNN, #NNNN
- Run ID: <run-id-1>
- Monitor: oz run get <run-id-1>

P0: <Title 2>
- GitHub Issues: #NNNN
- Run ID: <run-id-2>
- Monitor: oz run get <run-id-2>

...

To check all runs:
oz run list --output-format text
```

## Agent Environment: Repository Details

The cloud agent environment has the primary application repositories pre-installed. Include the relevant context below in your prompts to subagents.

Key points:
- **your-app-client** (your primary client repo): `/home/user/your-app-client`
- **your-app-server** (your primary server/backend repo): `/home/user/your-app-server`

## Guidelines

- **Skip P0s already being addressed**: If the briefing notes an active branch exists, skip spawning an agent for that issue
- **Limit concurrent agents**: Don't spawn more than 3 agents at once to avoid resource contention
- **Include context**: The more context in the prompt, the better the agent can fix the issue
- **Prefer targeted fixes**: Each agent should focus on one P0 issue, not multiple

## Example Usage

When asked "fix the P0s" or "address critical issues from the briefing":

1. Read `reports/weekly_product_briefings/roadmap_customer_alignment_2026-02-21.md`
2. Find P0s: Login Timeout Errors (#101, #102), Data Export Failures (#103), Slow Dashboard Load (#104, etc.)
3. Skip macOS crash (active branch exists per briefing)
4. Research model routing and UI issues
5. Spawn agents for the actionable P0s
6. Report run IDs


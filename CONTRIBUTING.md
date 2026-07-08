# Contributing

Thank you for your interest in contributing to competitive-intelligence-agent!

## Getting started

1. Fork the repository and clone your fork
2. Follow the setup instructions in [README.md](README.md)
3. Create a branch: `git checkout -b your-feature-name`

## What to contribute

- New skills (add a folder under `.warp/skills/` with a `SKILL.md` and any supporting scripts)
- Improvements to existing skills (better prompts, more robust scripts)
- Bug fixes in the Python data-fetching scripts
- Documentation improvements

## Guidelines

**Security**
- Never commit credentials, tokens, or real API keys — use the env var names from `.env.example`
- Run `pip-audit -r requirements.txt` before submitting a PR with dependency changes
- For security vulnerabilities, see [SECURITY.md](SECURITY.md)

**Code style**
- Python: follow PEP 8; keep scripts self-contained where possible
- Shell: use `set -euo pipefail` at the top of standalone scripts
- Skill docs: follow the existing `SKILL.md` structure (frontmatter, When to Use, How to Use sections)

**Pull requests**
- Keep PRs focused — one skill or fix per PR
- Include a short description of what changed and why
- Reference any related issues

## Running the scripts locally

```bash
cp .env.example .env
# Fill in your credentials
pip install -r requirements.txt
python .warp/skills/analyze_customer_feedback/analyze_feedback.py --days 7
```

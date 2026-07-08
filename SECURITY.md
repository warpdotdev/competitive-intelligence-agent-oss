# Security Policy

## Supported Versions

This project is a reference implementation. Security fixes are applied to the
latest version on `main` only.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing **security@warp.dev** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce or proof-of-concept code
- Any suggested remediation

You should receive an acknowledgement within 48 hours. We aim to release a fix
within 14 days for critical issues and 90 days for lower-severity issues.

We will credit reporters in the fix commit unless you prefer to remain
anonymous.

## Scope

In scope:
- Credential exposure or leakage in source code or generated files
- Dependency vulnerabilities in `requirements.txt`
- Injection vulnerabilities (SQL, command, template) in any script
- SSRF or unvalidated external URL usage in agent scripts

Out of scope:
- Issues in external services this tool integrates with (Google, Slack, Notion, Grain)
- Social engineering attacks
- Denial of service against local scripts

## Security Best Practices for Users

- Never commit `.env`, `token.json`, or `credentials.json` — all are gitignored
- Rotate credentials immediately if you suspect they have been exposed
- Run `pip-audit -r requirements.txt` periodically to check for new CVEs
- The `generate_readonly_token.py` output contains live credentials — treat
  it with the same care as a password

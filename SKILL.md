---
name: github-management
description: Use when Codex needs to manage GitHub repositories with gh CLI or GitHub APIs, including issues, pull requests, review comments, GitHub Actions CI, releases, labels, milestones, branch protection, repository hygiene, security audit, dependency alerts, or repo governance tasks.
---

# Github Management

Use this skill for full-cycle GitHub repository management. Prefer `gh` CLI for authenticated operations and use GitHub REST or GraphQL only when `gh` does not expose the needed data cleanly.

## Core Rule

Collect facts first, summarize risk, then ask before any mutating action.

Mutating actions include pushing commits, merging PRs, closing issues, deleting branches or tags, creating releases, changing labels or milestones, editing branch protection, changing repository settings, modifying permissions, dismissing reviews, rerunning workflows, and applying generated fixes.

Run the pipeline exactly:

`Context -> Auth -> Read-only Inspect -> Risk Summary -> Confirmation -> Mutation -> Verification`

If context, authentication, target identifiers, or user intent are missing, stop and ask. Do not guess.

## Authentication Onboarding

When this skill is triggered, first decide whether GitHub authentication is already ready for the requested repo. If readiness is unknown or missing, tell the user how to configure GitHub access step by step before doing GitHub management work.

Do not skip this onboarding. Use `references/authentication.md` and present the user-facing steps there. Keep the guidance practical:

1. Ask the user to create a classic Personal Access Token with `repo` scope.
2. Tell them to save it locally under this skill's `config/` folder, never in chat.
3. Tell them to run `gh auth login --with-token < config/token` and `gh auth setup-git`.
4. Tell them to verify with `gh auth status`.
5. Continue only after authentication is confirmed or the task is explicitly read-only and does not require GitHub access.

## Workflow

1. Confirm repository context.
   - Identify the local repository path and remote with `git remote -v`.
   - Confirm the target owner/repo with `gh repo view --json nameWithOwner,url`.
   - If the task references a PR, issue, release, branch, label, or workflow, resolve its exact identifier before acting.
2. Verify authentication.
   - Read `references/authentication.md` and inspect `config/auth.example.json` for the expected local auth shape.
   - Run `gh auth status`.
   - If authentication or scope is missing, guide the user through `gh auth login --with-token < config/token`, `gh auth setup-git`, or the configured token environment.
   - Do not accept tokens pasted into chat. Do not log tokens. Do not commit `config/auth.local.json`, `config/token`, or secret config files.
3. Gather read-only state.
   - Use scripts in `scripts/` when they match the task.
   - Use `--json` output when the result will feed later reasoning.
4. Summarize findings.
   - Include target repo, object IDs, URLs, current state, risks, and recommended next actions.
   - Separate GitHub Actions from external CI providers; report external provider URLs without attempting provider-specific access.
5. Get explicit confirmation before mutation.
   - For high-risk operations, require the user to name the exact operation and target.
   - If a helper script supports dry-run mode, run dry-run first and show the planned command/effect.
6. Execute the confirmed action.
   - Use the smallest scoped `gh` command or API call.
   - Preserve user work and avoid unrelated repo changes.
7. Verify after action.
   - Re-run the relevant read-only inspection.
   - Report the evidence, not assumptions.

## Helper Scripts

Use these scripts from the repository being managed unless the user provides another path:

```bash
python "<skill-path>/scripts/inspect_pr.py" --repo "." --json
python "<skill-path>/scripts/inspect_ci.py" --repo "." --json
python "<skill-path>/scripts/inspect_pr_checks.py" --repo "." --json
python "<skill-path>/scripts/fetch_comments.py" --repo "." --json
python "<skill-path>/scripts/triage_issues.py" --repo "." --json
python "<skill-path>/scripts/repo_audit.py" --repo "." --json
```

All JSON output uses:

```json
{"ok": true, "source": "github-management", "items": [], "warnings": [], "next_actions": []}
```

## Task Guide

| Task | First inspection | Confirmation needed before |
| --- | --- | --- |
| Issue triage | `triage_issues.py` or `gh issue list --json ...` | labeling, assigning, closing, editing milestone |
| PR review | `inspect_pr.py` | pushing fixes, submitting reviews, merging |
| Review comments | `fetch_comments.py`; read `references/review-comments.md` | resolving conversations or pushing fixes |
| CI failure | `inspect_ci.py` or `inspect_pr_checks.py`; read `references/ci-diagnostics.md` | rerunning workflows or applying fixes |
| Release | `gh release list/view` | creating, editing, deleting, or publishing a release |
| Repo audit | `repo_audit.py` | changing settings, protections, permissions, secrets, Actions policy |
| Security review | Read the matching security best-practice reference listed below | filing issues, changing policy, applying fixes |
| Threat model | Read `references/security-threat-model-template.md` and `references/security-controls-and-assets.md` | writing files, filing issues, applying mitigations |
| Security ownership map | Run `scripts/security_ownership/run_ownership_map.py` and query with `scripts/security_ownership/query_ownership.py` | writing analysis outside the requested output directory |

## Security Reference Routing

For security best practices, identify the repo language and framework, then load every matching reference:

- Go backend: `references/security-best-practices-golang-general-backend-security.md`
- JavaScript Express backend: `references/security-best-practices-javascript-express-web-server-security.md`
- JavaScript frontend, no framework or unclear framework: `references/security-best-practices-javascript-general-web-frontend-security.md`
- jQuery frontend: `references/security-best-practices-javascript-jquery-web-frontend-security.md`
- TypeScript/Next.js backend or full-stack app: `references/security-best-practices-javascript-typescript-nextjs-web-server-security.md`
- TypeScript/React frontend: `references/security-best-practices-javascript-typescript-react-web-frontend-security.md`
- TypeScript/Vue frontend: `references/security-best-practices-javascript-typescript-vue-web-frontend-security.md`
- Python Django backend: `references/security-best-practices-python-django-web-server-security.md`
- Python FastAPI backend: `references/security-best-practices-python-fastapi-web-server-security.md`
- Python Flask backend: `references/security-best-practices-python-flask-web-server-security.md`

For threat modeling, stay repo-grounded: use evidence anchors, trust boundaries, assets, attacker capabilities, abuse paths, mitigations, and explicit assumptions from `references/security-threat-model-template.md`.

For security ownership map tasks, keep analysis read-only against git history. Write artifacts only to the user-specified output directory or a repo-local `ownership-map-out/`, then use `references/security-ownership-neo4j-import.md` only when graph import is requested.

## References

- Read `references/authentication.md` before configuring or troubleshooting GitHub authentication.
- Read `references/safety-policy.md` before any mutating GitHub action.
- Read `references/workflows.md` for task-specific GitHub workflows.
- Read `references/review-comments.md` for PR comment and review-thread handling.
- Read `references/ci-diagnostics.md` for failing check and log inspection.
- Read `references/development-practices.md` before code changes caused by GitHub management work.
- Read `references/source-attribution.md` when source provenance matters.

## Common Mistakes

- Do not infer authentication from local git access; always check `gh auth status`.
- Do not treat external CI as GitHub Actions; report the URL and ask for access or logs.
- Do not merge or close anything because tests pass; summarize and ask first.
- Do not modify repository settings from an audit command. Audits are read-only.
- Do not hide uncertainty. If GitHub returns partial data or permissions block a check, report the gap.

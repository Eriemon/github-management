# Github Management Workflows

Use these workflows after loading `SKILL.md`. Keep the first pass read-only.

## Issue Triage

1. Run `python "<skill-path>/scripts/triage_issues.py" --repo "." --json`.
2. Group issues by label, assignee, milestone, and age.
3. Identify missing labels, missing owners, duplicates, stale issues, and blocked issues.
4. Present a proposed triage table.
5. Confirm before labeling, assigning, closing, editing title/body, or changing milestone.

Useful `gh` fallback:

```bash
gh issue list --limit 100 --json number,title,state,url,labels,assignees,milestone,updatedAt,author
```

## Pull Requests

1. Run `python "<skill-path>/scripts/inspect_pr.py" --repo "." --json`.
2. Summarize state, draft status, mergeability, review decision, labels, assignees, and checks.
3. If review comments matter, read `references/review-comments.md` and run `python "<skill-path>/scripts/fetch_comments.py" --repo "." --json`.
4. Confirm before pushing fixes, submitting a review, resolving conversations, approving, requesting changes, or merging.

Useful `gh` fallback:

```bash
gh pr view --json number,url,title,state,isDraft,mergeStateStatus,reviewDecision,headRefName,baseRefName,author,labels,assignees
gh pr checks <pr> --json name,state,bucket,link,startedAt,completedAt,workflow
```

## CI Failures

1. Run `python "<skill-path>/scripts/inspect_ci.py" --repo "." --json`.
2. Read `references/ci-diagnostics.md` when logs, field fallback, or external CI boundaries matter.
3. For GitHub Actions failures, summarize the failing check, run URL, and log snippet.
4. For external CI, report the URL and ask for logs or provider access.
5. If code changes are needed, use TDD in the target repository and consult `references/development-practices.md`.
6. Confirm before rerunning workflows or pushing fixes.

Useful `gh` fallback:

```bash
gh run view <run-id> --json name,workflowName,conclusion,status,url,event,headBranch,headSha
gh run view <run-id> --log
```

## Releases

1. Inspect current releases and tags.
2. Compare the requested version against existing tags and release notes.
3. Confirm target tag, prerelease/draft status, generated notes behavior, and assets.
4. Create or edit the release only after explicit confirmation.
5. Verify with `gh release view <tag>`.

Useful read-only commands:

```bash
gh release list --limit 20
gh release view <tag> --json tagName,name,isDraft,isPrerelease,publishedAt,url
```

## Repository Audit

1. Run `python "<skill-path>/scripts/repo_audit.py" --repo "." --json`.
2. Summarize default branch, visibility, viewer permission, branch protection, Actions permissions, and vulnerability alerts status.
3. Identify gaps separately from recommended changes.
4. Confirm before editing protection rules, repository settings, collaborators, teams, or Actions policy.

Useful read-only commands:

```bash
gh repo view --json nameWithOwner,url,defaultBranchRef,isPrivate,visibility,viewerPermission
gh api repos/{owner}/{repo}/branches/<branch>/protection
gh api repos/{owner}/{repo}/actions/permissions
gh api repos/{owner}/{repo}/vulnerability-alerts
```

## Security Review

1. Determine the language, framework, and security surface in the target repo.
2. Load only the relevant `references/security-best-practices-*.md` files listed in `SKILL.md`.
3. Produce findings with severity, file/line references when local code is available, and concrete remediation.
4. Confirm before filing issues, changing code, changing policy, or altering repository settings.

## Threat Modeling

1. Read `references/security-threat-model-template.md` and `references/security-controls-and-assets.md`.
2. Build a repo-grounded system model with evidence anchors, trust boundaries, assets, entry points, attacker capabilities, abuse paths, and mitigations.
3. Ask targeted questions when deployment model, internet exposure, data sensitivity, or auth expectations materially affect severity.
4. Write a threat model only after the user confirms the output location or accepts a repo-local filename.

## Security Ownership Map

1. Run `python "<skill-path>/scripts/security_ownership/run_ownership_map.py" --repo "." --out ownership-map-out`.
2. Query bounded slices with `python "<skill-path>/scripts/security_ownership/query_ownership.py" --data-dir ownership-map-out summary --section orphaned_sensitive_code`.
3. Treat the analysis as read-only against git history; output artifacts must stay in the requested output directory.
4. Read `references/security-ownership-neo4j-import.md` only when graph database import is requested.

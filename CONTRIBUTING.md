# Contributing

Thanks for improving `github-management`.

## Development Rules

- Keep `SKILL.md` concise and focused on behavior an agent must follow.
- Put detailed workflows in `references/` and deterministic helpers in `scripts/`.
- Preserve the safety pipeline: context, auth, read-only inspection, risk summary, confirmation, mutation, verification.
- Never commit local credentials, tokens, logs, or private GitHub data.

## Local Checks

Run lightweight checks before opening a pull request:

```powershell
python .\scripts\inspect_pr.py --help
python .\scripts\repo_audit.py --help
python .\scripts\triage_issues.py --help
```

Then review:

```powershell
git status --short
git diff --cached --stat
```

Confirm no private files under `config/` are staged.

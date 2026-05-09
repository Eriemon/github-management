# CI Diagnostics

Use this reference when a PR has failing checks or the user asks to debug CI.

## Inspection

1. Run `python "<skill-path>/scripts/inspect_ci.py" --repo "." --json`.
2. Use `python "<skill-path>/scripts/inspect_pr_checks.py" --repo "." --json` when compatibility with the original PR-check helper is useful.
3. For GitHub Actions, collect the check name, run URL, run id, state, and failure snippet.
4. If `gh pr checks` rejects fields, retry with available fields before giving up.
5. If logs are pending, say so and avoid guessing.

## External CI

Treat Buildkite and other external providers as out of scope unless the user supplies logs or credentials. Report the details URL only.

## Fix Flow

Summarize the failure, propose the smallest fix plan, ask for confirmation before pushing or rerunning workflows, then re-run inspection after the confirmed action.

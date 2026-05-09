# Safety Policy

Use this reference before any GitHub operation that can alter repository state.

## Confirmation Levels

| Level | Actions | Required behavior |
| --- | --- | --- |
| Read-only | view issues, inspect PRs, fetch checks, read settings, list releases | Run directly after confirming repo context and auth. |
| Low-risk mutation | add a non-sensitive comment, assign self, add informational label | Summarize target and planned command, then ask for confirmation. |
| High-risk mutation | merge PR, push commits, close issue, delete branch/tag, publish release, change branch protection, change repository settings, alter permissions, dismiss review, rerun deployment workflow | Require explicit confirmation naming the exact operation and target. Run dry-run or show command first when possible. |

## Required Mutation Gate

Before any mutation:

1. State the repository `owner/name`.
2. State the exact target: PR number, issue number, branch, tag, release, label, workflow, or setting.
3. State the current observed state.
4. State the planned command or API endpoint.
5. State the risk and rollback path if one exists.
6. Ask the user for explicit confirmation.

If any field is unknown, do not mutate.

## Never Do Automatically

- Merge a PR because checks are green.
- Close an issue because it appears stale.
- Delete a branch or tag without naming it.
- Change branch protection, Actions policy, secrets, collaborators, teams, or permissions without an exact request.
- Publish, edit, or delete a release without confirming version/tag and release notes.
- Resolve review conversations unless the requested comments were addressed.
- Rerun workflows that deploy, publish, charge money, or contact customers without confirmation.

## Dry-Run Defaults

Helper scripts and generated commands must default to dry-run for mutating operations. A non-dry-run mutation requires both:

- `confirmed=True` or an equivalent explicit confirmation in the calling flow.
- A target-specific command rather than a broad wildcard command.

## Reporting Permission Gaps

If `gh` cannot read a protected resource:

- Report the exact command or endpoint that failed.
- Include the permission or scope likely missing when known.
- Ask for logs, credentials, or scope changes instead of guessing.

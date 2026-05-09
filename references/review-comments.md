# Review Comments

Use this reference when a task involves PR conversation comments, review submissions, or inline review threads.

## Read-Only Inspection

1. Verify `gh auth status`.
2. Run `python "<skill-path>/scripts/fetch_comments.py" --repo "." --json`.
3. If the user supplied a PR, pass `--pr <number-or-url>`.
4. Number each unresolved thread and notable top-level comment.
5. Summarize the requested change, file path, line, author, resolved state, and risk.

## User Confirmation

Ask which numbered comments should be addressed. Do not push fixes, resolve conversations, submit reviews, approve, request changes, or dismiss reviews without explicit confirmation.

## After Fixes

Re-run `scripts/fetch_comments.py` and the relevant tests. Report remaining unresolved threads separately from comments that appear addressed by code changes.

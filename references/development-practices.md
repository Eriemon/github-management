# Development Practices

Use these practices when GitHub management work requires code changes in a target repository.

## TDD

For bug fixes or behavior changes, write or identify a failing test first, watch it fail for the expected reason, implement the smallest fix, then rerun the focused test and relevant broader checks.

## Systematic Debugging

When a failure is unclear, collect evidence before changing code. Reproduce the issue, isolate the failing layer, form one hypothesis at a time, and validate it with a targeted command or test.

## Review Handling

Address review comments by numbered item. If a comment is ambiguous or technically risky, ask a targeted question before changing code. Do not silently broaden scope.

## Verification Before Completion

Before claiming success, run the exact validation commands relevant to the task and report the evidence. If a check cannot run, report why and what risk remains.

## Git Worktrees

Use a separate worktree only when the user asks for isolated concurrent work or when existing local changes would otherwise be at risk. Never overwrite user changes.

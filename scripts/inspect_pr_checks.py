from typing import Optional

import gh_common
import inspect_ci


def inspect_pr_checks(
    repo: str,
    pr: Optional[str] = None,
    runner: gh_common.Runner = gh_common.run_gh,
    max_lines: int = inspect_ci.DEFAULT_MAX_LINES,
    context: int = inspect_ci.DEFAULT_CONTEXT_LINES,
) -> dict:
    return inspect_ci.inspect_ci(repo, pr=pr, runner=runner, max_lines=max_lines, context=context)


def main() -> None:
    parser = gh_common.base_parser("Compatibility entrypoint for inspecting failing PR checks.")
    parser.add_argument("--pr", help="PR number or URL. Defaults to the current branch PR.")
    parser.add_argument("--max-lines", type=int, default=inspect_ci.DEFAULT_MAX_LINES, help="Maximum log snippet lines.")
    parser.add_argument("--context", type=int, default=inspect_ci.DEFAULT_CONTEXT_LINES, help="Context lines around failure markers.")
    args = parser.parse_args()
    gh_common.print_payload(
        inspect_pr_checks(args.repo, pr=args.pr, max_lines=args.max_lines, context=args.context),
        args.as_json,
    )


if __name__ == "__main__":
    main()

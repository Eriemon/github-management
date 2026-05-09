from typing import Any, Dict, List, Optional

import gh_common


ISSUE_FIELDS = "number,title,state,url,labels,assignees,milestone,updatedAt,author"


def triage_issues(
    repo: str,
    labels: Optional[List[str]] = None,
    runner: gh_common.Runner = gh_common.run_gh,
) -> Dict[str, Any]:
    auth_error = gh_common.require_auth(repo, runner)
    if auth_error:
        return auth_error

    args = ["issue", "list", "--limit", "100", "--json", ISSUE_FIELDS]
    for label in labels or []:
        args.extend(["--label", label])
    issues = runner(repo, args)
    if issues.returncode != 0:
        return gh_common.envelope(ok=False, warnings=[(issues.stderr or issues.stdout).strip()], next_actions=["Check issue permissions and retry."])

    raw_items = gh_common.parse_json_output(issues.stdout, [])
    items: List[Dict[str, Any]] = []
    for issue in raw_items:
        milestone = issue.get("milestone") or {}
        items.append(
            {
                "type": "issue",
                "number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "url": issue.get("url"),
                "labels": gh_common.normalize_labels(issue.get("labels", [])),
                "assignees": gh_common.normalize_people(issue.get("assignees", [])),
                "milestone": milestone.get("title"),
                "updated_at": issue.get("updatedAt"),
            }
        )
    return gh_common.envelope(
        ok=True,
        items=items,
        next_actions=["Review stale open issues", "Confirm before labeling, assigning, closing, or changing milestones."],
    )


def main() -> None:
    parser = gh_common.base_parser("Triage GitHub issues.")
    parser.add_argument("--labels", nargs="*", default=[], help="Labels to filter by.")
    args = parser.parse_args()
    gh_common.print_payload(triage_issues(args.repo, labels=args.labels), args.as_json)


if __name__ == "__main__":
    main()

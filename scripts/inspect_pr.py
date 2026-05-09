from typing import Any, Dict, List, Optional

import gh_common


PR_FIELDS = "number,url,title,state,isDraft,mergeStateStatus,reviewDecision,headRefName,baseRefName,author,labels,assignees"
CHECK_FIELDS = "name,state,bucket,link,startedAt,completedAt,workflow"
CHECK_FIELDS_FALLBACK = "name,state,bucket,link"


def _view_pr(repo: str, pr: Optional[str], runner: gh_common.Runner) -> Dict[str, Any]:
    if pr:
        args = ["pr", "view", str(pr), "--json", PR_FIELDS]
    else:
        args = ["pr", "view", "--json", PR_FIELDS]
    view = runner(repo, args)
    if view.returncode != 0:
        raise RuntimeError((view.stderr or view.stdout or "Unable to resolve pull request").strip())
    return gh_common.parse_json_output(view.stdout, {})


def _checks(repo: str, pr_id: str, runner: gh_common.Runner) -> List[Dict[str, Any]]:
    checks = runner(repo, ["pr", "checks", pr_id, "--json", CHECK_FIELDS])
    if checks.returncode != 0:
        checks = runner(repo, ["pr", "checks", pr_id, "--json", CHECK_FIELDS_FALLBACK])
    if checks.returncode != 0:
        return []
    return gh_common.parse_json_output(checks.stdout, [])


def inspect_pr(repo: str, pr: Optional[str] = None, runner: gh_common.Runner = gh_common.run_gh) -> Dict[str, Any]:
    auth_error = gh_common.require_auth(repo, runner)
    if auth_error:
        return auth_error

    try:
        pr_payload = _view_pr(repo, pr, runner)
    except RuntimeError as exc:
        return gh_common.envelope(ok=False, warnings=[str(exc)], next_actions=["Provide a PR number or check the current branch PR."])

    pr_id = gh_common.pr_identifier(pr, pr_payload)
    checks = _checks(repo, pr_id, runner) if pr_id else []
    item = {
        "type": "pull-request",
        "number": pr_payload.get("number"),
        "url": pr_payload.get("url"),
        "title": pr_payload.get("title"),
        "state": pr_payload.get("state"),
        "is_draft": pr_payload.get("isDraft"),
        "merge_state": pr_payload.get("mergeStateStatus"),
        "review_decision": pr_payload.get("reviewDecision"),
        "head": pr_payload.get("headRefName"),
        "base": pr_payload.get("baseRefName"),
        "labels": gh_common.normalize_labels(pr_payload.get("labels", [])),
        "assignees": gh_common.normalize_people(pr_payload.get("assignees", [])),
        "checks": checks,
    }
    warnings = []
    if any((check.get("bucket") or check.get("state") or "").lower() in {"fail", "failing", "failure"} for check in checks):
        warnings.append("One or more PR checks are failing.")
    return gh_common.envelope(ok=True, items=[item], warnings=warnings, next_actions=["Review comments and failing checks before any mutation."])


def main() -> None:
    parser = gh_common.base_parser("Inspect a GitHub pull request.")
    parser.add_argument("--pr", help="PR number or URL. Defaults to the current branch PR.")
    args = parser.parse_args()
    gh_common.print_payload(inspect_pr(args.repo, pr=args.pr), args.as_json)


if __name__ == "__main__":
    main()

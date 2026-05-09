from typing import Any, Dict, List, Optional

import gh_common


CHECK_FIELDS = "name,state,bucket,link,startedAt,completedAt,workflow"
CHECK_FIELDS_FALLBACK = "name,state,bucket,link"
DEFAULT_MAX_LINES = 160
DEFAULT_CONTEXT_LINES = 30
PENDING_LOG_MARKERS = ("still in progress", "log will be available when it is complete")
FAILURE_VALUES = {"fail", "failing", "failure", "failed", "error", "cancelled", "timed_out", "action_required"}


def _resolve_pr(repo: str, pr: Optional[str], runner: gh_common.Runner) -> Dict[str, Any]:
    if pr:
        view = runner(repo, ["pr", "view", str(pr), "--json", "number,url"])
    else:
        view = runner(repo, ["pr", "view", "--json", "number,url"])
    if view.returncode != 0:
        raise RuntimeError((view.stderr or view.stdout or "Unable to resolve pull request").strip())
    return gh_common.parse_json_output(view.stdout, {})


def _failed(check: Dict[str, Any]) -> bool:
    statuses = [check.get("bucket"), check.get("state"), check.get("conclusion"), check.get("status")]
    return any(str(status or "").strip().lower() in FAILURE_VALUES for status in statuses)


def _check_url(check: Dict[str, Any]) -> str:
    return check.get("link") or check.get("detailsUrl") or check.get("url") or ""


def _is_pending_log(message: str) -> bool:
    lowered = (message or "").lower()
    return any(marker in lowered for marker in PENDING_LOG_MARKERS)


def _repo_slug(repo: str, runner: gh_common.Runner) -> Optional[str]:
    result = runner(repo, ["repo", "view", "--json", "nameWithOwner"])
    if result.returncode != 0:
        return None
    payload = gh_common.parse_json_output(result.stdout, {})
    return payload.get("nameWithOwner")


def _job_log(repo: str, job_id: str, runner: gh_common.Runner) -> str:
    slug = _repo_slug(repo, runner)
    if not slug:
        return ""
    result = runner(repo, ["api", f"/repos/{slug}/actions/jobs/{job_id}/logs"])
    return result.stdout if result.returncode == 0 else ""


def _check_log(repo: str, run_id: str, job_id: Optional[str], runner: gh_common.Runner) -> str:
    log_result = runner(repo, ["run", "view", run_id, "--log"])
    if log_result.returncode == 0:
        return log_result.stdout
    message = log_result.stderr or log_result.stdout
    if job_id and _is_pending_log(message):
        return _job_log(repo, job_id, runner)
    return message


def inspect_ci(
    repo: str,
    pr: Optional[str] = None,
    runner: gh_common.Runner = gh_common.run_gh,
    max_lines: int = DEFAULT_MAX_LINES,
    context: int = DEFAULT_CONTEXT_LINES,
) -> Dict[str, Any]:
    auth_error = gh_common.require_auth(repo, runner)
    if auth_error:
        return auth_error

    try:
        pr_payload = _resolve_pr(repo, pr, runner)
    except RuntimeError as exc:
        return gh_common.envelope(ok=False, warnings=[str(exc)], next_actions=["Provide a PR number or URL to inspect CI."])

    pr_id = gh_common.pr_identifier(pr, pr_payload)
    checks_result = runner(repo, ["pr", "checks", pr_id, "--json", CHECK_FIELDS])
    if checks_result.returncode != 0:
        checks_result = runner(repo, ["pr", "checks", pr_id, "--json", CHECK_FIELDS_FALLBACK])
    if checks_result.returncode != 0:
        return gh_common.envelope(ok=False, warnings=[(checks_result.stderr or checks_result.stdout).strip()], next_actions=["Check PR permissions and retry."])

    checks = gh_common.parse_json_output(checks_result.stdout, [])
    items: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for check in checks:
        if not _failed(check):
            continue
        url = _check_url(check)
        run_id = gh_common.extract_actions_run_id(url)
        job_id = gh_common.extract_actions_job_id(url)
        if run_id:
            log_text = _check_log(repo, run_id, job_id, runner)
            snippet = gh_common.failure_snippet(log_text, context=context, max_lines=max_lines)
            items.append(
                {
                    "type": "ci-check",
                    "provider": "github-actions",
                    "name": check.get("name"),
                    "state": check.get("state"),
                    "bucket": check.get("bucket"),
                    "url": url,
                    "run_id": run_id,
                    "job_id": job_id,
                    "snippet": snippet,
                }
            )
        else:
            warnings.append(f"{check.get('name', 'unknown')} is external CI; report the URL and do not fetch provider logs.")
            items.append(
                {
                    "type": "ci-check",
                    "provider": "external",
                    "name": check.get("name"),
                    "state": check.get("state"),
                    "bucket": check.get("bucket"),
                    "url": url,
                }
            )

    ok = len(items) == 0
    next_actions = ["Fix GitHub Actions failures or request external CI logs before changing code."] if items else ["No failing CI checks found."]
    return gh_common.envelope(ok=ok, items=items, warnings=warnings, next_actions=next_actions)


def main() -> None:
    parser = gh_common.base_parser("Inspect failing GitHub PR checks.")
    parser.add_argument("--pr", help="PR number or URL. Defaults to the current branch PR.")
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES, help="Maximum log snippet lines.")
    parser.add_argument("--context", type=int, default=DEFAULT_CONTEXT_LINES, help="Context lines around failure markers.")
    args = parser.parse_args()
    gh_common.print_payload(inspect_ci(args.repo, pr=args.pr, max_lines=args.max_lines, context=args.context), args.as_json)


if __name__ == "__main__":
    main()

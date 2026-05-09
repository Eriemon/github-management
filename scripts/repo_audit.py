from typing import Any, Dict

import gh_common


REPO_FIELDS = "nameWithOwner,url,defaultBranchRef,isPrivate,visibility,viewerPermission"


def _api_json(repo: str, path: str, runner: gh_common.Runner, fallback: Any) -> Any:
    response = runner(repo, ["api", path])
    if response.returncode != 0:
        return fallback
    return gh_common.parse_json_output(response.stdout, fallback)


def audit_repo(repo: str, runner: gh_common.Runner = gh_common.run_gh) -> Dict[str, Any]:
    auth_error = gh_common.require_auth(repo, runner)
    if auth_error:
        return auth_error

    view = runner(repo, ["repo", "view", "--json", REPO_FIELDS])
    if view.returncode != 0:
        return gh_common.envelope(ok=False, warnings=[(view.stderr or view.stdout).strip()], next_actions=["Check repository access and retry."])
    repo_payload = gh_common.parse_json_output(view.stdout, {})
    default_branch = (repo_payload.get("defaultBranchRef") or {}).get("name")

    protection: Dict[str, Any] = {}
    if default_branch:
        protection = _api_json(repo, f"repos/{{owner}}/{{repo}}/branches/{default_branch}/protection", runner, {})
    actions_permissions = _api_json(repo, "repos/{owner}/{repo}/actions/permissions", runner, {})
    vulnerability_result = runner(repo, ["api", "repos/{owner}/{repo}/vulnerability-alerts"])
    vulnerability_alerts = vulnerability_result.returncode == 0

    item = {
        "type": "repo-audit",
        "name_with_owner": repo_payload.get("nameWithOwner"),
        "url": repo_payload.get("url"),
        "default_branch": default_branch,
        "is_private": repo_payload.get("isPrivate"),
        "visibility": repo_payload.get("visibility"),
        "viewer_permission": repo_payload.get("viewerPermission"),
        "branch_protection": protection,
        "actions_permissions": actions_permissions,
        "vulnerability_alerts_enabled": vulnerability_alerts,
    }

    warnings = []
    if not protection:
        warnings.append("Default branch protection was not available or is not configured.")
    if not vulnerability_alerts:
        warnings.append("Dependabot vulnerability alerts could not be confirmed.")
    return gh_common.envelope(
        ok=True,
        items=[item],
        warnings=warnings,
        next_actions=["Review audit findings; confirm explicitly before changing repository settings."],
    )


def main() -> None:
    parser = gh_common.base_parser("Audit read-only GitHub repository settings.")
    args = parser.parse_args()
    gh_common.print_payload(audit_repo(args.repo), args.as_json)


if __name__ == "__main__":
    main()

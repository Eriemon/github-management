from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import gh_common


QUERY = """
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $commentsCursor: String,
  $reviewsCursor: String,
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      title
      state
      comments(first: 100, after: $commentsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { id body createdAt updatedAt author { login } }
      }
      reviews(first: 100, after: $reviewsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { id state body submittedAt author { login } }
      }
      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          diffSide
          startLine
          startDiffSide
          originalLine
          originalStartLine
          resolvedBy { login }
          comments(first: 100) {
            nodes { id body createdAt updatedAt author { login } }
          }
        }
      }
    }
  }
}
"""


PR_FIELDS = "number,url,title,state,headRepositoryOwner,headRepository"


def _resolve_pr(repo: str, pr: Optional[str], runner: gh_common.Runner) -> Dict[str, Any]:
    if pr:
        view = runner(repo, ["pr", "view", str(pr), "--json", PR_FIELDS])
    else:
        view = runner(repo, ["pr", "view", "--json", PR_FIELDS])
    if view.returncode != 0:
        raise RuntimeError((view.stderr or view.stdout or "Unable to resolve pull request").strip())
    return gh_common.parse_json_output(view.stdout, {})


def _owner_repo(pr_payload: Dict[str, Any]) -> tuple[str, str]:
    owner, repo = _owner_repo_from_url(str(pr_payload.get("url") or ""))
    if owner and repo:
        return owner, repo

    owner = ((pr_payload.get("headRepositoryOwner") or {}).get("login") or "").strip()
    repo = ((pr_payload.get("headRepository") or {}).get("name") or "").strip()
    if not owner or not repo:
        raise RuntimeError("Unable to resolve PR repository owner/name from URL or head repository.")
    return owner, repo


def _owner_repo_from_url(url: str) -> tuple[str, str]:
    path_parts = [part for part in urlparse(url).path.split("/") if part]
    if len(path_parts) >= 4 and path_parts[2] == "pull":
        return path_parts[0], path_parts[1]
    return "", ""


def _page_info(connection: Dict[str, Any]) -> Dict[str, Any]:
    return connection.get("pageInfo") or {}


def _graphql_page(
    repo: str,
    owner: str,
    name: str,
    number: int,
    comments_cursor: Optional[str],
    reviews_cursor: Optional[str],
    threads_cursor: Optional[str],
    runner: gh_common.Runner,
) -> Dict[str, Any]:
    args = [
        "api",
        "graphql",
        "-f",
        f"query={QUERY}",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={name}",
        "-F",
        f"number={number}",
    ]
    if comments_cursor:
        args.extend(["-F", f"commentsCursor={comments_cursor}"])
    if reviews_cursor:
        args.extend(["-F", f"reviewsCursor={reviews_cursor}"])
    if threads_cursor:
        args.extend(["-F", f"threadsCursor={threads_cursor}"])

    result = runner(repo, args)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "Unable to fetch PR comments").strip())
    payload = gh_common.parse_json_output(result.stdout, {})
    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL errors: {payload['errors']}")
    return payload


def fetch_comments(
    repo: str,
    pr: Optional[str] = None,
    runner: gh_common.Runner = gh_common.run_gh,
) -> Dict[str, Any]:
    auth_error = gh_common.require_auth(repo, runner)
    if auth_error:
        return auth_error

    try:
        pr_payload = _resolve_pr(repo, pr, runner)
        owner, name = _owner_repo(pr_payload)
        number = int(pr_payload["number"])
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        return gh_common.envelope(ok=False, warnings=[str(exc)], next_actions=["Provide a PR number or URL to inspect comments."])

    conversation_comments: List[Dict[str, Any]] = []
    reviews: List[Dict[str, Any]] = []
    review_threads: List[Dict[str, Any]] = []
    comments_cursor = reviews_cursor = threads_cursor = None
    pr_meta: Optional[Dict[str, Any]] = None

    try:
        while True:
            payload = _graphql_page(repo, owner, name, number, comments_cursor, reviews_cursor, threads_cursor, runner)
            pull_request = payload["data"]["repository"]["pullRequest"]
            if pr_meta is None:
                pr_meta = {
                    "number": pull_request.get("number"),
                    "url": pull_request.get("url"),
                    "title": pull_request.get("title"),
                    "state": pull_request.get("state"),
                    "owner": owner,
                    "repo": name,
                }

            comments = pull_request.get("comments") or {}
            review_data = pull_request.get("reviews") or {}
            threads = pull_request.get("reviewThreads") or {}
            conversation_comments.extend(comments.get("nodes") or [])
            reviews.extend(review_data.get("nodes") or [])
            review_threads.extend(threads.get("nodes") or [])

            comments_info = _page_info(comments)
            reviews_info = _page_info(review_data)
            threads_info = _page_info(threads)
            comments_cursor = comments_info.get("endCursor") if comments_info.get("hasNextPage") else None
            reviews_cursor = reviews_info.get("endCursor") if reviews_info.get("hasNextPage") else None
            threads_cursor = threads_info.get("endCursor") if threads_info.get("hasNextPage") else None
            if not (comments_cursor or reviews_cursor or threads_cursor):
                break
    except (KeyError, TypeError, RuntimeError) as exc:
        return gh_common.envelope(ok=False, warnings=[str(exc)], next_actions=["Check PR permissions and retry comment inspection."])

    item = {
        "type": "pr-comments",
        "pull_request": pr_meta or pr_payload,
        "summary": {
            "conversation_comments": len(conversation_comments),
            "reviews": len(reviews),
            "review_threads": len(review_threads),
            "unresolved_threads": sum(1 for thread in review_threads if not thread.get("isResolved")),
        },
        "conversation_comments": conversation_comments,
        "reviews": reviews,
        "review_threads": review_threads,
    }
    return gh_common.envelope(ok=True, items=[item], next_actions=["Number the comments, summarize required fixes, and ask which ones to address."])


def main() -> None:
    parser = gh_common.base_parser("Fetch PR comments, reviews, and review threads.")
    parser.add_argument("--pr", help="PR number or URL. Defaults to the current branch PR.")
    args = parser.parse_args()
    gh_common.print_payload(fetch_comments(args.repo, pr=args.pr), args.as_json)


if __name__ == "__main__":
    main()

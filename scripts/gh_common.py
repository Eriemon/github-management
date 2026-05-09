import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


SOURCE = "github-management"
Runner = Callable[[str, List[str]], Any]
SKILL_ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATTERN = re.compile(r"(ghp_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]+)")


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return TOKEN_PATTERN.sub("<redacted-token>", value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def envelope(
    ok: bool = True,
    items: Optional[List[Dict[str, Any]]] = None,
    warnings: Optional[List[str]] = None,
    next_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return redact({
        "ok": ok,
        "source": SOURCE,
        "items": items or [],
        "warnings": warnings or [],
        "next_actions": next_actions or [],
    })


def load_auth_config(skill_root: Optional[Path] = None) -> Dict[str, Any]:
    skill_root = skill_root or SKILL_ROOT
    config_dir = skill_root / "config"
    example_path = config_dir / "auth.example.json"
    local_path = config_dir / "auth.local.json"
    path = local_path if local_path.exists() else example_path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def configured_token_available(auth_config: Optional[Dict[str, Any]] = None, skill_root: Optional[Path] = None) -> bool:
    skill_root = skill_root or SKILL_ROOT
    config = auth_config if auth_config is not None else load_auth_config(skill_root)
    token_env = config.get("token_env")
    if token_env and os.environ.get(token_env):
        return True
    token_file = config.get("token_file")
    if token_file:
        token_path = Path(token_file)
        if not token_path.is_absolute():
            token_path = skill_root / token_path
        return token_path.exists() and bool(token_path.read_text(encoding="utf-8").strip())
    return False


def run_gh(repo: str, args: List[str]) -> subprocess.CompletedProcess:
    repo_path = str(Path(repo).resolve())
    try:
        return subprocess.run(
            ["gh", *args],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            ["gh", *args],
            127,
            stdout="",
            stderr="gh is not installed or not on PATH.",
        )


def parse_json_output(output: str, fallback: Any) -> Any:
    text = (output or "").strip()
    if not text:
        return fallback
    return json.loads(text)


def require_auth(repo: str, runner: Runner = run_gh) -> Optional[Dict[str, Any]]:
    auth = runner(repo, ["auth", "status"])
    if getattr(auth, "returncode", 1) != 0:
        detail = (getattr(auth, "stderr", "") or getattr(auth, "stdout", "") or "gh is not authenticated").strip()
        config = load_auth_config()
        token_hint = "A configured token file/env was found; run `gh auth login --with-token < config/token` and `gh auth setup-git`." if configured_token_available(config) else "Create a token using `references/authentication.md`, save it under `config/`, then run `gh auth login --with-token < config/token`."
        return envelope(
            ok=False,
            warnings=[detail],
            next_actions=[f"{token_hint} See `references/authentication.md`."],
        )
    return None


def pr_identifier(pr: Optional[str], pr_payload: Dict[str, Any]) -> str:
    if pr:
        return str(pr)
    number = pr_payload.get("number")
    return str(number) if number is not None else ""


def extract_actions_run_id(url: str) -> Optional[str]:
    match = re.search(r"/actions/runs/(\d+)", url or "")
    return match.group(1) if match else None


def extract_actions_job_id(url: str) -> Optional[str]:
    match = re.search(r"/actions/runs/\d+/job/(\d+)", url or "")
    if match:
        return match.group(1)
    match = re.search(r"/job/(\d+)", url or "")
    return match.group(1) if match else None


def failure_snippet(log: str, context: int = 1, max_lines: int = 20) -> str:
    lines = (log or "").splitlines()
    if not lines:
        return ""
    patterns = ("fail", "failed", "failure", "error", "exception", "traceback")
    for index, line in enumerate(lines):
        if any(pattern in line.lower() for pattern in patterns):
            start = max(0, index - context)
            end = min(len(lines), index + context + 1)
            return "\n".join(lines[start:end][:max_lines])
    return "\n".join(lines[: min(max_lines, len(lines))])


def normalize_people(values: Iterable[Dict[str, Any]]) -> List[str]:
    return [item.get("login") for item in values or [] if item.get("login")]


def normalize_labels(values: Iterable[Dict[str, Any]]) -> List[str]:
    return [item.get("name") for item in values or [] if item.get("name")]


def plan_mutation(action: str, target: str, confirmed: bool = False, dry_run: bool = True) -> Dict[str, Any]:
    item = {"action": action, "target": target, "dry_run": dry_run, "confirmed": confirmed}
    if dry_run:
        return envelope(ok=True, items=[item], next_actions=["Review the dry-run plan and explicitly confirm before execution."])
    if not confirmed:
        return envelope(
            ok=False,
            items=[item],
            warnings=[f"{action} on {target} requires explicit confirmation."],
            next_actions=[f"Confirm the exact operation and target before running {action}."],
        )
    return envelope(ok=True, items=[item], next_actions=["Run the confirmed mutation, then re-inspect the target."])


def print_payload(payload: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(f"ok: {payload['ok']}")
    for warning in payload.get("warnings", []):
        print(f"warning: {warning}")
    for item in payload.get("items", []):
        print(json.dumps(item, sort_keys=True))
    for action in payload.get("next_actions", []):
        print(f"next: {action}")


def base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--repo", default=".", help="Path to the local GitHub repository.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print machine-readable JSON.")
    return parser

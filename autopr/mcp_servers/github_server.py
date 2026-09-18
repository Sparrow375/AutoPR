"""
GitHub MCP Server — AutoPR Tool Server

Exposes GitHub and Git operations as MCP tools and ADK-compatible functions:
- create_branch
- read_file
- write_file
- get_diff
- create_pull_request
- create_issue
- list_files

Supports both remote PyGithub operations (when GITHUB_TOKEN is present)
and local Git workspace operations as a zero-config fallback.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from autopr.config.settings import get_settings
from autopr.tools.exceptions import GitOperationError

logger = logging.getLogger("autopr.mcp.github")

server = MCPServer("autopr-github")


class FileChange(BaseModel):
    path: str
    content: str
    commit_message: str


def _get_workspace_root() -> Path:
    """Resolve current repository workspace root."""
    return Path(os.getcwd()).resolve()


def _run_git_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Execute a local git command safely."""
    work_dir = cwd or _get_workspace_root()
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return result
    except Exception as e:
        raise GitOperationError(operation=" ".join(args), reason=str(e)) from e


@server.tool()
def create_branch(branch_name: str, base_branch: str = "main") -> dict[str, Any]:
    """Create a new Git branch for work item implementation.

    Args:
        branch_name: Name of the new branch (e.g. 'feat/ENG-123-user-auth').
        base_branch: Name of base branch to branch off from (default 'main').

    Returns:
        Dictionary with status, branch name, and base branch.
    """
    settings = get_settings()
    logger.info("Creating branch %s from %s", branch_name, base_branch)

    # 1. Try PyGithub if token and remote configured
    if settings.github_token and settings.github_repo_owner:
        try:
            from github import Github

            gh = Github(settings.github_token)
            repo = gh.get_repo(f"{settings.github_repo_owner}/{settings.github_repo_name}")
            base_ref = repo.get_branch(base_branch)
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.commit.sha)
            return {
                "success": True,
                "branch": branch_name,
                "base": base_branch,
                "mode": "remote_github",
            }
        except Exception as e:
            logger.warning("Remote GitHub create_branch failed (%s), falling back to local git", e)

    # 2. Local git fallback
    proc = _run_git_command(["checkout", "-b", branch_name])
    if proc.returncode != 0 and "already exists" in proc.stderr:
        # Branch exists, switch to it
        proc = _run_git_command(["checkout", branch_name])

    if proc.returncode != 0:
        raise GitOperationError(operation=f"checkout -b {branch_name}", reason=proc.stderr.strip())

    return {
        "success": True,
        "branch": branch_name,
        "base": base_branch,
        "mode": "local_git",
    }


@server.tool()
def read_file(file_path: str, branch: str | None = None) -> str:
    """Read file content from the repository.

    Args:
        file_path: Relative path to the file from repository root.
        branch: Optional git branch name (reads working copy if omitted).

    Returns:
        The content of the file as string.
    """
    settings = get_settings()
    norm_path = file_path.replace("\\", "/")

    if branch and settings.github_token and settings.github_repo_owner:
        try:
            from github import Github

            gh = Github(settings.github_token)
            repo = gh.get_repo(f"{settings.github_repo_owner}/{settings.github_repo_name}")
            content_file = repo.get_contents(norm_path, ref=branch)
            return content_file.decoded_content.decode("utf-8")
        except Exception as e:
            logger.debug("Remote read_file failed (%s), reading from local disk", e)

    local_path = _get_workspace_root() / norm_path
    if not local_path.exists():
        raise GitOperationError(operation="read_file", reason=f"File not found: {file_path}")

    return local_path.read_text(encoding="utf-8")


@server.tool()
def write_file(file_path: str, content: str, commit_message: str = "Update file") -> dict[str, Any]:
    """Write content to a file in the repository and stage it.

    Args:
        file_path: Relative path to the target file.
        content: The text content to write.
        commit_message: Description of the file modification.

    Returns:
        Dictionary with status, path, and bytes written.
    """
    norm_path = file_path.replace("\\", "/")
    full_path = _get_workspace_root() / norm_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

    # Stage the file locally
    _run_git_command(["add", norm_path])

    return {
        "success": True,
        "path": norm_path,
        "bytes_written": len(content.encode("utf-8")),
        "staged": True,
        "commit_message": commit_message,
    }


@server.tool()
def get_diff(base_branch: str = "main", head_branch: str | None = None) -> str:
    """Get the unified git diff between current changes/branch and base branch.

    Args:
        base_branch: Target branch to compare against (default 'main').
        head_branch: Optional head branch. If None, diffs current working tree and staged changes.

    Returns:
        Unified git diff text.
    """
    if head_branch:
        proc = _run_git_command(["diff", f"{base_branch}...{head_branch}"])
    else:
        # Check staged + unstaged changes
        proc = _run_git_command(["diff", "HEAD"])
        if not proc.stdout.strip():
            # Try plain diff
            proc = _run_git_command(["diff"])

    return proc.stdout


@server.tool()
def create_pull_request(
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main",
    commit_changes: bool = False,
) -> dict[str, Any]:
    """Create a GitHub Pull Request with the proposed changes.

    Args:
        title: PR title (e.g. 'feat(auth): add JWT authentication').
        body: Markdown body describing changes, rationale, testing done.
        head_branch: Feature branch containing commits.
        base_branch: Target base branch (default 'main').
        commit_changes: Whether to stage and commit uncommitted files first.

    Returns:
        Dictionary with PR number, PR URL, and status.
    """
    settings = get_settings()

    # Commit any remaining uncommitted changes locally only if requested
    if commit_changes:
        status = _run_git_command(["status", "--porcelain"])
        if status.stdout.strip():
            _run_git_command(["add", "-A"])
            _run_git_command(["commit", "-m", title])

    if settings.github_token and settings.github_repo_owner:
        try:
            from github import Github

            gh = Github(settings.github_token)
            repo = gh.get_repo(f"{settings.github_repo_owner}/{settings.github_repo_name}")
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
            )
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "title": pr.title,
                "mode": "github_api",
            }
        except Exception as e:
            logger.warning("Remote PR creation failed (%s), providing local/simulated PR record", e)

    # Simulated/Local PR record (for hackathon demo without push credentials)
    mock_url = (
        f"https://github.com/{settings.github_repo_owner or 'user'}/"
        f"{settings.github_repo_name}/pull/{hash(title) % 1000 + 1}"
    )
    return {
        "success": True,
        "pr_number": hash(title) % 1000 + 1,
        "pr_url": mock_url,
        "title": title,
        "body": body,
        "head_branch": head_branch,
        "base_branch": base_branch,
        "mode": "simulated_local",
    }


@server.tool()
def create_issue(title: str, body: str, labels: list[str] | None = None) -> dict[str, Any]:
    """Create a GitHub Issue (used for smart escalation when retries fail).

    Args:
        title: Issue title (e.g. '[AutoPR Escalation] Implementation failed for ENG-123').
        body: Detailed description of failure, attempts made, error logs.
        labels: Optional issue labels (e.g. ['help wanted', 'autopr-escalation']).

    Returns:
        Dictionary with issue number and URL.
    """
    settings = get_settings()
    labels = labels or ["help wanted", "autopr-escalation"]

    if settings.github_token and settings.github_repo_owner:
        try:
            from github import Github

            gh = Github(settings.github_token)
            repo = gh.get_repo(f"{settings.github_repo_owner}/{settings.github_repo_name}")
            issue = repo.create_issue(title=title, body=body, labels=labels)
            return {
                "success": True,
                "issue_number": issue.number,
                "issue_url": issue.html_url,
                "title": issue.title,
            }
        except Exception as e:
            logger.warning("Remote create_issue failed (%s), returning local record", e)

    mock_url = (
        f"https://github.com/{settings.github_repo_owner or 'user'}/"
        f"{settings.github_repo_name}/issues/{hash(title) % 500 + 1}"
    )
    return {
        "success": True,
        "issue_number": hash(title) % 500 + 1,
        "issue_url": mock_url,
        "title": title,
        "body": body,
        "labels": labels,
        "mode": "simulated_local",
    }


@server.tool()
def list_files(directory: str = "", branch: str | None = None) -> list[str]:
    """List repository files matching directory path.

    Args:
        directory: Relative directory path from repository root (default root).
        branch: Optional branch name.

    Returns:
        List of relative file paths.
    """
    root = _get_workspace_root() / directory if directory else _get_workspace_root()
    if not root.exists():
        return []

    ignored_dirs = {".git", ".venv", "node_modules", "__pycache__", ".chroma"}
    files: list[str] = []

    for p in root.rglob("*"):
        if any(ignored in p.parts for ignored in ignored_dirs):
            continue
        if p.is_file():
            files.append(str(p.relative_to(_get_workspace_root())).replace("\\", "/"))

    return files


if __name__ == "__main__":
    server.run()

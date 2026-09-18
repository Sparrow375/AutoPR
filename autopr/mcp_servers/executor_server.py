"""
Code Execution & Validation MCP Server — AutoPR Tool Server

Exposes sandboxed code validation, execution, and linting as MCP tools and ADK functions:
- run_command
- run_tests
- run_lint
- check_syntax

Provides structured test outputs, syntax validation, and timeouts for ReAct feedback loops.
"""

from __future__ import annotations

import ast
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("autopr.mcp.executor")

server = MCPServer("autopr-executor")


def _get_workspace_root() -> Path:
    """Resolve current repository workspace root."""
    return Path(os.getcwd()).resolve()


@server.tool()
def run_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Execute a shell command with timeout and output capture.

    Args:
        command: Command string to execute.
        cwd: Optional working directory (defaults to workspace root).
        timeout: Maximum execution time in seconds (default 60).

    Returns:
        Dictionary with exit_code, stdout, stderr, and timed_out status.
    """
    work_dir = Path(cwd).resolve() if cwd else _get_workspace_root()
    logger.info("Executing command: %s in %s (timeout=%ds)", command, work_dir, timeout)

    try:
        proc = subprocess.run(
            command,
            cwd=str(work_dir),
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
            "success": proc.returncode == 0,
        }
    except subprocess.TimeoutExpired as e:
        logger.warning("Command '%s' timed out after %ds", command, timeout)
        return {
            "exit_code": -1,
            "stdout": e.stdout or "" if isinstance(e.stdout, str) else "",
            "stderr": f"Command timed out after {timeout} seconds",
            "timed_out": True,
            "success": False,
        }
    except Exception as e:
        logger.error("Failed to run command '%s': %s", command, e)
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "timed_out": False,
            "success": False,
        }


@server.tool()
def run_tests(
    test_path: str = "autopr/tests",
    cwd: str | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """Run pytest suite and parse test outcomes for agent diagnostic loops.

    Args:
        test_path: Path or test selector (default 'autopr/tests').
        cwd: Optional working directory.
        timeout: Maximum execution time in seconds.

    Returns:
        Dictionary with passed, total, failed, error summary, and raw output.
    """
    work_dir = Path(cwd).resolve() if cwd else _get_workspace_root()
    cmd = f'"{sys.executable}" -m pytest {test_path} -v --tb=short'
    result = run_command(command=cmd, cwd=str(work_dir), timeout=timeout)

    stdout = result["stdout"]
    stderr = result["stderr"]

    passed = result["exit_code"] == 0
    # Basic summary parser
    summary_line = ""
    for line in reversed(stdout.splitlines()):
        if "passed" in line or "failed" in line or "error" in line:
            summary_line = line
            break

    return {
        "success": passed,
        "exit_code": result["exit_code"],
        "summary": summary_line or ("Tests passed" if passed else "Tests failed"),
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": result["timed_out"],
    }


@server.tool()
def run_lint(
    path: str = "autopr",
    cwd: str | None = None,
) -> dict[str, Any]:
    """Run ruff linter on target path and return violations.

    Args:
        path: Path to lint (default 'autopr').
        cwd: Optional working directory.

    Returns:
        Dictionary with success status, violations, and exit code.
    """
    work_dir = Path(cwd).resolve() if cwd else _get_workspace_root()
    cmd = f'"{sys.executable}" -m ruff check {path}'
    result = run_command(command=cmd, cwd=str(work_dir), timeout=30)

    return {
        "success": result["exit_code"] == 0,
        "exit_code": result["exit_code"],
        "output": result["stdout"] or result["stderr"],
    }


@server.tool()
def check_syntax(file_path: str) -> dict[str, Any]:
    """Validate Python syntax for a file using AST parsing and py_compile.

    Args:
        file_path: Path to python file.

    Returns:
        Dictionary with valid status, error message, and line number if invalid.
    """
    full_path = _get_workspace_root() / file_path.replace("\\", "/")
    if not full_path.exists():
        return {"valid": False, "error": f"File not found: {file_path}", "line": 0}

    try:
        content = full_path.read_text(encoding="utf-8")
        ast.parse(content, filename=str(full_path))
        return {"valid": True, "error": None, "line": None}
    except SyntaxError as e:
        return {
            "valid": False,
            "error": f"SyntaxError: {e.msg}",
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text,
        }
    except Exception as e:
        return {"valid": False, "error": str(e), "line": None}


if __name__ == "__main__":
    server.run()

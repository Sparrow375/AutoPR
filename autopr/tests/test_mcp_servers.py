"""
Unit tests for AutoPR MCP Servers (GitHub, Linear, Discord, Executor).
"""

from __future__ import annotations

import pytest

from autopr.mcp_servers import (
    discord_server,
    executor_server,
    github_server,
    linear_server,
)


def test_github_server_list_files() -> None:
    files = github_server.list_files()
    assert len(files) > 0
    assert any("pyproject.toml" in f for f in files)


def test_github_server_read_file() -> None:
    content = github_server.read_file("pyproject.toml")
    assert "autopr" in content.lower()


def test_github_server_create_pull_request_simulated() -> None:
    pr = github_server.create_pull_request(
        title="test: sample PR",
        body="PR description body",
        head_branch="test/sample",
        base_branch="main",
    )
    assert pr["success"] is True
    assert "pr_url" in pr
    assert pr["title"] == "test: sample PR"


def test_github_server_create_issue() -> None:
    issue = github_server.create_issue(
        title="[AutoPR Escalation] Test issue",
        body="Detailed failure traceback",
    )
    assert issue["success"] is True
    assert "issue_url" in issue


@pytest.mark.asyncio
async def test_linear_server_get_issue_demo() -> None:
    issue = await linear_server.get_issue("ENG-101")
    assert issue["identifier"] == "ENG-101"
    assert "title" in issue
    assert "description" in issue


@pytest.mark.asyncio
async def test_linear_server_update_status() -> None:
    res = await linear_server.update_issue_status("ENG-101", "In Progress")
    assert res["success"] is True
    assert res["state"] == "In Progress"


@pytest.mark.asyncio
async def test_linear_server_add_comment() -> None:
    res = await linear_server.add_comment("ENG-101", "Automated test comment")
    assert res["success"] is True


@pytest.mark.asyncio
async def test_discord_server_simulated_notification() -> None:
    res = await discord_server.send_notification("Test notification")
    assert res["success"] is True


@pytest.mark.asyncio
async def test_discord_server_pipeline_update() -> None:
    res = await discord_server.send_pipeline_update(
        event_type="PR_CREATED",
        status="success",
        details="Pull request ready for review",
        pr_url="https://github.com/Sparrow375/AutoPR/pull/1",
        work_item_id="ENG-101",
    )
    assert res["success"] is True


def test_executor_server_run_command() -> None:
    res = executor_server.run_command("echo AutoPR_OK")
    assert res["success"] is True
    assert "AutoPR_OK" in res["stdout"]


def test_executor_server_check_syntax() -> None:
    # Valid file
    res = executor_server.check_syntax("autopr/config/settings.py")
    assert res["valid"] is True

    # Non-existent file
    res_bad = executor_server.check_syntax("non_existent_file.py")
    assert res_bad["valid"] is False

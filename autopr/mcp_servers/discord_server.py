"""
Discord MCP Server — AutoPR Notification Tool Server

Exposes notification dispatch as MCP tools and ADK-compatible functions:
- send_notification
- send_pipeline_update

Sends Discord webhook payloads with rich embeds, color codes, and status fields.
Operates in safe logging mode if DISCORD_WEBHOOK_URL is unset.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer

from autopr.config.settings import get_settings

logger = logging.getLogger("autopr.mcp.discord")

server = MCPServer("autopr-discord")

COLOR_MAP = {
    "success": 0x22C55E,  # Vibrant emerald
    "in_progress": 0x3B82F6,  # Modern blue
    "warning": 0xF97316,  # Amber orange
    "error": 0xEF4444,  # Rose red
    "info": 0x6366F1,  # Indigo
}


@server.tool()
async def send_notification(
    content: str, embeds: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Send a notification message with optional embeds to the configured Discord channel.

    Args:
        content: Main text message.
        embeds: Optional list of Discord embed dictionaries.

    Returns:
        Dictionary with status and delivery details.
    """
    settings = get_settings()
    webhook_url = settings.discord_webhook_url

    if not webhook_url:
        logger.info("[Discord Notification (Simulated)] %s | Embeds: %s", content, embeds)
        return {"success": True, "mode": "simulated", "delivered": False, "reason": "No webhook URL"}

    payload: dict[str, Any] = {"content": content}
    if embeds:
        payload["embeds"] = embeds

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            return {"success": True, "mode": "live_webhook", "delivered": True}
    except Exception as e:
        logger.error("Failed to deliver Discord webhook: %s", e)
        return {"success": False, "error": str(e), "mode": "live_webhook", "delivered": False}


@server.tool()
async def send_pipeline_update(
    event_type: str,
    status: str,
    details: str,
    pr_url: str | None = None,
    work_item_id: str = "",
) -> dict[str, Any]:
    """Send a formatted pipeline status update with a rich embed to Discord.

    Args:
        event_type: Type of event (e.g. 'PR_CREATED', 'PIPELINE_FAILED', 'VALIDATION_FAILED').
        status: Status category ('success', 'in_progress', 'warning', 'error', 'info').
        details: Human-readable description of the event or progress.
        pr_url: Optional Pull Request URL to attach as a clickable link.
        work_item_id: Associated work item identifier (e.g. 'ENG-101').

    Returns:
        Dictionary with status and delivery details.
    """
    color = COLOR_MAP.get(status.lower(), COLOR_MAP["info"])

    title = f"🚀 AutoPR Update: {event_type.replace('_', ' ').title()}"
    if work_item_id:
        title += f" ({work_item_id})"

    fields = [
        {"name": "Status", "value": status.upper(), "inline": True},
    ]

    if work_item_id:
        fields.append({"name": "Work Item", "value": work_item_id, "inline": True})

    if pr_url:
        fields.append({"name": "Pull Request", "value": f"[View PR on GitHub]({pr_url})", "inline": False})

    embed = {
        "title": title,
        "description": details,
        "color": color,
        "fields": fields,
        "footer": {"text": "AutoPR • Autonomous Agent Pipeline"},
    }

    return await send_notification(content="", embeds=[embed])


if __name__ == "__main__":
    server.run()

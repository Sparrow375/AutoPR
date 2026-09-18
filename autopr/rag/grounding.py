"""
AutoPR RAG Pipeline — Knowledge Grounding & BRD Injection

Provides adaptive knowledge injection from Business Requirement Documents (BRDs),
project specifications, and documentation into agent execution contexts.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger("autopr.rag.grounding")


class BRDContext(BaseModel):
    """Extracted business requirements and constraints from a BRD document."""

    title: str
    file_path: str
    raw_content: str
    requirements: list[str] = []
    constraints: list[str] = []
    tech_stack_rules: list[str] = []


def _get_workspace_root() -> Path:
    return Path(os.getcwd()).resolve()


def discover_and_load_brd(custom_path: str | None = None) -> BRDContext | None:
    """Discover and parse active Business Requirement Documents (BRD / PRD / Spec).

    Args:
        custom_path: Optional explicit file path to a BRD/PRD document.

    Returns:
        BRDContext if found and parsed, None otherwise.
    """
    root = _get_workspace_root()

    candidate_files: list[Path] = []
    if custom_path:
        p = Path(custom_path)
        candidate_files.append(p if p.is_absolute() else root / p)
    else:
        # Check standard BRD filenames and folders
        patterns = [
            "*BRD*.md",
            "*PRD*.md",
            "*AutoPR*.docx.md",
            "docs/*brd*.md",
            "docs/*prd*.md",
            "brd/*.md",
        ]
        for pattern in patterns:
            candidate_files.extend(list(root.glob(pattern)))

    valid_file: Path | None = None
    for candidate in candidate_files:
        if candidate.is_file() and candidate.stat().st_size > 50:
            valid_file = candidate
            break

    if not valid_file:
        logger.info("No active BRD/PRD document found in workspace")
        return None

    try:
        content = valid_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error("Failed to read BRD file %s: %s", valid_file, e)
        return None

    rel_path = str(valid_file.relative_to(root)).replace("\\", "/")
    logger.info("Loaded active BRD document from %s (%d chars)", rel_path, len(content))

    # Extract bullet points under key sections
    requirements: list[str] = []
    constraints: list[str] = []
    tech_stack: list[str] = []

    lines = content.splitlines()
    current_section = "req"  # default to requirements

    for line in lines:
        clean = line.strip()
        if clean.startswith("#"):
            lower_header = clean.lower()
            if "outcome" in lower_header or "requirement" in lower_header or "workflow" in lower_header or "goal" in lower_header:
                current_section = "req"
            elif "constraint" in lower_header or "rule" in lower_header or "ground rule" in lower_header:
                current_section = "const"
            elif "tech" in lower_header or "stack" in lower_header or "architecture" in lower_header:
                current_section = "tech"
            else:
                current_section = "req"
            continue

        if re.match(r"^[*•\-\d\.]+\s+", clean):
            bullet = re.sub(r"^[*•\-\d\.]+\s+", "", clean).strip()
            if len(bullet) > 10:
                if current_section == "const":
                    constraints.append(bullet)
                elif current_section == "tech":
                    tech_stack.append(bullet)
                else:
                    requirements.append(bullet)

    return BRDContext(
        title=valid_file.stem,
        file_path=rel_path,
        raw_content=content[:5000],  # Truncate to reasonable context window
        requirements=requirements[:15],
        constraints=constraints[:10],
        tech_stack_rules=tech_stack[:10],
    )


def format_brd_for_prompt(brd: BRDContext | None = None) -> str:
    """Format parsed BRD rules into markdown for agent prompts."""
    active_brd = brd or discover_and_load_brd()
    if not active_brd:
        return ""

    sections = [
        f"## Active Business Requirement Document (BRD: `{active_brd.file_path}`)",
    ]

    if active_brd.requirements:
        sections.append("### Key Requirements:")
        for r in active_brd.requirements:
            sections.append(f"- {r}")

    if active_brd.constraints:
        sections.append("### Project Constraints:")
        for c in active_brd.constraints:
            sections.append(f"- {c}")

    if active_brd.tech_stack_rules:
        sections.append("### Architectural & Tech Stack Directives:")
        for t in active_brd.tech_stack_rules:
            sections.append(f"- {t}")

    return "\n".join(sections)

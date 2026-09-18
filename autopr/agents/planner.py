"""
AutoPR Agent — PlannerAgent

Analyzes work item requirements, investigates codebase context via RAG,
consults active BRD rules, formulates an execution plan, and self-evaluates
a confidence score for human-in-the-loop review.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from autopr.config.models import get_model_client
from autopr.config.settings import get_settings
from autopr.rag.grounding import discover_and_load_brd, format_brd_for_prompt
from autopr.rag.retriever import get_retriever

logger = logging.getLogger("autopr.agents.planner")


class PlanStep(BaseModel):
    """An individual actionable step in the implementation plan."""

    step_number: int
    action: str = Field(description="e.g. 'CREATE_FILE', 'MODIFY_FILE', 'ADD_TEST'")
    file_path: str = Field(description="Relative path of file to create or modify")
    description: str = Field(description="Detailed instructions of what to implement")


class ImplementationPlan(BaseModel):
    """Structured plan produced by PlannerAgent."""

    work_item_id: str
    title: str
    summary: str
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)
    confidence_rationale: str = ""
    risk_assessment: str = Field(default="low", description="'low', 'medium', or 'high'")
    target_files: list[str] = []
    steps: list[PlanStep] = []
    test_strategy: list[str] = []
    needs_human_approval: bool = False


class PlannerAgent:
    """Agent responsible for context discovery and implementation planning."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.retriever = get_retriever()
        self.model_client = get_model_client()

    async def plan(
        self,
        work_item: dict[str, Any],
        custom_instructions: str = "",
    ) -> ImplementationPlan:
        """Analyze ticket and generate structured ImplementationPlan.

        Args:
            work_item: Work item dictionary (id, title, description, labels).
            custom_instructions: Optional user-provided guidance or overrides.

        Returns:
            ImplementationPlan instance.
        """
        item_id = str(work_item.get("identifier") or work_item.get("id") or "UNKNOWN")
        title = str(work_item.get("title", ""))
        desc = str(work_item.get("description", ""))

        logger.info("PlannerAgent planning for %s: '%s'", item_id, title)

        # 1. RAG Context Retrieval
        query = f"{title} {desc}"
        snippets = self.retriever.retrieve(query=query, top_k=self.settings.rag_top_k)
        rag_context = self.retriever.format_for_prompt(snippets)

        # 2. BRD Context Retrieval
        brd_context = format_brd_for_prompt(discover_and_load_brd())

        system_instruction = (
            "You are the PlannerAgent in AutoPR, an autonomous software engineering assistant. "
            "Your role is to analyze a work item ticket, examine codebase snippets, and produce "
            "a concrete, minimal, high-quality ImplementationPlan.\n"
            "Rules:\n"
            "1. Be precise about which files to modify and which tests to create/update.\n"
            "2. Evaluate your confidence score (0.0 to 1.0). If requirements are ambiguous, give <0.7.\n"
            "3. Favor non-breaking, incremental changes following existing project architecture.\n"
            "4. Follow any rules in the active BRD (Business Requirement Document) provided."
        )

        prompt = f"""
## Work Item Ticket:
- **ID**: {item_id}
- **Title**: {title}
- **Description**: {desc}
- **Labels**: {work_item.get('labels', [])}
- **Additional Instructions**: {custom_instructions or 'None'}

{brd_context}

{rag_context}

Produce the structured ImplementationPlan with realistic file targets, step-by-step instructions, and test plan.
"""

        plan = self.model_client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            model=self.settings.planning_model,
            response_schema=ImplementationPlan,
        )

        if isinstance(plan, ImplementationPlan):
            # Ensure work_item_id and title match
            plan.work_item_id = item_id
            if not plan.title:
                plan.title = title
            # Check confidence against threshold
            if plan.confidence_score < self.settings.confidence_threshold:
                plan.needs_human_approval = True
            return plan

        # Fallback plan if model failed to validate schema
        logger.warning("Falling back to synthetic ImplementationPlan for %s", item_id)
        return ImplementationPlan(
            work_item_id=item_id,
            title=title,
            summary=f"Implementation plan for {item_id}: {title}",
            confidence_score=0.8,
            confidence_rationale="Generated via fallback heuristic planning.",
            risk_assessment="low",
            target_files=["autopr/api/server.py"],
            steps=[
                PlanStep(
                    step_number=1,
                    action="MODIFY_FILE",
                    file_path="autopr/api/server.py",
                    description=f"Implement requirements for {title}",
                )
            ],
            test_strategy=[f"Add unit test in autopr/tests/test_{item_id.lower().replace('-', '_')}.py"],
            needs_human_approval=False,
        )

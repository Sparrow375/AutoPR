"""
AutoPR Agent — OrchestratorAgent

Root agent coordinating the multi-agent hierarchy (Planner, Coder, Reviewer, Notifier).
Manages pipeline stage state machines, emits typed WebSocket events, supports
Intentional Failure Demo mode, BRD injection, and Human-in-the-Loop approval.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from autopr.agents.coder import CoderAgent
from autopr.agents.notifier import NotifierAgent
from autopr.agents.planner import PlannerAgent
from autopr.agents.reviewer import ReviewerAgent
from autopr.api.events import (
    CheckStatus,
    CodeChangesData,
    ConfidenceUpdateData,
    ErrorData,
    EventType,
    FileAction,
    FileChangeData,
    HumanInputNeededData,
    PipelineCompletedData,
    PipelineEvent,
    PipelineStartedData,
    PRCreatedData,
    ReasoningData,
    RetryStartedData,
    Stage,
    StageCompletedData,
    StageData,
    ToolCalledData,
    ValidationCheck,
    ValidationResultData,
    WorkItemSource,
)
from autopr.config.settings import get_settings
from autopr.mcp_servers import github_server, linear_server

logger = logging.getLogger("autopr.agents.orchestrator")

EventEmitter = Callable[[PipelineEvent], Awaitable[None]]


class OrchestratorAgent:
    """Main coordinator governing autonomous work item to PR lifecycle."""

    def __init__(
        self,
        event_emitter: EventEmitter | None = None,
    ) -> None:
        self.settings = get_settings()
        self.event_emitter = event_emitter
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.reviewer = ReviewerAgent()
        self.notifier = NotifierAgent()

    async def _emit(self, event: PipelineEvent) -> None:
        """Emit event over WebSocket if emitter callback is registered."""
        if self.event_emitter:
            try:
                await self.event_emitter(event)
            except Exception as e:
                logger.warning("Failed to emit WebSocket event: %s", e)

    async def run(
        self,
        work_item_id: str,
        source: WorkItemSource = WorkItemSource.LINEAR,
        inject_failure: bool = False,
        custom_instructions: str = "",
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute full autonomous end-to-end pipeline run.

        Args:
            work_item_id: Work item identifier (e.g. 'ENG-101' or '42').
            source: Source tracker ('linear' or 'github').
            inject_failure: If True, executes Intentional Failure Demo mode.
            custom_instructions: Optional user guidance overrides.
            run_id: Optional unique run identifier.

        Returns:
            Dictionary with final outcome, PR details, and telemetry.
        """
        active_run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        stages_completed: list[str] = []

        logger.info("Starting AutoPR pipeline [run_id=%s] for %s (%s)", active_run_id, work_item_id, source.value)

        # ------------------------------------------------------------------
        # 1. Pipeline Started
        # ------------------------------------------------------------------
        await self._emit(
            PipelineEvent.create(
                run_id=active_run_id,
                event_type=EventType.PIPELINE_STARTED,
                **PipelineStartedData(
                    work_item_id=work_item_id,
                    title=f"Work item {work_item_id}",
                    source=source,
                ).model_dump(),
            )
        )

        try:
            # ------------------------------------------------------------------
            # 2. Stage: FETCHING
            # ------------------------------------------------------------------
            t0 = time.time()
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_STARTED,
                    stage=Stage.FETCHING,
                    **StageData(stage=Stage.FETCHING).model_dump(),
                )
            )
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.REASONING,
                    stage=Stage.FETCHING,
                    **ReasoningData(
                        thought=f"Fetching work item requirements from {source.value.title()} tracker...",
                        agent="OrchestratorAgent",
                    ).model_dump(),
                )
            )

            # Tool call: get_issue
            work_item = await linear_server.get_issue(work_item_id)
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.TOOL_CALLED,
                    stage=Stage.FETCHING,
                    **ToolCalledData(
                        tool_name="linear.get_issue",
                        args={"issue_id": work_item_id},
                        result={"title": work_item.get("title"), "state": work_item.get("state")},
                        duration_ms=int((time.time() - t0) * 1000),
                    ).model_dump(),
                )
            )

            duration_fetch = int((time.time() - t0) * 1000)
            stages_completed.append(Stage.FETCHING.value)
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_COMPLETED,
                    stage=Stage.FETCHING,
                    **StageCompletedData(
                        stage=Stage.FETCHING,
                        duration_ms=duration_fetch,
                        result_summary=f"Retrieved: {work_item.get('title')}",
                    ).model_dump(),
                )
            )

            # ------------------------------------------------------------------
            # 3. Stage: PLANNING
            # ------------------------------------------------------------------
            t0 = time.time()
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_STARTED,
                    stage=Stage.PLANNING,
                    **StageData(stage=Stage.PLANNING).model_dump(),
                )
            )
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.REASONING,
                    stage=Stage.PLANNING,
                    **ReasoningData(
                        thought="Analyzing codebase structure via ChromaDB RAG and checking active BRD directives...",
                        agent="PlannerAgent",
                    ).model_dump(),
                )
            )

            plan = await self.planner.plan(work_item, custom_instructions=custom_instructions)

            # Emit Confidence Score
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.CONFIDENCE_UPDATE,
                    stage=Stage.PLANNING,
                    **ConfidenceUpdateData(
                        score=plan.confidence_score,
                        threshold=self.settings.confidence_threshold,
                        agent="PlannerAgent",
                    ).model_dump(),
                )
            )

            # Human-in-the-Loop check
            if plan.needs_human_approval:
                await self._emit(
                    PipelineEvent.create(
                        run_id=active_run_id,
                        event_type=EventType.HUMAN_INPUT_NEEDED,
                        stage=Stage.PLANNING,
                        **HumanInputNeededData(
                            prompt=f"Confidence {plan.confidence_score:.2f} is below {self.settings.confidence_threshold:.2f}. Approve plan?",
                            options=["Approve & Proceed", "Reject & Abort"],
                            a2ui_payload={
                                "title": plan.title,
                                "summary": plan.summary,
                                "target_files": plan.target_files,
                                "risk": plan.risk_assessment,
                            },
                        ).model_dump(),
                    )
                )

            duration_plan = int((time.time() - t0) * 1000)
            stages_completed.append(Stage.PLANNING.value)
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_COMPLETED,
                    stage=Stage.PLANNING,
                    **StageCompletedData(
                        stage=Stage.PLANNING,
                        duration_ms=duration_plan,
                        result_summary=f"Formulated {len(plan.steps)} steps (Confidence: {plan.confidence_score:.2f})",
                    ).model_dump(),
                )
            )

            # ------------------------------------------------------------------
            # 4. Stage: CODING
            # ------------------------------------------------------------------
            t0 = time.time()
            branch_name = f"feat/{work_item_id.lower()}-{uuid.uuid4().hex[:4]}"
            github_server.create_branch(branch_name=branch_name)

            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_STARTED,
                    stage=Stage.CODING,
                    **StageData(stage=Stage.CODING).model_dump(),
                )
            )
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.REASONING,
                    stage=Stage.CODING,
                    **ReasoningData(
                        thought=f"Implementing {len(plan.steps)} plan steps and generating unit tests on branch {branch_name}...",
                        agent="CoderAgent",
                    ).model_dump(),
                )
            )

            changes = await self.coder.implement_plan(
                plan=plan,
                inject_failure=inject_failure,
            )

            # Emit Code Changes & Diff
            file_changes = [
                FileChangeData(path=p, action=FileAction.MODIFY, diff="")
                for p in changes.files_modified
            ] + [
                FileChangeData(path=p, action=FileAction.CREATE, diff="")
                for p in changes.files_created
            ]
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.CODE_CHANGES,
                    stage=Stage.CODING,
                    **CodeChangesData(files=file_changes).model_dump(),
                )
            )

            duration_code = int((time.time() - t0) * 1000)
            stages_completed.append(Stage.CODING.value)
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_COMPLETED,
                    stage=Stage.CODING,
                    **StageCompletedData(
                        stage=Stage.CODING,
                        duration_ms=duration_code,
                        result_summary=f"Staged {len(file_changes)} files",
                    ).model_dump(),
                )
            )

            # ------------------------------------------------------------------
            # 5. Stage: REVIEWING (Self-Healing ReAct Loop)
            # ------------------------------------------------------------------
            t0 = time.time()
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_STARTED,
                    stage=Stage.REVIEWING,
                    **StageData(stage=Stage.REVIEWING).model_dump(),
                )
            )

            validation = None
            max_attempts = self.settings.max_retry_attempts

            for attempt in range(1, max_attempts + 1):
                await self._emit(
                    PipelineEvent.create(
                        run_id=active_run_id,
                        event_type=EventType.REASONING,
                        stage=Stage.REVIEWING,
                        **ReasoningData(
                            thought=f"Validation attempt {attempt}/{max_attempts}: Running ruff and pytest...",
                            agent="ReviewerAgent",
                        ).model_dump(),
                    )
                )

                validation = await self.reviewer.validate(
                    work_item_id=work_item_id,
                    attempt=attempt,
                )

                # Emit Validation Result
                checks = [
                    ValidationCheck(
                        name="ruff-lint",
                        status=CheckStatus.PASS if "F" not in validation.lint_output else CheckStatus.FAIL,
                        output=validation.lint_output[:300],
                    ),
                    ValidationCheck(
                        name="pytest",
                        status=CheckStatus.PASS if validation.is_valid else CheckStatus.FAIL,
                        output=validation.test_output[:300],
                    ),
                ]
                await self._emit(
                    PipelineEvent.create(
                        run_id=active_run_id,
                        event_type=EventType.VALIDATION_RESULT,
                        stage=Stage.REVIEWING,
                        **ValidationResultData(checks=checks).model_dump(),
                    )
                )

                if validation.is_valid:
                    logger.info("Validation passed on attempt %d!", attempt)
                    break

                if attempt < max_attempts:
                    # Retry Triggered
                    await self._emit(
                        PipelineEvent.create(
                            run_id=active_run_id,
                            event_type=EventType.RETRY_STARTED,
                            stage=Stage.REVIEWING,
                            **RetryStartedData(
                                attempt=attempt,
                                max_attempts=max_attempts,
                                reason=validation.diagnostics[:200] or "Validation checks failed",
                            ).model_dump(),
                        )
                    )
                    await self._emit(
                        PipelineEvent.create(
                            run_id=active_run_id,
                            event_type=EventType.REASONING,
                            stage=Stage.REVIEWING,
                            **ReasoningData(
                                thought=f"Self-healing trigger: instructing CoderAgent to fix failures ({validation.diagnostics[:100]}...)",
                                agent="ReviewerAgent",
                            ).model_dump(),
                        )
                    )

                    # Re-invoke CoderAgent to fix errors with diagnostic feedback
                    changes = await self.coder.implement_plan(
                        plan=plan,
                        diagnostic_feedback=validation.diagnostics,
                        inject_failure=False,  # Clear failure on fix attempt
                    )

            duration_review = int((time.time() - t0) * 1000)
            stages_completed.append(Stage.REVIEWING.value)
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_COMPLETED,
                    stage=Stage.REVIEWING,
                    **StageCompletedData(
                        stage=Stage.REVIEWING,
                        duration_ms=duration_review,
                        result_summary="Validation successful" if validation and validation.is_valid else "Escalation triggered",
                    ).model_dump(),
                )
            )

            # ------------------------------------------------------------------
            # 6. Stage: NOTIFYING
            # ------------------------------------------------------------------
            t0 = time.time()
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_STARTED,
                    stage=Stage.NOTIFYING,
                    **StageData(stage=Stage.NOTIFYING).model_dump(),
                )
            )
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.REASONING,
                    stage=Stage.NOTIFYING,
                    **ReasoningData(
                        thought="Composing natural language PR summary, creating GitHub PR, updating Linear and Discord...",
                        agent="NotifierAgent",
                    ).model_dump(),
                )
            )

            notification = await self.notifier.notify_and_create_pr(
                work_item=work_item,
                plan=plan,
                changes=changes,
                branch_name=branch_name,
            )

            # Emit PR Created
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.PR_CREATED,
                    stage=Stage.NOTIFYING,
                    **PRCreatedData(
                        url=notification.pr_url,
                        number=notification.pr_number,
                        title=notification.pr_title,
                        summary=notification.pr_summary[:400],
                        branch=branch_name,
                    ).model_dump(),
                )
            )

            duration_notify = int((time.time() - t0) * 1000)
            stages_completed.append(Stage.NOTIFYING.value)
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.STAGE_COMPLETED,
                    stage=Stage.NOTIFYING,
                    **StageCompletedData(
                        stage=Stage.NOTIFYING,
                        duration_ms=duration_notify,
                        result_summary=f"PR #{notification.pr_number} dispatched",
                    ).model_dump(),
                )
            )

            # ------------------------------------------------------------------
            # 7. Pipeline Completed
            # ------------------------------------------------------------------
            total_duration = int((time.time() - start_time) * 1000)
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.PIPELINE_COMPLETED,
                    **PipelineCompletedData(
                        success=True,
                        pr_url=notification.pr_url,
                        duration_ms=total_duration,
                        stages_completed=stages_completed,
                    ).model_dump(),
                )
            )

            return {
                "run_id": active_run_id,
                "success": True,
                "work_item_id": work_item_id,
                "pr_url": notification.pr_url,
                "pr_number": notification.pr_number,
                "branch": branch_name,
                "duration_ms": total_duration,
            }

        except Exception as e:
            logger.error("Pipeline run failed: %s", e, exc_info=True)
            total_duration = int((time.time() - start_time) * 1000)
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.ERROR,
                    **ErrorData(
                        message=str(e),
                        stage=Stage.REVIEWING,
                        recoverable=False,
                    ).model_dump(),
                )
            )
            await self._emit(
                PipelineEvent.create(
                    run_id=active_run_id,
                    event_type=EventType.PIPELINE_COMPLETED,
                    **PipelineCompletedData(
                        success=False,
                        pr_url=None,
                        duration_ms=total_duration,
                        stages_completed=stages_completed,
                    ).model_dump(),
                )
            )
            return {
                "run_id": active_run_id,
                "success": False,
                "error": str(e),
                "duration_ms": total_duration,
            }

"""
AutoPR Pipeline Event Schema

⚠️  SHARED CONTRACT — Both backend (Person A) and frontend (Person B) depend on this.
    Any changes here MUST be mirrored in: dashboard/src/lib/types.ts
    Always coordinate with your teammate before modifying.

This module defines the canonical event types and data models for
real-time WebSocket communication between the API server and dashboard.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EventType(StrEnum):
    """All possible WebSocket event types."""

    PIPELINE_STARTED = "pipeline_started"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    TOOL_CALLED = "tool_called"
    REASONING = "reasoning"
    CONFIDENCE_UPDATE = "confidence_update"
    HUMAN_INPUT_NEEDED = "human_input_needed"
    HUMAN_INPUT_RECEIVED = "human_input_received"
    ERROR = "error"
    RETRY_STARTED = "retry_started"
    CODE_CHANGES = "code_changes"
    VALIDATION_RESULT = "validation_result"
    PR_CREATED = "pr_created"
    PIPELINE_COMPLETED = "pipeline_completed"


class Stage(StrEnum):
    """Pipeline stages in execution order."""

    FETCHING = "fetching"
    PLANNING = "planning"
    CODING = "coding"
    REVIEWING = "reviewing"
    NOTIFYING = "notifying"


class WorkItemSource(StrEnum):
    """Supported work item tracker sources."""

    LINEAR = "linear"
    GITHUB = "github"


class FileAction(StrEnum):
    """Actions that can be performed on a file."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class CheckStatus(StrEnum):
    """Status of a validation check."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


# ---------------------------------------------------------------------------
# Event Data Payloads
# ---------------------------------------------------------------------------

class PipelineStartedData(BaseModel):
    """Data for pipeline_started event."""

    work_item_id: str
    title: str
    source: WorkItemSource


class StageData(BaseModel):
    """Data for stage_started event."""

    stage: Stage


class StageCompletedData(BaseModel):
    """Data for stage_completed event."""

    stage: Stage
    duration_ms: int
    result_summary: str


class ToolCalledData(BaseModel):
    """Data for tool_called event."""

    tool_name: str
    args: dict[str, Any] = {}
    result: Any = None
    duration_ms: int = 0


class ReasoningData(BaseModel):
    """Data for reasoning event."""

    thought: str
    agent: str


class ConfidenceUpdateData(BaseModel):
    """Data for confidence_update event."""

    score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    agent: str


class HumanInputNeededData(BaseModel):
    """Data for human_input_needed event."""

    prompt: str
    options: list[str] = []
    a2ui_payload: dict[str, Any] | None = None


class HumanInputReceivedData(BaseModel):
    """Data for human_input_received event."""

    response: str


class ErrorData(BaseModel):
    """Data for error event."""

    message: str
    stage: Stage
    recoverable: bool = True
    stack_trace: str | None = None


class RetryStartedData(BaseModel):
    """Data for retry_started event."""

    attempt: int
    max_attempts: int
    reason: str


class FileChangeData(BaseModel):
    """A single file change."""

    path: str
    action: FileAction
    diff: str = ""


class CodeChangesData(BaseModel):
    """Data for code_changes event."""

    files: list[FileChangeData]


class ValidationCheck(BaseModel):
    """A single validation check result."""

    name: str
    status: CheckStatus
    output: str = ""


class ValidationResultData(BaseModel):
    """Data for validation_result event."""

    checks: list[ValidationCheck]


class PRCreatedData(BaseModel):
    """Data for pr_created event."""

    url: str
    number: int
    title: str
    summary: str
    branch: str


class PipelineCompletedData(BaseModel):
    """Data for pipeline_completed event."""

    success: bool
    pr_url: str | None = None
    duration_ms: int
    stages_completed: list[str] = []


# ---------------------------------------------------------------------------
# Core Event Model
# ---------------------------------------------------------------------------

class PipelineEvent(BaseModel):
    """A single event emitted by the pipeline over WebSocket.

    This is the canonical message format sent from the backend
    to the frontend dashboard.
    """

    run_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: EventType
    stage: Stage | None = None
    data: dict[str, Any] = {}

    def to_ws_message(self) -> str:
        """Serialize to JSON string for WebSocket transmission."""
        return self.model_dump_json()

    @classmethod
    def create(
        cls,
        run_id: str,
        event_type: EventType,
        stage: Stage | None = None,
        **data: Any,
    ) -> PipelineEvent:
        """Factory method for creating events with keyword data."""
        return cls(
            run_id=run_id,
            event_type=event_type,
            stage=stage,
            data=data,
        )


# ---------------------------------------------------------------------------
# API Request/Response Models
# ---------------------------------------------------------------------------

class StartPipelineRequest(BaseModel):
    """POST /api/run — Start a new pipeline run."""

    work_item_id: str
    source: WorkItemSource = WorkItemSource.LINEAR


class StartPipelineResponse(BaseModel):
    """Response from POST /api/run."""

    run_id: str
    status: str = "started"


class RunSummary(BaseModel):
    """Summary of a pipeline run for list view."""

    run_id: str
    work_item_id: str
    source: WorkItemSource
    status: str  # "running", "completed", "failed"
    started_at: datetime
    completed_at: datetime | None = None
    pr_url: str | None = None


class RunDetail(BaseModel):
    """Detailed view of a pipeline run."""

    run_id: str
    work_item_id: str
    source: WorkItemSource
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    pr_url: str | None = None
    events: list[PipelineEvent] = []


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: bool = True
    code: str
    message: str
    details: dict[str, Any] = {}

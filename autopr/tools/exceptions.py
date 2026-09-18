"""
AutoPR Custom Exceptions

Centralized exception hierarchy. All custom exceptions inherit from AutoPRError.
Use specific exceptions for specific failure modes — never raise generic Exception.
"""

from __future__ import annotations


class AutoPRError(Exception):
    """Base exception for all AutoPR errors."""

    def __init__(self, message: str, code: str = "AUTOPR_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class WorkItemNotFoundError(AutoPRError):
    """Raised when a work item ID doesn't exist in the tracker."""

    def __init__(self, item_id: str, source: str = "unknown") -> None:
        super().__init__(
            message=f"Work item '{item_id}' not found in {source}",
            code="WORK_ITEM_NOT_FOUND",
        )
        self.item_id = item_id
        self.source = source


class WorkItemParseError(AutoPRError):
    """Raised when a work item's content can't be parsed into requirements."""

    def __init__(self, item_id: str, reason: str = "") -> None:
        super().__init__(
            message=f"Failed to parse work item '{item_id}': {reason}",
            code="WORK_ITEM_PARSE_ERROR",
        )


class ValidationFailedError(AutoPRError):
    """Raised when code validation (test/lint/build) fails."""

    def __init__(self, check_name: str, output: str = "") -> None:
        super().__init__(
            message=f"Validation check '{check_name}' failed",
            code="VALIDATION_FAILED",
        )
        self.check_name = check_name
        self.output = output


class MaxRetriesExceededError(AutoPRError):
    """Raised when the agent exceeds maximum retry attempts."""

    def __init__(self, attempts: int, reason: str = "") -> None:
        super().__init__(
            message=f"Exceeded {attempts} retry attempts: {reason}",
            code="MAX_RETRIES_EXCEEDED",
        )
        self.attempts = attempts


class MCPConnectionError(AutoPRError):
    """Raised when an MCP server can't be reached."""

    def __init__(self, server_name: str, reason: str = "") -> None:
        super().__init__(
            message=f"MCP server '{server_name}' unreachable: {reason}",
            code="MCP_CONNECTION_ERROR",
        )
        self.server_name = server_name


class RateLimitError(AutoPRError):
    """Raised when an external API rate limit is hit."""

    def __init__(self, service: str, retry_after: int | None = None) -> None:
        msg = f"Rate limit hit for {service}"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(message=msg, code="RATE_LIMIT_ERROR")
        self.service = service
        self.retry_after = retry_after


class GitOperationError(AutoPRError):
    """Raised when a Git/GitHub operation fails."""

    def __init__(self, operation: str, reason: str = "") -> None:
        super().__init__(
            message=f"Git operation '{operation}' failed: {reason}",
            code="GIT_OPERATION_ERROR",
        )


class ContextRetrievalError(AutoPRError):
    """Raised when RAG context retrieval fails."""

    def __init__(self, reason: str = "") -> None:
        super().__init__(
            message=f"Context retrieval failed: {reason}",
            code="CONTEXT_RETRIEVAL_ERROR",
        )


class LowConfidenceError(AutoPRError):
    """Raised when agent confidence is below threshold and human input is needed."""

    def __init__(self, score: float, threshold: float, agent: str = "") -> None:
        super().__init__(
            message=f"Agent '{agent}' confidence {score:.2f} below threshold {threshold:.2f}",
            code="LOW_CONFIDENCE",
        )
        self.score = score
        self.threshold = threshold
        self.agent = agent

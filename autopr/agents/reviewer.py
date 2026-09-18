"""
AutoPR Agent — ReviewerAgent

Runs validation checks (linting, test suite execution, syntax audits),
diagnoses failures with structured root-cause analysis, coordinates the
self-healing ReAct retry loop with CoderAgent, and triggers smart escalation
if maximum retries are exceeded.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from autopr.config.models import get_model_client
from autopr.config.settings import get_settings
from autopr.mcp_servers import (
    discord_server,
    executor_server,
    github_server,
    linear_server,
)

logger = logging.getLogger("autopr.agents.reviewer")


class Diagnostics(BaseModel):
    """Root-cause analysis and actionable repair guidance produced by Reviewer."""

    root_cause: str = Field(description="Explanation of why the test or lint failed")
    suggested_fix: str = Field(description="Concrete instructions for CoderAgent to fix the issue")
    affected_files: list[str] = Field(description="List of files that must be updated")


class ValidationResult(BaseModel):
    """Comprehensive validation outcome produced by ReviewerAgent."""

    is_valid: bool
    attempt_number: int = 1
    checks_passed: int = 0
    checks_failed: int = 0
    test_output: str = ""
    lint_output: str = ""
    diagnostics: str = ""
    escalated: bool = False
    escalation_issue_url: str | None = None


class ReviewerAgent:
    """Agent responsible for code validation, diagnosis, and retry orchestration."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_client = get_model_client()

    async def validate(
        self,
        work_item_id: str,
        attempt: int = 1,
        test_selector: str | None = None,
    ) -> ValidationResult:
        """Run lint and tests, diagnose any failures, and escalate if needed.

        Args:
            work_item_id: Associated work item identifier.
            attempt: Current retry attempt count.
            test_selector: Specific test path or test file selector.

        Returns:
            ValidationResult with diagnostics and status.
        """
        logger.info("ReviewerAgent running validation (Attempt %d/%d) for %s", attempt, self.settings.max_retry_attempts, work_item_id)

        # 1. Run Lint Check
        lint_res = executor_server.run_lint("autopr")
        lint_success = lint_res["success"]
        lint_output = lint_res["output"]

        # 2. Run Test Suite
        test_path = test_selector or f"autopr/tests/test_{work_item_id.lower().replace('-', '_')}.py"
        test_res = executor_server.run_tests(test_path=test_path)
        test_success = test_res["success"]
        test_output = f"{test_res['stdout']}\n{test_res['stderr']}"

        # Combine checks
        passed_count = (1 if lint_success else 0) + (1 if test_success else 0)
        failed_count = (0 if lint_success else 1) + (0 if test_success else 1)
        is_valid = lint_success and test_success

        diagnostics_text = ""

        if not is_valid:
            logger.warning("Validation failed for %s. Analyzing failures...", work_item_id)
            diag_prompt = f"""
Analyze the following test/lint failures for Work Item {work_item_id}:

## Lint Output:
{lint_output[:2000]}

## Test Output:
{test_output[:3000]}

Provide root cause diagnosis and concrete instructions for CoderAgent to resolve the issue.
"""
            diag_schema = self.model_client.generate(
                prompt=diag_prompt,
                model=self.settings.review_model,
                response_schema=Diagnostics,
            )

            if isinstance(diag_schema, Diagnostics):
                diagnostics_text = f"**Root Cause**: {diag_schema.root_cause}\n**Suggested Fix**: {diag_schema.suggested_fix}"
            else:
                diagnostics_text = f"Validation failed: Tests or lint had non-zero exit codes.\n{test_output[-500:]}"

            # Smart Escalation if max attempts exceeded
            if attempt >= self.settings.max_retry_attempts:
                logger.error("Max retries exceeded for %s. Triggering smart escalation!", work_item_id)
                escalation_title = f"[AutoPR Escalation] Autonomous implementation failed for {work_item_id}"
                escalation_body = f"""
## AutoPR Escalation Report
- **Work Item**: {work_item_id}
- **Attempts Made**: {attempt}
- **Status**: Self-healing loop unable to resolve validation errors.

### Failure Diagnostics:
{diagnostics_text}

### Raw Test Traceback:
```
{test_output[-1500:]}
```

### Raw Lint Output:
```
{lint_output[-800:]}
```

*This issue was automatically created by AutoPR Smart Escalation for human engineering intervention.*
"""
                issue_record = github_server.create_issue(
                    title=escalation_title,
                    body=escalation_body,
                    labels=["help wanted", "autopr-escalation"],
                )
                issue_url = issue_record.get("issue_url")

                # Post notification to Linear and Discord
                await linear_server.add_comment(
                    issue_id=work_item_id,
                    comment=f"⚠️ **AutoPR Escalation**: Autonomous retry limit reached. Escalation issue created: {issue_url}",
                )
                await discord_server.send_pipeline_update(
                    event_type="SMART_ESCALATION",
                    status="error",
                    details=f"Autonomous retry limit exceeded for {work_item_id}. Created escalation issue: {issue_url}",
                    work_item_id=work_item_id,
                )

                return ValidationResult(
                    is_valid=False,
                    attempt_number=attempt,
                    checks_passed=passed_count,
                    checks_failed=failed_count,
                    test_output=test_output,
                    lint_output=lint_output,
                    diagnostics=diagnostics_text,
                    escalated=True,
                    escalation_issue_url=issue_url,
                )

        return ValidationResult(
            is_valid=is_valid,
            attempt_number=attempt,
            checks_passed=passed_count,
            checks_failed=failed_count,
            test_output=test_output,
            lint_output=lint_output,
            diagnostics=diagnostics_text,
            escalated=False,
            escalation_issue_url=None,
        )

"""
AutoPR Agent — CoderAgent

Executes the ImplementationPlan by reading existing code, generating modifications
and new test suites, validating syntax, and staging changes via the GitHub tool layer.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from autopr.agents.planner import ImplementationPlan
from autopr.config.models import get_model_client
from autopr.config.settings import get_settings
from autopr.mcp_servers import github_server
from autopr.rag.grounding import discover_and_load_brd, format_brd_for_prompt

logger = logging.getLogger("autopr.agents.coder")


class FileModification(BaseModel):
    """Represents a generated code modification for a specific file."""

    file_path: str
    action: str = "MODIFY_FILE"
    explanation: str = ""
    complete_content: str = Field(description="The complete, updated file content with all imports and code.")


class CodeChanges(BaseModel):
    """Summary of all changes produced by CoderAgent."""

    files_modified: list[str] = []
    files_created: list[str] = []
    diff: str = ""
    summary: str = ""


class CoderAgent:
    """Agent responsible for writing code and generating tests according to plan."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_client = get_model_client()

    def _clean_code_fences(self, text: str) -> str:
        """Strip markdown ```python ... ``` fences if wrapped."""
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return clean

    async def implement_plan(
        self,
        plan: ImplementationPlan,
        diagnostic_feedback: str = "",
        inject_failure: bool = False,
    ) -> CodeChanges:
        """Implement all steps in the plan and create tests.

        Args:
            plan: The structured ImplementationPlan.
            diagnostic_feedback: Optional error feedback from ReviewerAgent retry loop.
            inject_failure: If True, injects an intentional bug for demo mode.

        Returns:
            CodeChanges object with file lists and unified diff.
        """
        logger.info("CoderAgent executing plan for %s (%d steps)", plan.work_item_id, len(plan.steps))

        files_modified: list[str] = []
        files_created: list[str] = []
        brd_context = format_brd_for_prompt(discover_and_load_brd())

        # Determine target files from steps and target_files list
        targets = list(dict.fromkeys(plan.target_files + [s.file_path for s in plan.steps]))
        if not targets:
            targets = ["autopr/api/server.py"]

        for file_path in targets:
            norm_path = file_path.replace("\\", "/")
            existing_content = ""
            is_new = True

            try:
                existing_content = github_server.read_file(norm_path)
                is_new = False
            except Exception:
                is_new = True

            logger.info("CoderAgent modifying %s (is_new=%s)", norm_path, is_new)

            system_instruction = (
                "You are the CoderAgent in AutoPR. Your job is to implement code changes "
                "with surgical precision, clean architecture, and standard Python type hints.\n"
                "Rules:\n"
                "1. Always output the COMPLETE, runnable file content. Never use placeholders like '# ... rest of code'.\n"
                "2. Maintain backwards compatibility and follow existing codebase style.\n"
                "3. Preserve all imports, docstrings, and existing functions unless instructed to change them.\n"
            )

            prompt = f"""
## Plan for Work Item {plan.work_item_id}:
- **Title**: {plan.title}
- **Summary**: {plan.summary}

## Target File: `{norm_path}` ({'NEW FILE' if is_new else 'EXISTING FILE'})

{brd_context}

{'## Existing File Content:' if not is_new else ''}
```python
{existing_content if not is_new else '# New file'}
```

{'## Diagnostic Feedback from Failed Validation (Fix this bug!):' if diagnostic_feedback else ''}
{diagnostic_feedback}

{'## INTENTIONAL FAILURE DEMO MODE: Introduce a deliberate syntax or assertion error so ReviewerAgent can demonstrate self-healing.' if inject_failure else ''}

Generate the complete updated file content:
"""

            file_mod = self.model_client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=self.settings.coding_model,
                response_schema=FileModification,
            )

            content_to_write = ""
            if isinstance(file_mod, FileModification) and file_mod.complete_content:
                content_to_write = self._clean_code_fences(file_mod.complete_content)
            elif isinstance(file_mod, str):
                content_to_write = self._clean_code_fences(file_mod)
            else:
                # Retain existing content if generation was empty
                content_to_write = existing_content or f"# AutoPR created {norm_path}\n"

            # Check syntax if python file
            if norm_path.endswith(".py") and not inject_failure:
                try:
                    import ast
                    ast.parse(content_to_write)
                except SyntaxError as e:
                    logger.warning("Syntax error in generated code for %s: %s. Attempting self-correction.", norm_path, e)
                    # Attempt quick self-fix prompt
                    fix_prompt = f"Fix the SyntaxError ({e.msg} at line {e.lineno}) in this Python code and return only the corrected valid code:\n```python\n{content_to_write}\n```"
                    corrected = self.model_client.generate(prompt=fix_prompt, model=self.settings.coding_model)
                    if isinstance(corrected, str) and "def " in corrected:
                        content_to_write = self._clean_code_fences(corrected)

            # Write file to disk/git
            github_server.write_file(
                file_path=norm_path,
                content=content_to_write,
                commit_message=f"feat({plan.work_item_id.lower()}): update {norm_path}",
            )

            if is_new:
                files_created.append(norm_path)
            else:
                files_modified.append(norm_path)

        # Generate Test File if test strategy exists and tests aren't already written
        test_file_path = f"autopr/tests/test_{plan.work_item_id.lower().replace('-', '_')}.py"
        if test_file_path not in files_created and test_file_path not in files_modified:
            logger.info("CoderAgent generating test suite: %s", test_file_path)
            test_prompt = f"""
Write a comprehensive pytest test suite in `{test_file_path}` for the changes implemented for {plan.work_item_id}: {plan.title}.
Test Strategy: {plan.test_strategy}
Include at least 2 test cases (happy path and validation/edge cases).
Output the COMPLETE test file content.
"""
            test_mod = self.model_client.generate(
                prompt=test_prompt,
                model=self.settings.coding_model,
                response_schema=FileModification,
            )
            test_code = (
                test_mod.complete_content
                if isinstance(test_mod, FileModification) and test_mod.complete_content
                else f"def test_{plan.work_item_id.lower().replace('-', '_')}_placeholder():\n    assert True\n"
            )
            test_code = self._clean_code_fences(test_code)

            github_server.write_file(
                file_path=test_file_path,
                content=test_code,
                commit_message=f"test({plan.work_item_id.lower()}): add test suite for {plan.title}",
            )
            files_created.append(test_file_path)

        # Get unified git diff
        diff = github_server.get_diff()

        return CodeChanges(
            files_modified=files_modified,
            files_created=files_created,
            diff=diff,
            summary=f"Implemented {len(files_modified)} modified files and {len(files_created)} new files for {plan.work_item_id}",
        )

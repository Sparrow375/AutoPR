# AutoPR: Context-Aware Work Item to PR Agent

Software development workflows often require engineers to manually translate a work item into a code change. This involves understanding the ticket, finding the relevant parts of the codebase, retrieving project and domain context, implementing the change, writing tests, debugging failures, creating a Pull Request, and notifying the team about the status of the Work Item. These steps are spread across multiple systems and require significant manual effort and context switching.

&nbsp;

The goal is to build AutoPR, an agent that automates this workflow from a single Work Item ID.

&nbsp;

Given a Work Item ID from Notion, Linear, or Jira, the agent should:

* Fetch and interpret the work item's requirements and acceptance criteria.

* Retrieve relevant context from documentation, repository rules, coding standards, and domain knowledge.

* Identify the relevant code and tests.

* Implement the required changes, and create or update tests for the change.

* Run the relevant build, test, lint, type check, and validation workflows.

* Diagnose failures and attempt to resolve them autonomously.

* Re-run validation after making corrective changes.

* Create a GitHub Pull Request with the implementation, tests, validation results, and reference to the original work item.

* Keep the Status updated in the Work Item such as New → Assigned → Dev In Progress → Submitted for Review.

* Notify the team through Slack or Microsoft Teams with the resulting PR, and post along with a summary in the ticket comments tagging the respective QA and PM assigned.

## Expected Workflow

The solution should demonstrate an end to end flow:

&nbsp;

Work Item ID → Context Retrieval → Codebase Analysis → Implementation → Tests → Validation → Self Debugging → Pull Request → Team Notification

&nbsp;

The final Pull Request should be traceable to the original work item and provide sufficient evidence of what was changed and how it was validated.

## Expected Outcomes

The solution should demonstrate meaningful use and may include the following:

* Agent skills for repository analysis, implementation, testing, debugging, and PR creation.

* Tools for interacting with repositories, work tracking systems, communication platforms, and development environments.

* MCP servers for integrating external or custom built systems where appropriate.

* RAG pipelines for retrieving relevant documentation, repository instructions, and domain context.

* GitHub for repository operations and Pull Request creation.

* Slack or Microsoft Teams for automated team communication.

## Demonstration and Creativity

The implementation should not be limited to simply connecting APIs and showing a successful Pull Request. Any AI Agent these days can simply do most of the tasks listed above. That is where we want to see your creativity, add as many elements as possible that are unavailable out-of-the-box from existing Agents.

&nbsp;

Teams are encouraged to creatively demonstrate how their agent reasons through and executes the workflow. The demonstration should make the agent's capabilities, context retrieval, decision making, debugging process, and final outcome easy to understand.

&nbsp;

Creative approaches could include:

* A representation of the agent's workflow and tool interactions.

* Demonstrating how retrieved context changes the implementation.

* Intentionally introducing a build or test failure and showing the agent diagnose and fix it.

* Showing how the agent handles ambiguous requirements or missing context.

* A way to show execution progress, retrieved context, validation results, and PR status.

* Any other approach that clearly demonstrates the value and technical depth of the solution.

Creativity should be used to communicate the engineering behind the solution, not as a substitute for a working implementation.

## Success Criteria

A successful solution should demonstrate that AutoPR can take a valid Work Item ID and drive the development workflow through implementation, testing, validation, Pull Request creation, and team notification with minimal human intervention.

&nbsp;

The demonstration should also clearly show:

* How different the Agent works from Out-of-the-box features.

* How the Agent is able to fetch the data live, not hardcoded.

* Able to adapt to new knowledge, such as coding rules, or BRDs (A document will be given during review, and it should respect the instructions without explicitly hardcoding them somewhere).

* How changes are validated, not hallucinated (The ReAct Loop).

* How it responds to failures, and takes input IF NEEDED.

* How the status updates regularly and the team is notified of the end result.

The solution will be evaluated on both technical execution and the clarity and creativity with which the solution is demonstrated.

## Note

1. You can choose Notion or any work management alternative to demonstrate that is free and open to use. The names mentioned are for example purposes.

2. The steps such as tests, linting, validations, etc SHOULD respect the repo rules. They should only be created (or updated) ONLY when the org wide practices allow.

&nbsp;

&nbsp;

&nbsp;
# AutoPR — Context-Aware Work Item to Pull Request Agent

AutoPR is an autonomous multi-agent engineering assistant powered by Google ADK 2.0 and Gemini models. Given a work item ticket (from Linear or GitHub Issues), AutoPR investigates codebase context via RAG, plans modifications, writes code and tests, validates through a self-healing ReAct loop, creates a Pull Request with rich summaries, and dispatches team notifications.

## Architecture

- **ADK Multi-Agent Core**: Orchestrator, Planner, Coder, Reviewer, and Notifier agents.
- **Model Context Protocol (MCP)**: GitHub, Linear, Discord, and Code Execution tool servers.
- **RAG Engine**: Codebase indexing & semantic retrieval with ChromaDB and search grounding.
- **FastAPI + WebSocket Gateway**: Real-time event streaming and REST control.
- **Next.js Dashboard**: Live visual pipeline graph, confidence scoring, diff preview, and failure demo controls.

# AutoPR - Project Context

## Project Overview
AutoPR is a **Context-Aware Work Item to Pull Request Agent** built for a hackathon. Given a Work Item ID from a task tracker, the agent autonomously:
1. Fetches and interprets the ticket's requirements
2. Retrieves context from docs, repo rules, coding standards via RAG
3. Identifies relevant code, tests, and active BRD constraints
4. Implements changes + creates/updates tests
5. Runs build/test/lint validation
6. Diagnoses and fixes failures (self-healing ReAct loop)
7. Creates a GitHub Pull Request with rich natural language descriptions
8. Updates ticket status in Linear / GitHub Issues
9. Notifies team via Discord webhooks with rich embeds

## Architecture Decisions

| Decision | Choice |
|---|---|
| **Framework** | Google ADK 2.0 (Python) |
| **Work Item Tracker** | Linear (primary) + GitHub Issues (adapter) + Demo Mock Store |
| **Frontend** | Custom Next.js Dashboard + WebSocket + A2UI |
| **Agent Architecture** | Multi-agent hierarchy (Orchestrator → Planner, Coder, Reviewer, Notifier) |
| **Models** | Gemini 3.5 Flash-Lite / 3.1 Flash-Lite (primary, Google AI Studio Free Tier compliant) + optional local LLM (Ollama/Gemma) |
| **Notifications** | Discord (webhooks) |
| **RAG Strategy** | ChromaDB in-memory (local ONNX embeddings for zero rate-limit impact) + BRD grounding |
| **MCP Servers** | GitHub, Linear, Discord, Code Execution (sandboxed) |
| **Team Split** | Person A: Backend (agents, MCP, RAG, API) / Person B: Frontend (Next.js, A2UI, visualizations) |
| **Visual Theme** | Light professional (Linear/Notion-inspired) |
| **Demo Target** | This AutoPR repo itself (meta, self-referential) |
| **Project Structure** | Python monorepo with /agents, /mcp_servers, /tools, /rag, /api + /dashboard |

## Innovation Features (All 7 Implemented in Backend)
1. 🎬 **Live Agent Workflow Visualization** — Orchestrator emits typed WebSocket events for every step, tool call, reasoning thought, and code diff.
2. 🧠 **Confidence Scoring & Human-in-the-Loop** — PlannerAgent computes confidence score (0.0 to 1.0); if <0.7, emits `human_input_needed` event with A2UI payload.
3. 🔄 **Intentional Failure Demo Mode** — `/api/demo/failure` injects a deliberate bug, ReviewerAgent detects it and coordinates self-healing ReAct loop with CoderAgent.
4. 📝 **BRD Injection Demo** — `/api/demo/brd` dynamically ingests project specifications/BRDs and enforces business rules.
5. 🔍 **Code Diff Preview** — CoderAgent generates unified git diffs emitted via `code_changes` event.
6. 💬 **Natural Language PR Summary** — NotifierAgent generates human-grade PR summaries mapping changes directly to ticket acceptance criteria.
7. 🔔 **Smart Escalation** — If ReviewerAgent exceeds max retries, autonomously creates a labeled GitHub issue with debug logs and alerts the team.

## Project Structure
```
autopr/
├── agents/          # ADK agents (orchestrator, planner, coder, reviewer, notifier)
├── mcp_servers/     # MCP 2.0 servers (github, linear, discord, executor)
├── tools/           # Shared tools, exception hierarchy
├── rag/             # RAG pipeline (indexer, retriever, grounding/BRD)
├── api/             # FastAPI REST + WebSocket gateway (server, events)
├── config/          # Central Settings (Pydantic), ModelClient
└── tests/           # Full pytest test suite (mcp, rag, pipeline)
dashboard/           # Next.js frontend (Person B workspace)
```

## Technology Stack
- **Backend**: Python 3.13+, Google ADK 2.0, FastAPI, ChromaDB, PyGithub, Uvicorn, WebSockets
- **Frontend**: Next.js 14+, TypeScript, WebSocket, A2UI renderer
- **APIs**: Linear GraphQL API, GitHub REST/GraphQL API, Discord Webhooks
- **Models**: Gemini 3.5 Flash-Lite / 3.1 Flash-Lite via Google AI Studio, optional Ollama for local LLMs
- **Protocol**: MCP (Model Context Protocol 2.0) for tool servers

## Implementation Status (Person A - Backend: COMPLETE)
- [x] Python 3.13 virtual environment with all core and dev dependencies installed
- [x] 4 MCP tool servers fully operational with both remote and local fallbacks
- [x] In-memory RAG pipeline with AST chunking, local ONNX embeddings, and BRD ingestion
- [x] Multi-agent hierarchy: Orchestrator, Planner, Coder, Reviewer, Notifier
- [x] Self-healing ReAct retry loop with smart escalation
- [x] FastAPI REST endpoints + WebSocket streaming gateway (`/ws/events`)
- [x] 20/20 unit and integration tests passing (`pytest autopr/tests`)
- [x] Clean Ruff linting passing across entire project

## Git Info
- **Repository**: Sparrow375/AutoPR
- **Branch Strategy**: main (stable), dev (development), feat/* (per-feature)
- **Active Branches**: `feat/backend-core` (Person A), `feat/frontend-dashboard-layout` (Person B)
- **Integration Status**: Merged backend + frontend implementations

## Implementation Status
- **Person A (Backend)**: COMPLETE — MCP servers, RAG pipeline, ADK agents, FastAPI REST + WebSocket gateway, 20/20 pytest pass.
- **Person B (Frontend)**: COMPLETE — Next.js 14 App Router, UI primitives, WorkflowGraph, LiveLog, ConfidenceMeter, CodeDiffPreview, A2UIRenderer, WebSocket client, REST client.

## Key Files for Sync
- `CONTRIBUTING.md` — Full ground rules, conventions, directory ownership
- `autopr/api/events.py` — **SHARED CONTRACT** (Python source of truth)
- `dashboard/src/lib/types.ts` — **SHARED CONTRACT** (TypeScript mirror)
- `dashboard/src/lib/mockEvents.ts` — Mock data for frontend development
- `autopr/config/settings.py` — Central configuration
- `autopr/tools/exceptions.py` — Exception hierarchy

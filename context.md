# AutoPR - Project Context

## Project Overview
AutoPR is a **Context-Aware Work Item to Pull Request Agent** built for a hackathon. Given a Work Item ID from a task tracker, the agent autonomously:
1. Fetches and interprets the ticket's requirements
2. Retrieves context from docs, repo rules, coding standards
3. Identifies relevant code and tests
4. Implements changes + creates/updates tests
5. Runs build/test/lint validation
6. Diagnoses and fixes failures (ReAct loop)
7. Creates a GitHub Pull Request
8. Updates ticket status
9. Notifies team via Discord

## Architecture Decisions (Finalized)

| Decision | Choice |
|---|---|
| **Framework** | Google ADK 2.0 (Python) |
| **Work Item Tracker** | Linear (primary) + GitHub Issues (adapter) |
| **Frontend** | Custom Next.js Dashboard + WebSocket + A2UI |
| **Agent Architecture** | Multi-agent hierarchy (Orchestrator → Planner, Coder, Reviewer, Notifier) |
| **Models** | Gemini 2.5 Pro (primary) + Gemini 2.5 Flash (simpler tasks) + optional local LLM (Ollama/Gemma) |
| **Notifications** | Discord (webhooks) |
| **RAG Strategy** | ChromaDB in-memory + Google Search grounding |
| **MCP Servers** | GitHub, Linear, Discord, Code Execution (sandboxed) |
| **Team Split** | Person A: Backend (agents, MCP, RAG) / Person B: Frontend (Next.js, A2UI, visualizations) |
| **Visual Theme** | Light professional (Linear/Notion-inspired) |
| **Demo Target** | This AutoPR repo itself (meta, self-referential) |
| **Project Structure** | Python monorepo with /agents, /mcp_servers, /tools, /rag, /api + /dashboard |

## Innovation Features (7 selected)
1. 🎬 **Live Agent Workflow Visualization** — animated pipeline graph with real-time tool calls & reasoning
2. 🧠 **Confidence Scoring & Human-in-the-Loop** — agent self-rates confidence; low-confidence triggers A2UI approval dialog
3. 🔄 **Intentional Failure Demo Mode** — demo button injects a bug, agent diagnoses and fixes it live
4. 📝 **BRD Injection Demo** — drop a new BRD doc into repo, agent adapts implementation
5. 🔍 **Code Diff Preview** — rich side-by-side diff in dashboard before PR creation
6. 💬 **Natural Language PR Summary** — human-quality PR description explaining what/why/how
7. 🔔 **Smart Escalation** — after N retries, creates documented "help wanted" issue with debugging context

## Project Structure
```
autopr/
├── agents/          # ADK agents (orchestrator, planner, coder, reviewer, notifier)
├── mcp_servers/     # MCP server implementations (github, linear, discord, executor)
├── tools/           # Shared ADK tools/functions
├── rag/             # RAG pipeline (ChromaDB indexing, retrieval)
├── api/             # FastAPI + WebSocket server
├── config/          # Configuration, env vars
└── tests/
dashboard/           # Next.js frontend (separate directory)
├── src/
└── ...
```

## Technology Stack
- **Backend**: Python 3.11+, Google ADK 2.0, FastAPI, ChromaDB, PyGithub
- **Frontend**: Next.js 14+, TypeScript, WebSocket, A2UI renderer
- **APIs**: Linear GraphQL API, GitHub REST/GraphQL API, Discord Webhooks
- **Models**: Gemini 2.5 Pro/Flash via Google AI Studio, optional Ollama for local LLMs
- **Protocol**: MCP (Model Context Protocol) for tool servers

## Git Info
- **Repository**: Sparrow375/AutoPR
- **Branch Strategy**: main (stable), dev (development), feature/* (per-feature)
- **Status**: Fresh repo, no commits yet

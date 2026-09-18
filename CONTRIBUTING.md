# AutoPR — Contributing Guide & Ground Rules

> **Read this fully before writing any code.** This document ensures both team members (Person A: Backend, Person B: Frontend) stay synchronized.

---

## Table of Contents

1. [Git Workflow](#1-git-workflow)
2. [Branch Naming](#2-branch-naming)
3. [Commit Messages](#3-commit-messages)
4. [Pull Request Conventions](#4-pull-request-conventions)
5. [Directory Ownership](#5-directory-ownership)
6. [Backend Conventions (Python)](#6-backend-conventions-python)
7. [Frontend Conventions (TypeScript/Next.js)](#7-frontend-conventions-typescriptnextjs)
8. [API Contract Rules](#8-api-contract-rules)
9. [Environment & Secrets](#9-environment--secrets)
10. [Error Handling](#10-error-handling)
11. [Logging](#11-logging)
12. [Testing](#12-testing)
13. [Configuration](#13-configuration)
14. [Communication Protocol](#14-communication-protocol)

---

## 1. Git Workflow

```
main          ← production-ready, never commit directly
  └── dev     ← integration branch, both merge here
       ├── feat/backend-*    ← Person A's feature branches
       └── feat/frontend-*   ← Person B's feature branches
```

### Rules
- **Never push directly to `main` or `dev`.** Always create a feature branch and merge via PR (or fast-forward merge after review).
- **Pull from `dev` before starting new work.** Always `git pull origin dev` before branching.
- **Resolve conflicts in your feature branch**, not in `dev`.
- **Keep branches short-lived.** Merge at least once a day to avoid divergence.

### Daily Sync Workflow
```bash
# Start of work
git checkout dev
git pull origin dev
git checkout -b feat/backend-mcp-github   # or feat/frontend-workflow-graph

# End of work
git add .
git commit -m "feat(mcp): implement GitHub MCP server"
git push origin feat/backend-mcp-github
# Then merge into dev (via PR or direct merge)
```

---

## 2. Branch Naming

Format: `feat/<scope>-<short-description>`

| Person | Prefix Examples |
|--------|----------------|
| Person A (Backend) | `feat/backend-agents`, `feat/backend-mcp-github`, `feat/backend-rag-indexer` |
| Person B (Frontend) | `feat/frontend-dashboard-layout`, `feat/frontend-workflow-graph`, `feat/frontend-websocket` |
| Shared | `feat/shared-event-schema`, `fix/shared-api-contract` |

Other prefixes:
- `fix/` — bug fixes
- `docs/` — documentation only
- `chore/` — tooling, config, dependencies

---

## 3. Commit Messages

We use **Conventional Commits** (enforced by convention, not tooling — keep it simple for a hackathon).

### Format
```
<type>(<scope>): <description>

[optional body]
```

### Types
| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `docs` | Documentation only |
| `style` | Formatting, missing semicolons, etc. (not CSS) |
| `test` | Adding or fixing tests |
| `chore` | Build config, dependencies, tooling |

### Scopes
| Scope | Meaning |
|-------|---------|
| `agents` | Agent code (orchestrator, planner, coder, reviewer, notifier) |
| `mcp` | MCP server code |
| `rag` | RAG pipeline |
| `api` | FastAPI / WebSocket server |
| `config` | Configuration |
| `dashboard` | Next.js frontend |
| `ui` | UI components |
| `ws` | WebSocket client/events |

### Examples
```
feat(agents): implement PlannerAgent with RAG retrieval
feat(mcp): add GitHub MCP server with PR creation tool
feat(dashboard): add WorkflowGraph component with reactflow
fix(api): handle WebSocket disconnect gracefully
docs(readme): add setup instructions
chore(deps): add chromadb to pyproject.toml
```

---

## 4. Pull Request Conventions

- **Title**: Same as commit message format — `feat(scope): description`
- **Body**: Brief description of what changed and why
- **Keep PRs small** — one feature per PR when possible
- **Tag the other person** for awareness (not full review — hackathon speed)

---

## 5. Directory Ownership

This is **critical** to avoid merge conflicts. Each person owns specific directories.

```
autopr/                    ← PERSON A owns everything below
├── agents/                ← Person A ONLY
├── mcp_servers/           ← Person A ONLY
├── tools/                 ← Person A ONLY
├── rag/                   ← Person A ONLY
├── api/                   ← Person A ONLY (but Person B should review event schema)
├── config/                ← Person A ONLY
└── tests/                 ← Person A ONLY

dashboard/                 ← PERSON B owns everything below
├── src/
│   ├── app/               ← Person B ONLY
│   ├── components/        ← Person B ONLY
│   ├── lib/               ← Person B ONLY
│   └── styles/            ← Person B ONLY
├── public/                ← Person B ONLY
└── package.json           ← Person B ONLY

# SHARED files (coordinate before editing)
├── context.md             ← Both can update (append only, don't rewrite)
├── CONTRIBUTING.md        ← Both (coordinate)
├── README.md              ← Both (coordinate)
├── .env.example           ← Both (append your vars, don't remove others')
├── .gitignore             ← Both (append only)
└── autopr/api/events.py   ← SHARED CONTRACT (see Section 8)
```

### Golden Rule
> **If a file is in the other person's directory, do NOT edit it.** Open a quick message/issue instead.

---

## 6. Backend Conventions (Python)

### Python Version
- **Python 3.11+** required

### Style
- **Formatter**: `ruff format` (line length 88, double quotes)
- **Linter**: `ruff check`
- **Type hints**: Required on all function signatures. Use `from __future__ import annotations`.
- **Docstrings**: Google-style docstrings on all public functions/classes.

```python
from __future__ import annotations

def fetch_work_item(item_id: str, *, include_comments: bool = False) -> WorkItem:
    """Fetch a work item from the configured tracker.

    Args:
        item_id: The work item identifier (e.g., "AUT-123").
        include_comments: Whether to include issue comments.

    Returns:
        A WorkItem object with parsed requirements.

    Raises:
        WorkItemNotFoundError: If the item ID doesn't exist.
    """
```

### Naming
| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `snake_case.py` | `planner_agent.py` |
| Classes | `PascalCase` | `PlannerAgent`, `GitHubMCPServer` |
| Functions | `snake_case` | `fetch_work_item()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS` |
| Private | `_leading_underscore` | `_parse_response()` |
| Pydantic models | `PascalCase` | `ImplementationPlan` |
| ADK Agents | `PascalCase` + "Agent" suffix | `PlannerAgent` |
| MCP Tools | `snake_case` verb phrases | `create_pull_request` |

### Imports
Order (enforced by ruff):
1. Standard library
2. Third-party packages
3. Local imports

```python
import os
from datetime import datetime

from fastapi import FastAPI
from google.adk import Agent
from pydantic import BaseModel

from autopr.config.settings import Settings
from autopr.tools.github import create_branch
```

### Async Convention
- **FastAPI routes**: Always `async def`
- **ADK tools**: Follow ADK conventions (typically sync with `@tool` decorator)
- **MCP servers**: Follow MCP protocol conventions
- **HTTP calls**: Use `httpx.AsyncClient` (not `requests`)

### Pydantic Models
All data flowing between agents or across the API must be a Pydantic model:

```python
from pydantic import BaseModel, Field

class ImplementationPlan(BaseModel):
    """Output from PlannerAgent consumed by CoderAgent."""
    
    work_item_id: str
    title: str
    files_to_modify: list[FileChange]
    files_to_create: list[FileChange]
    test_strategy: str
    relevant_context: list[ContextSnippet]
    confidence_score: float = Field(ge=0.0, le=1.0)
```

---

## 7. Frontend Conventions (TypeScript/Next.js)

### Framework
- **Next.js 14+** with App Router
- **TypeScript** (strict mode)
- **No Tailwind** — use vanilla CSS (CSS Modules)

### Style
- **Formatter**: Prettier (defaults)
- **Linter**: ESLint (Next.js config)

### Naming
| Thing | Convention | Example |
|-------|-----------|---------|
| Files (components) | `PascalCase.tsx` | `WorkflowGraph.tsx` |
| Files (utilities) | `camelCase.ts` | `websocket.ts` |
| Files (styles) | `ComponentName.module.css` | `WorkflowGraph.module.css` |
| Components | `PascalCase` | `WorkflowGraph` |
| Hooks | `use` prefix | `useWebSocket`, `usePipelineEvents` |
| Types/Interfaces | `PascalCase` | `PipelineEvent`, `StageStatus` |
| Constants | `UPPER_SNAKE_CASE` | `WS_RECONNECT_DELAY` |
| CSS classes | `camelCase` in modules | `.stageNode`, `.activeState` |
| Props interfaces | `ComponentNameProps` | `WorkflowGraphProps` |

### Component Structure
```tsx
// WorkflowGraph.tsx
import { FC } from 'react';
import styles from './WorkflowGraph.module.css';
import { PipelineEvent, StageStatus } from '@/lib/types';

interface WorkflowGraphProps {
  stages: StageStatus[];
  currentStage: string | null;
  onStageClick?: (stage: string) => void;
}

export const WorkflowGraph: FC<WorkflowGraphProps> = ({
  stages,
  currentStage,
  onStageClick,
}) => {
  // ...
};
```

### Directory Layout
```
dashboard/src/
├── app/
│   ├── page.tsx                  # Home / main dashboard
│   ├── layout.tsx                # Root layout with providers
│   ├── globals.css               # Global styles + CSS variables
│   └── run/
│       └── [id]/
│           └── page.tsx          # Pipeline run detail
├── components/
│   ├── WorkflowGraph.tsx         # Pipeline visualization
│   ├── WorkflowGraph.module.css
│   ├── LiveLog.tsx               # Real-time log stream
│   ├── CodeDiffPreview.tsx       # Side-by-side diff
│   ├── ConfidenceMeter.tsx       # Confidence gauge
│   ├── A2UIRenderer.tsx          # A2UI component renderer
│   └── ui/                       # Reusable primitives
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Badge.tsx
│       └── ...
├── lib/
│   ├── types.ts                  # Shared TypeScript types
│   ├── websocket.ts              # WebSocket client hook
│   ├── api.ts                    # REST API client
│   └── constants.ts              # Shared constants
└── styles/
    └── tokens.css                # Design tokens (colors, spacing, fonts)
```

---

## 8. API Contract Rules

> [!IMPORTANT]
> **The WebSocket event schema is the single most important shared contract.** Both people depend on it. Changes to it require coordination.

### The Canonical Event Schema

**File**: `autopr/api/events.py` (Python) ↔ `dashboard/src/lib/types.ts` (TypeScript)

These two files must stay **perfectly in sync**. When one changes, the other must change too.

#### Python (source of truth)
```python
# autopr/api/events.py
from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Any

class EventType(str, Enum):
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

class Stage(str, Enum):
    FETCHING = "fetching"
    PLANNING = "planning"
    CODING = "coding"
    REVIEWING = "reviewing"
    NOTIFYING = "notifying"

class PipelineEvent(BaseModel):
    run_id: str
    timestamp: datetime
    event_type: EventType
    stage: Stage | None = None
    data: dict[str, Any] = {}
```

#### TypeScript (mirror — must match exactly)
```typescript
// dashboard/src/lib/types.ts
export type EventType =
  | "pipeline_started"
  | "stage_started"
  | "stage_completed"
  | "tool_called"
  | "reasoning"
  | "confidence_update"
  | "human_input_needed"
  | "human_input_received"
  | "error"
  | "retry_started"
  | "code_changes"
  | "validation_result"
  | "pr_created"
  | "pipeline_completed";

export type Stage =
  | "fetching"
  | "planning"
  | "coding"
  | "reviewing"
  | "notifying";

export interface PipelineEvent {
  run_id: string;
  timestamp: string;  // ISO 8601
  event_type: EventType;
  stage: Stage | null;
  data: Record<string, any>;
}
```

### Event Data Payloads

Each `event_type` has a specific `data` shape. Both sides must agree:

| Event Type | `data` Shape |
|---|---|
| `pipeline_started` | `{ work_item_id: string, title: string, source: "linear" \| "github" }` |
| `stage_started` | `{ stage: Stage }` |
| `stage_completed` | `{ stage: Stage, duration_ms: number, result_summary: string }` |
| `tool_called` | `{ tool_name: string, args: object, result: any, duration_ms: number }` |
| `reasoning` | `{ thought: string, agent: string }` |
| `confidence_update` | `{ score: number, threshold: number, agent: string }` |
| `human_input_needed` | `{ prompt: string, options: string[], a2ui_payload?: object }` |
| `human_input_received` | `{ response: string }` |
| `error` | `{ message: string, stage: Stage, recoverable: boolean, stack_trace?: string }` |
| `retry_started` | `{ attempt: number, max_attempts: number, reason: string }` |
| `code_changes` | `{ files: Array<{ path: string, action: "create" \| "modify" \| "delete", diff: string }> }` |
| `validation_result` | `{ checks: Array<{ name: string, status: "pass" \| "fail" \| "skip", output: string }> }` |
| `pr_created` | `{ url: string, number: number, title: string, summary: string, branch: string }` |
| `pipeline_completed` | `{ success: boolean, pr_url: string \| null, duration_ms: number, stages_completed: string[] }` |

### REST API Endpoints

| Method | Path | Description | Person |
|--------|------|-------------|--------|
| `POST` | `/api/run` | Start pipeline `{ work_item_id, source }` → `{ run_id }` | A builds, B consumes |
| `GET` | `/api/runs` | List all runs → `{ runs: RunSummary[] }` | A builds, B consumes |
| `GET` | `/api/runs/{run_id}` | Get run detail → `{ run: RunDetail }` | A builds, B consumes |
| `POST` | `/api/demo/inject-failure` | Inject bug `{ run_id }` | A builds, B consumes |
| `POST` | `/api/demo/inject-brd` | Inject BRD `{ run_id, brd_content }` | A builds, B consumes |
| `WS` | `/ws/{run_id}` | Real-time event stream | A builds, B consumes |

### Change Process for API Contract
1. Person who needs the change **proposes** it in a message/issue
2. **Both agree** on the new shape
3. Person A updates `autopr/api/events.py`
4. Person B updates `dashboard/src/lib/types.ts`
5. Both commit with `feat(shared): update event schema - <description>`

---

## 9. Environment & Secrets

### `.env` File Rules
- **Never commit `.env`** — it's in `.gitignore`
- **Always update `.env.example`** when adding a new variable
- **Prefix variables** by domain:

```bash
# Google / Gemini
GEMINI_API_KEY=

# Linear
LINEAR_API_KEY=

# GitHub
GITHUB_TOKEN=
GITHUB_REPO_OWNER=
GITHUB_REPO_NAME=

# Discord
DISCORD_WEBHOOK_URL=

# Optional - Local LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3

# Server
API_HOST=0.0.0.0
API_PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Frontend Env Vars
Next.js requires `NEXT_PUBLIC_` prefix for client-side env vars. Only `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` are used client-side.

---

## 10. Error Handling

### Backend
- **Never swallow exceptions silently.** Always log and re-raise or handle.
- **Custom exception classes** for each domain:

```python
# autopr/tools/exceptions.py
class AutoPRError(Exception):
    """Base exception for all AutoPR errors."""

class WorkItemNotFoundError(AutoPRError):
    """Raised when a work item ID doesn't exist."""

class ValidationFailedError(AutoPRError):
    """Raised when code validation (test/lint/build) fails."""

class MCPConnectionError(AutoPRError):
    """Raised when an MCP server can't be reached."""

class RateLimitError(AutoPRError):
    """Raised when an API rate limit is hit."""
```

- **API responses**: Always return structured errors:
```json
{
  "error": true,
  "code": "WORK_ITEM_NOT_FOUND",
  "message": "Linear issue AUT-999 not found",
  "details": {}
}
```

### Frontend
- **Every API call** must have error handling (try/catch or `.catch()`)
- **Show user-friendly error messages** — never raw stack traces
- **WebSocket disconnects** must show a reconnecting indicator, not crash

---

## 11. Logging

### Backend
Use Python's `logging` module with structured format:

```python
import logging

logger = logging.getLogger(__name__)

# Levels:
# DEBUG   - Tool call args/responses, ChromaDB queries
# INFO    - Stage transitions, agent delegations, PR created
# WARNING - Retries, low confidence, rate limit approaching
# ERROR   - Failures, exceptions, MCP server unreachable
```

Naming convention: logger name = module name (via `__name__`).

Every log that goes to WebSocket should **also** go to Python logging.

### Frontend
Use `console` levels consistently:
- `console.info` — WebSocket events, route changes
- `console.warn` — Reconnect attempts, missing data
- `console.error` — API failures, render errors

---

## 12. Testing

### Backend (`autopr/tests/`)
- **Framework**: `pytest`
- **Test file naming**: `test_<module>.py` (e.g., `test_planner_agent.py`)
- **Fixtures** in `conftest.py`
- **Mock external APIs** — never hit real Linear/GitHub/Discord in tests
- **Minimum coverage target**: Core agents and MCP tools should have at least one happy-path and one error-path test each

```
autopr/tests/
├── conftest.py                  # Shared fixtures
├── test_orchestrator_agent.py
├── test_planner_agent.py
├── test_coder_agent.py
├── test_reviewer_agent.py
├── test_notifier_agent.py
├── mcp/
│   ├── test_github_server.py
│   ├── test_linear_server.py
│   ├── test_discord_server.py
│   └── test_executor_server.py
├── test_rag_indexer.py
├── test_rag_retriever.py
└── test_api_server.py
```

### Frontend (`dashboard/`)
- **Linting**: `npm run lint`
- **Build check**: `npm run build` (type errors caught here)
- **No unit tests required** for hackathon — focus on working demo
- **Manual testing**: Always test with the real WebSocket connection

---

## 13. Configuration

### Backend Config Hierarchy
```
Env var (.env) → Settings class → Agent config
```

All config goes through `autopr/config/settings.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    linear_api_key: str
    github_token: str
    discord_webhook_url: str
    
    # Defaults
    default_model: str = "gemini-2.5-flash"
    planning_model: str = "gemini-2.5-pro"
    max_retry_attempts: int = 3
    confidence_threshold: float = 0.7
    
    class Config:
        env_file = ".env"
```

**Never hardcode** API keys, URLs, or model names in agent/tool code. Always read from `Settings`.

### Frontend Config
All external URLs come from `NEXT_PUBLIC_*` env vars:
```typescript
// dashboard/src/lib/constants.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
```

---

## 14. Communication Protocol

### How to Stay Synced

Since you're working in parallel, follow these rules:

1. **Daily standup** (async or sync): What you did, what you're doing, any blockers
2. **API contract changes**: Always notify the other person BEFORE changing event schema
3. **Merge into `dev` at least once per day** to catch integration issues early
4. **If stuck for > 30 minutes**: Ask the other person or pivot to a different task

### Mock Data for Frontend Development

Person B can start building the dashboard **immediately** without waiting for Person A's backend, using mock WebSocket events:

```typescript
// dashboard/src/lib/mockEvents.ts
export const MOCK_EVENTS: PipelineEvent[] = [
  {
    run_id: "run-001",
    timestamp: new Date().toISOString(),
    event_type: "pipeline_started",
    stage: null,
    data: { work_item_id: "AUT-42", title: "Add rate limiting", source: "linear" },
  },
  {
    run_id: "run-001",
    timestamp: new Date().toISOString(),
    event_type: "stage_started",
    stage: "planning",
    data: {},
  },
  // ... more mock events
];
```

### Running the Full Stack Locally

```bash
# Terminal 1 — Backend
cd autopr
python -m autopr.api.server  # Runs on :8000

# Terminal 2 — Frontend
cd dashboard
npm run dev                   # Runs on :3000
```

---

## Quick Reference Card

| Question | Answer |
|----------|--------|
| How do I name my branch? | `feat/backend-*` or `feat/frontend-*` |
| How do I format my commit? | `feat(scope): description` |
| Can I edit the other person's files? | **No.** Notify them instead. |
| Where do API keys go? | `.env` file (never committed) |
| What if I need a new WebSocket event? | Propose it → both agree → both update |
| What if I need a new REST endpoint? | Person A adds it → tells Person B the shape |
| What model do I use for agent X? | Check `config/settings.py` — never hardcode |
| How do I run tests? | `pytest tests/` (backend) or `npm run build` (frontend) |
| What do I do if I'm stuck? | Ask your teammate after 30 minutes |

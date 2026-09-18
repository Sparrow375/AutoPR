"""
AutoPR API Server — FastAPI & WebSocket Gateway

Provides REST endpoints for triggering runs, demo modes, and approvals,
along with real-time WebSocket event broadcasting to the Next.js dashboard.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from autopr.agents.orchestrator import OrchestratorAgent
from autopr.api.events import (
    PipelineEvent,
    StartPipelineRequest,
    StartPipelineResponse,
    WorkItemSource,
)
from autopr.config.settings import get_settings

logger = logging.getLogger("autopr.api.server")

app = FastAPI(
    title="AutoPR API",
    description="Context-Aware Work Item to Pull Request Agent Gateway",
    version="0.1.0",
)

# Enable CORS for Next.js dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manages active WebSocket connections from frontend dashboards."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected (%d total)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected (%d remaining)", len(self.active_connections))

    async def broadcast_event(self, event: PipelineEvent) -> None:
        """Broadcast a pipeline event to all connected WebSocket clients."""
        payload = event.to_ws_message()
        disconnected: list[WebSocket] = []
        for ws in self.active_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws)


manager = ConnectionManager()

# Active runs store
RUNS_STORE: dict[str, dict[str, Any]] = {}


class ApprovalRequest(BaseModel):
    run_id: str
    approved: bool
    feedback: str = ""


class DemoRequest(BaseModel):
    work_item_id: str = "ENG-101"
    source: WorkItemSource = WorkItemSource.LINEAR


@app.get("/health")
@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "AutoPR", "version": "0.1.0"}


@app.websocket("/ws")
@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket streaming endpoint for real-time dashboard visualization."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive client messages (e.g. human input)
            data = await websocket.receive_text()
            logger.debug("Received WebSocket message: %s", data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug("WebSocket error: %s", e)
        manager.disconnect(websocket)


async def _run_pipeline_task(
    run_id: str,
    work_item_id: str,
    source: WorkItemSource,
    inject_failure: bool = False,
    custom_instructions: str = "",
) -> None:
    """Background task runner for orchestrator."""
    RUNS_STORE[run_id] = {
        "run_id": run_id,
        "work_item_id": work_item_id,
        "status": "running",
        "inject_failure": inject_failure,
    }

    orchestrator = OrchestratorAgent(event_emitter=manager.broadcast_event)
    result = await orchestrator.run(
        work_item_id=work_item_id,
        source=source,
        inject_failure=inject_failure,
        custom_instructions=custom_instructions,
        run_id=run_id,
    )

    RUNS_STORE[run_id].update(result)
    RUNS_STORE[run_id]["status"] = "completed" if result.get("success") else "failed"


@app.post("/api/run", response_model=StartPipelineResponse)
@app.post("/api/pipeline/start", response_model=StartPipelineResponse)
async def start_pipeline(request: StartPipelineRequest) -> StartPipelineResponse:
    """Start autonomous pipeline for a given work item ID."""
    if not request.work_item_id or not request.work_item_id.strip():
        raise HTTPException(status_code=400, detail="work_item_id cannot be empty")

    import uuid
    run_id = f"run-{uuid.uuid4().hex[:8]}"

    # Run in background so API responds immediately
    asyncio.create_task(
        _run_pipeline_task(
            run_id=run_id,
            work_item_id=request.work_item_id.strip(),
            source=request.source,
        )
    )

    return StartPipelineResponse(run_id=run_id, status="started")


@app.get("/api/runs/{run_id}")
async def get_run_status(run_id: str) -> dict[str, Any]:
    """Query state and details of a pipeline run."""
    run = RUNS_STORE.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.post("/api/demo/failure", response_model=StartPipelineResponse)
async def trigger_failure_demo(request: DemoRequest) -> StartPipelineResponse:
    """Intentional Failure Demo Mode: Injects a deliberate bug to show self-healing ReAct loop."""
    import uuid
    run_id = f"demo-fail-{uuid.uuid4().hex[:8]}"

    asyncio.create_task(
        _run_pipeline_task(
            run_id=run_id,
            work_item_id=request.work_item_id,
            source=request.source,
            inject_failure=True,
        )
    )

    return StartPipelineResponse(run_id=run_id, status="started (failure demo mode)")


@app.post("/api/demo/brd", response_model=StartPipelineResponse)
async def trigger_brd_demo(request: DemoRequest) -> StartPipelineResponse:
    """BRD Injection Demo Mode: Adapts implementation to newly injected Business Requirements Document."""
    import uuid
    run_id = f"demo-brd-{uuid.uuid4().hex[:8]}"

    asyncio.create_task(
        _run_pipeline_task(
            run_id=run_id,
            work_item_id=request.work_item_id,
            source=request.source,
            custom_instructions="Strictly enforce BRD compliance rules and add BRD traceability headers.",
        )
    )

    return StartPipelineResponse(run_id=run_id, status="started (BRD demo mode)")


@app.post("/api/pipeline/approve")
async def approve_plan(request: ApprovalRequest) -> dict[str, Any]:
    """Human-in-the-Loop approval callback for low-confidence plans."""
    logger.info("Human approval response for %s: approved=%s", request.run_id, request.approved)
    return {"status": "ok", "run_id": request.run_id, "approved": request.approved}


def start() -> None:
    """Entry point for CLI or local development runner."""
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    start()

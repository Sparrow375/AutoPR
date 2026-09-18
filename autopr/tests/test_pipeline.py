"""
Integration tests for AutoPR FastAPI Server, WebSocket Events, and Pipeline.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from autopr.api.events import EventType, PipelineEvent, Stage
from autopr.api.server import app


def test_api_health_endpoint() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "AutoPR"


def test_api_start_pipeline_validation() -> None:
    client = TestClient(app)
    # Empty work item id should fail with 400 or 422
    resp = client.post("/api/run", json={"work_item_id": "", "source": "linear"})
    assert resp.status_code in (400, 422)


def test_api_start_pipeline_success() -> None:
    client = TestClient(app)
    resp = client.post("/api/run", json={"work_item_id": "ENG-101", "source": "linear"})
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["status"] == "started"


def test_api_demo_failure_endpoint() -> None:
    client = TestClient(app)
    resp = client.post("/api/demo/failure", json={"work_item_id": "ENG-102"})
    assert resp.status_code == 200
    data = resp.json()
    assert "demo-fail-" in data["run_id"]


def test_api_demo_brd_endpoint() -> None:
    client = TestClient(app)
    resp = client.post("/api/demo/brd", json={"work_item_id": "ENG-103"})
    assert resp.status_code == 200
    data = resp.json()
    assert "demo-brd-" in data["run_id"]


def test_pipeline_event_serialization() -> None:
    event = PipelineEvent.create(
        run_id="run-test-123",
        event_type=EventType.STAGE_STARTED,
        stage=Stage.PLANNING,
        step=1,
        message="Planning started",
    )
    json_str = event.to_ws_message()
    assert "run-test-123" in json_str
    assert "stage_started" in json_str
    assert "planning" in json_str

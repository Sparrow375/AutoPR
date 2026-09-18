/**
 * Mock WebSocket Events for Frontend Development
 *
 * Person B can use these to build and test the dashboard UI
 * without needing the backend running. Simulates a full pipeline run.
 *
 * Usage:
 *   import { MOCK_EVENTS, simulatePipeline } from '@/lib/mockEvents';
 */

import { PipelineEvent } from './types';

const RUN_ID = "run-demo-001";
const BASE_TIME = new Date();

function t(offsetMs: number): string {
  return new Date(BASE_TIME.getTime() + offsetMs).toISOString();
}

/**
 * A complete sequence of events simulating a successful pipeline run.
 * Use this to develop the dashboard UI with realistic data.
 */
export const MOCK_EVENTS: PipelineEvent[] = [
  // ---- Pipeline Start ----
  {
    run_id: RUN_ID,
    timestamp: t(0),
    event_type: "pipeline_started",
    stage: null,
    data: {
      work_item_id: "AUT-42",
      title: "Add rate limiting to GitHub MCP server",
      source: "linear",
    },
  },

  // ---- Fetching Stage ----
  {
    run_id: RUN_ID,
    timestamp: t(500),
    event_type: "stage_started",
    stage: "fetching",
    data: {},
  },
  {
    run_id: RUN_ID,
    timestamp: t(1200),
    event_type: "tool_called",
    stage: "fetching",
    data: {
      tool_name: "get_issue",
      args: { issue_id: "AUT-42" },
      result: {
        title: "Add rate limiting to GitHub MCP server",
        description: "Implement token bucket rate limiting...",
        labels: ["enhancement", "backend"],
      },
      duration_ms: 680,
    },
  },
  {
    run_id: RUN_ID,
    timestamp: t(2000),
    event_type: "stage_completed",
    stage: "fetching",
    data: {
      stage: "fetching",
      duration_ms: 1500,
      result_summary: "Fetched issue AUT-42 with 3 acceptance criteria",
    },
  },

  // ---- Planning Stage ----
  {
    run_id: RUN_ID,
    timestamp: t(2200),
    event_type: "stage_started",
    stage: "planning",
    data: {},
  },
  {
    run_id: RUN_ID,
    timestamp: t(3000),
    event_type: "reasoning",
    stage: "planning",
    data: {
      thought: "The task requires adding rate limiting to the GitHub MCP server. I need to find the existing server file and understand its current structure.",
      agent: "PlannerAgent",
    },
  },
  {
    run_id: RUN_ID,
    timestamp: t(4500),
    event_type: "tool_called",
    stage: "planning",
    data: {
      tool_name: "search_codebase",
      args: { query: "github mcp server rate limit" },
      result: [
        { file: "autopr/mcp_servers/github_server.py", relevance: 0.95 },
        { file: "autopr/config/settings.py", relevance: 0.72 },
      ],
      duration_ms: 1200,
    },
  },
  {
    run_id: RUN_ID,
    timestamp: t(6000),
    event_type: "confidence_update",
    stage: "planning",
    data: { score: 0.87, threshold: 0.7, agent: "PlannerAgent" },
  },
  {
    run_id: RUN_ID,
    timestamp: t(7000),
    event_type: "stage_completed",
    stage: "planning",
    data: {
      stage: "planning",
      duration_ms: 4800,
      result_summary: "Created implementation plan: modify 2 files, create 1 test file",
    },
  },

  // ---- Coding Stage ----
  {
    run_id: RUN_ID,
    timestamp: t(7500),
    event_type: "stage_started",
    stage: "coding",
    data: {},
  },
  {
    run_id: RUN_ID,
    timestamp: t(8000),
    event_type: "reasoning",
    stage: "coding",
    data: {
      thought: "I'll implement a TokenBucketRateLimiter class and integrate it into the GitHub MCP server's API call methods.",
      agent: "CoderAgent",
    },
  },
  {
    run_id: RUN_ID,
    timestamp: t(12000),
    event_type: "code_changes",
    stage: "coding",
    data: {
      files: [
        {
          path: "autopr/mcp_servers/github_server.py",
          action: "modify",
          diff: "@@ -45,6 +45,28 @@\n+class TokenBucketRateLimiter:\n+    \"\"\"Token bucket rate limiter for API calls.\"\"\"\n+    def __init__(self, tokens_per_second: float = 10.0):\n+        self.rate = tokens_per_second\n+        ...",
        },
        {
          path: "autopr/tests/mcp/test_rate_limiter.py",
          action: "create",
          diff: "+import pytest\n+from autopr.mcp_servers.github_server import TokenBucketRateLimiter\n+\n+def test_rate_limiter_allows_within_limit():\n+    ...",
        },
      ],
    },
  },
  {
    run_id: RUN_ID,
    timestamp: t(13000),
    event_type: "stage_completed",
    stage: "coding",
    data: {
      stage: "coding",
      duration_ms: 5500,
      result_summary: "Modified 1 file, created 1 test file (47 lines added)",
    },
  },

  // ---- Reviewing Stage ----
  {
    run_id: RUN_ID,
    timestamp: t(13500),
    event_type: "stage_started",
    stage: "reviewing",
    data: {},
  },
  {
    run_id: RUN_ID,
    timestamp: t(15000),
    event_type: "validation_result",
    stage: "reviewing",
    data: {
      checks: [
        { name: "ruff check", status: "pass", output: "All checks passed" },
        { name: "pytest", status: "pass", output: "3 passed in 0.42s" },
        { name: "mypy", status: "pass", output: "Success: no issues found" },
      ],
    },
  },
  {
    run_id: RUN_ID,
    timestamp: t(16000),
    event_type: "confidence_update",
    stage: "reviewing",
    data: { score: 0.93, threshold: 0.7, agent: "ReviewerAgent" },
  },
  {
    run_id: RUN_ID,
    timestamp: t(16500),
    event_type: "stage_completed",
    stage: "reviewing",
    data: {
      stage: "reviewing",
      duration_ms: 3000,
      result_summary: "All 3 checks passed. Confidence: 93%",
    },
  },

  // ---- Notifying Stage ----
  {
    run_id: RUN_ID,
    timestamp: t(17000),
    event_type: "stage_started",
    stage: "notifying",
    data: {},
  },
  {
    run_id: RUN_ID,
    timestamp: t(18000),
    event_type: "pr_created",
    stage: "notifying",
    data: {
      url: "https://github.com/Sparrow375/AutoPR/pull/1",
      number: 1,
      title: "feat(mcp): add rate limiting to GitHub MCP server",
      summary: "Implements a token bucket rate limiter for the GitHub MCP server to prevent API rate limit errors during heavy usage. Adds configurable rate (default: 10 req/s) and includes 3 unit tests.",
      branch: "feat/autopr-AUT-42-rate-limiting",
    },
  },
  {
    run_id: RUN_ID,
    timestamp: t(19000),
    event_type: "tool_called",
    stage: "notifying",
    data: {
      tool_name: "send_notification",
      args: { channel: "discord", message: "PR #1 created" },
      result: { success: true },
      duration_ms: 340,
    },
  },
  {
    run_id: RUN_ID,
    timestamp: t(19500),
    event_type: "stage_completed",
    stage: "notifying",
    data: {
      stage: "notifying",
      duration_ms: 2500,
      result_summary: "PR #1 created, Discord notification sent, Linear status updated",
    },
  },

  // ---- Pipeline Complete ----
  {
    run_id: RUN_ID,
    timestamp: t(20000),
    event_type: "pipeline_completed",
    stage: null,
    data: {
      success: true,
      pr_url: "https://github.com/Sparrow375/AutoPR/pull/1",
      duration_ms: 20000,
      stages_completed: ["fetching", "planning", "coding", "reviewing", "notifying"],
    },
  },
];

/**
 * Simulates a pipeline run by dispatching mock events with realistic delays.
 *
 * @param onEvent - Callback invoked for each event
 * @param speedMultiplier - 1.0 = real-time, 2.0 = 2x speed, etc.
 * @returns Cancel function to stop the simulation
 */
export function simulatePipeline(
  onEvent: (event: PipelineEvent) => void,
  speedMultiplier: number = 3.0,
): () => void {
  const timeouts: ReturnType<typeof setTimeout>[] = [];
  let cancelled = false;

  MOCK_EVENTS.forEach((event, index) => {
    const baseDelay = new Date(event.timestamp).getTime() - BASE_TIME.getTime();
    const adjustedDelay = baseDelay / speedMultiplier;

    const timeout = setTimeout(() => {
      if (!cancelled) {
        onEvent({
          ...event,
          timestamp: new Date().toISOString(), // Use current time
        });
      }
    }, adjustedDelay);

    timeouts.push(timeout);
  });

  return () => {
    cancelled = true;
    timeouts.forEach(clearTimeout);
  };
}

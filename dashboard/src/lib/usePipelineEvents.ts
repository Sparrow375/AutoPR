"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  PipelineEvent,
  Stage,
  EventType,
  STAGE_CONFIGS,
} from "./types";
import { useWebSocket, ConnectionState } from "./websocket";
import { simulatePipeline } from "./mockEvents";

// ── Derived state for a single stage ────────────────────────────────

export type StageState = "pending" | "active" | "completed" | "error" | "retry";

export interface StageStatus {
  id: Stage;
  label: string;
  icon: string;
  description: string;
  state: StageState;
  durationMs: number | null;
  resultSummary: string | null;
}

// ── Pipeline aggregate state ────────────────────────────────────────

export interface PipelineState {
  /** All events received so far, in order */
  events: PipelineEvent[];
  /** Derived status per stage */
  stages: StageStatus[];
  /** Currently active stage, or null */
  currentStage: Stage | null;
  /** Latest confidence score and metadata */
  confidence: { score: number; threshold: number; agent: string } | null;
  /** Pipeline run metadata */
  workItemId: string | null;
  workItemTitle: string | null;
  /** Is the pipeline finished? */
  isCompleted: boolean;
  /** Did it succeed? */
  isSuccess: boolean | null;
  /** PR URL if created */
  prUrl: string | null;
  /** WebSocket connection state (live mode) */
  connectionState: ConnectionState;
  /** Whether we are in mock/demo mode */
  isMockMode: boolean;
}

function buildInitialStages(): StageStatus[] {
  return STAGE_CONFIGS.map((cfg) => ({
    ...cfg,
    state: "pending" as StageState,
    durationMs: null,
    resultSummary: null,
  }));
}

function reduceEvent(stages: StageStatus[], event: PipelineEvent): StageStatus[] {
  const next = stages.map((s) => ({ ...s }));
  const type = event.event_type as EventType;
  const data = event.data as Record<string, unknown>;

  switch (type) {
    case "stage_started": {
      const stageId = (data.stage ?? event.stage) as Stage;
      const idx = next.findIndex((s) => s.id === stageId);
      if (idx !== -1) next[idx].state = "active";
      break;
    }
    case "stage_completed": {
      const stageId = (data.stage ?? event.stage) as Stage;
      const idx = next.findIndex((s) => s.id === stageId);
      if (idx !== -1) {
        next[idx].state = "completed";
        next[idx].durationMs = (data.duration_ms as number) ?? null;
        next[idx].resultSummary = (data.result_summary as string) ?? null;
      }
      break;
    }
    case "error": {
      const stageId = (data.stage ?? event.stage) as Stage;
      const idx = next.findIndex((s) => s.id === stageId);
      if (idx !== -1) next[idx].state = "error";
      break;
    }
    case "retry_started": {
      // Mark the current active stage as retrying
      const active = next.find((s) => s.state === "active" || s.state === "error");
      if (active) active.state = "retry";
      break;
    }
  }

  return next;
}

// ── Hook ────────────────────────────────────────────────────────────

interface UsePipelineEventsOptions {
  runId: string | null;
  mockMode?: boolean;
}

export function usePipelineEvents({
  runId,
  mockMode = false,
}: UsePipelineEventsOptions): PipelineState {
  const [mockEvents, setMockEvents] = useState<PipelineEvent[]>([]);
  const [stages, setStages] = useState<StageStatus[]>(buildInitialStages);
  const cancelMockRef = useRef<(() => void) | null>(null);

  // Live WebSocket — only connect when not in mock mode
  const ws = useWebSocket(mockMode ? null : runId);

  // Pick the right event source
  const events = mockMode ? mockEvents : ws.events;

  // Process new events into stage state
  const prevLenRef = useRef(0);
  useEffect(() => {
    if (events.length > prevLenRef.current) {
      let current = stages;
      for (let i = prevLenRef.current; i < events.length; i++) {
        current = reduceEvent(current, events[i]);
      }
      setStages(current);
      prevLenRef.current = events.length;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events.length]);

  // Start mock simulation
  const startMock = useCallback(() => {
    if (cancelMockRef.current) cancelMockRef.current();
    setMockEvents([]);
    setStages(buildInitialStages());
    prevLenRef.current = 0;

    const cancel = simulatePipeline((event) => {
      setMockEvents((prev) => [...prev, event]);
    }, 3.0);

    cancelMockRef.current = cancel;
  }, []);

  // Auto-start mock when mock mode is enabled
  useEffect(() => {
    if (mockMode) {
      startMock();
      return () => {
        if (cancelMockRef.current) cancelMockRef.current();
      };
    }
  }, [mockMode, startMock]);

  // Derive aggregate state
  const state = useMemo<PipelineState>(() => {
    const currentStage = stages.find((s) => s.state === "active" || s.state === "retry")?.id ?? null;

    const lastConfidence = [...events]
      .reverse()
      .find((e) => e.event_type === "confidence_update");
    const confidence = lastConfidence
      ? {
          score: lastConfidence.data.score as number,
          threshold: lastConfidence.data.threshold as number,
          agent: lastConfidence.data.agent as string,
        }
      : null;

    const startedEvent = events.find((e) => e.event_type === "pipeline_started");
    const completedEvent = events.find((e) => e.event_type === "pipeline_completed");
    const prEvent = events.find((e) => e.event_type === "pr_created");

    return {
      events,
      stages,
      currentStage,
      confidence,
      workItemId: (startedEvent?.data.work_item_id as string) ?? null,
      workItemTitle: (startedEvent?.data.title as string) ?? null,
      isCompleted: !!completedEvent,
      isSuccess: completedEvent ? (completedEvent.data.success as boolean) : null,
      prUrl: (prEvent?.data.url as string) ?? (completedEvent?.data.pr_url as string) ?? null,
      connectionState: mockMode ? "connected" : ws.connectionState,
      isMockMode: mockMode,
    };
  }, [events, stages, mockMode, ws.connectionState]);

  return state;
}

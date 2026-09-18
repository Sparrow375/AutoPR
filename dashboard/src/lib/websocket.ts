"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { PipelineEvent } from "./types";
import { WS_BASE_URL, WS_RECONNECT_DELAY, MAX_RETRY_ATTEMPTS } from "./constants";

export type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

interface UseWebSocketReturn {
  /** Accumulated pipeline events in order received */
  events: PipelineEvent[];
  /** Current WebSocket connection state */
  connectionState: ConnectionState;
  /** Send a message (e.g., human input response) */
  send: (data: unknown) => void;
  /** Manually reconnect */
  reconnect: () => void;
}

/**
 * WebSocket hook for consuming real-time pipeline events.
 *
 * Connects to `WS /ws/{runId}`, auto-reconnects on disconnect
 * with exponential backoff, and parses incoming PipelineEvent JSON.
 */
export function useWebSocket(runId: string | null): UseWebSocketReturn {
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const connectRef = useRef<() => void>(() => {});

  const cleanup = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!runId) return;

    cleanup();
    setConnectionState("connecting");

    const url = `${WS_BASE_URL}/ws/${runId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.info(`[WS] Connected to ${url}`);
      setConnectionState("connected");
      retriesRef.current = 0;
    };

    ws.onmessage = (msg) => {
      try {
        const event: PipelineEvent = JSON.parse(msg.data);
        setEvents((prev) => [...prev, event]);
      } catch (err) {
        console.error("[WS] Failed to parse message:", err);
      }
    };

    ws.onerror = (err) => {
      console.error("[WS] Error:", err);
      setConnectionState("error");
    };

    ws.onclose = (e) => {
      console.warn(`[WS] Closed (code=${e.code})`);
      setConnectionState("disconnected");

      // Auto-reconnect with exponential backoff
      if (retriesRef.current < MAX_RETRY_ATTEMPTS) {
        const delay = WS_RECONNECT_DELAY * Math.pow(2, retriesRef.current);
        retriesRef.current += 1;
        console.info(`[WS] Reconnecting in ${delay}ms (attempt ${retriesRef.current}/${MAX_RETRY_ATTEMPTS})`);
        reconnectTimerRef.current = setTimeout(() => connectRef.current(), delay);
      } else {
        console.error("[WS] Max reconnection attempts reached");
        setConnectionState("error");
      }
    };
  }, [runId, cleanup]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn("[WS] Cannot send — not connected");
    }
  }, []);

  const reconnect = useCallback(() => {
    retriesRef.current = 0;
    connect();
  }, [connect]);

  useEffect(() => {
    connectRef.current = connect;
    const timer = setTimeout(() => {
      connect();
    }, 0);
    return () => {
      clearTimeout(timer);
      cleanup();
    };
  }, [connect, cleanup]);

  return { events, connectionState, send, reconnect };
}

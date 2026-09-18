export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

/** Milliseconds before attempting WebSocket reconnection */
export const WS_RECONNECT_DELAY = 2000;

/** Maximum WebSocket reconnection attempts before giving up */
export const MAX_RETRY_ATTEMPTS = 5;

/** Default speed multiplier for mock pipeline simulation */
export const MOCK_SPEED_MULTIPLIER = 3.0;

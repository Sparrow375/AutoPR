import {
  StartPipelineRequest,
  StartPipelineResponse,
  RunSummary,
  RunDetail,
  ErrorResponse,
} from "./types";
import { API_BASE_URL } from "./constants";

/** Custom error for API failures with structured error info. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  try {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });

    const body = await res.json();

    if (!res.ok) {
      const err = body as ErrorResponse;
      throw new ApiError(
        res.status,
        err.code || "UNKNOWN",
        err.message || res.statusText,
        err.details || {},
      );
    }

    return body as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    // Network error — backend probably not running
    throw new ApiError(0, "NETWORK_ERROR", `Cannot reach API at ${url}`);
  }
}

// ── REST API Client ──────────────────────────────────────────────────

/** POST /api/run — Start a new pipeline run. */
export async function startPipeline(
  workItemId: string,
  source: "linear" | "github" = "linear",
): Promise<StartPipelineResponse> {
  return request<StartPipelineResponse>("/api/run", {
    method: "POST",
    body: JSON.stringify({ work_item_id: workItemId, source } satisfies StartPipelineRequest),
  });
}

/** GET /api/runs — List all pipeline runs. */
export async function listRuns(): Promise<{ runs: RunSummary[] }> {
  return request<{ runs: RunSummary[] }>("/api/runs");
}

/** GET /api/runs/{runId} — Get run detail with events. */
export async function getRunDetail(runId: string): Promise<RunDetail> {
  return request<RunDetail>(`/api/runs/${runId}`);
}

/** POST /api/demo/inject-failure — Inject a bug for demo. */
export async function injectFailure(runId: string): Promise<{ success: boolean }> {
  return request<{ success: boolean }>("/api/demo/inject-failure", {
    method: "POST",
    body: JSON.stringify({ run_id: runId }),
  });
}

/** POST /api/demo/inject-brd — Inject BRD document for demo. */
export async function injectBRD(
  runId: string,
  brdContent: string,
): Promise<{ success: boolean }> {
  return request<{ success: boolean }>("/api/demo/inject-brd", {
    method: "POST",
    body: JSON.stringify({ run_id: runId, brd_content: brdContent }),
  });
}

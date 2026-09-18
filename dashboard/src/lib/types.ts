/**
 * AutoPR Pipeline Event Types
 *
 * ⚠️  SHARED CONTRACT — This file MUST stay in sync with:
 *     autopr/api/events.py (Python — source of truth)
 *
 *     Any changes here require coordination with Person A (Backend).
 *     See CONTRIBUTING.md Section 8 for the change process.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

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

export type WorkItemSource = "linear" | "github";

export type FileAction = "create" | "modify" | "delete";

export type CheckStatus = "pass" | "fail" | "skip";

// ---------------------------------------------------------------------------
// Event Data Payloads
// ---------------------------------------------------------------------------

export interface PipelineStartedData {
  work_item_id: string;
  title: string;
  source: WorkItemSource;
}

export interface StageData {
  stage: Stage;
}

export interface StageCompletedData {
  stage: Stage;
  duration_ms: number;
  result_summary: string;
}

export interface ToolCalledData {
  tool_name: string;
  args: Record<string, unknown>;
  result: unknown;
  duration_ms: number;
}

export interface ReasoningData {
  thought: string;
  agent: string;
}

export interface ConfidenceUpdateData {
  score: number;    // 0.0 - 1.0
  threshold: number; // 0.0 - 1.0
  agent: string;
}

export interface HumanInputNeededData {
  prompt: string;
  options: string[];
  a2ui_payload?: Record<string, unknown>;
}

export interface HumanInputReceivedData {
  response: string;
}

export interface ErrorData {
  message: string;
  stage: Stage;
  recoverable: boolean;
  stack_trace?: string;
}

export interface RetryStartedData {
  attempt: number;
  max_attempts: number;
  reason: string;
}

export interface FileChangeData {
  path: string;
  action: FileAction;
  diff: string;
}

export interface CodeChangesData {
  files: FileChangeData[];
}

export interface ValidationCheck {
  name: string;
  status: CheckStatus;
  output: string;
}

export interface ValidationResultData {
  checks: ValidationCheck[];
}

export interface PRCreatedData {
  url: string;
  number: number;
  title: string;
  summary: string;
  branch: string;
}

export interface PipelineCompletedData {
  success: boolean;
  pr_url: string | null;
  duration_ms: number;
  stages_completed: string[];
}

// ---------------------------------------------------------------------------
// Core Event Model
// ---------------------------------------------------------------------------

export interface PipelineEvent {
  run_id: string;
  timestamp: string; // ISO 8601
  event_type: EventType;
  stage: Stage | null;
  data: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// API Request/Response Models
// ---------------------------------------------------------------------------

export interface StartPipelineRequest {
  work_item_id: string;
  source: WorkItemSource;
}

export interface StartPipelineResponse {
  run_id: string;
  status: string;
}

export interface RunSummary {
  run_id: string;
  work_item_id: string;
  source: WorkItemSource;
  status: "running" | "completed" | "failed";
  started_at: string;
  completed_at: string | null;
  pr_url: string | null;
}

export interface RunDetail extends RunSummary {
  events: PipelineEvent[];
}

export interface ErrorResponse {
  error: true;
  code: string;
  message: string;
  details: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Stage Display Config (for UI rendering)
// ---------------------------------------------------------------------------

export interface StageConfig {
  id: Stage;
  label: string;
  icon: string;
  description: string;
}

export const STAGE_CONFIGS: StageConfig[] = [
  {
    id: "fetching",
    label: "Fetch",
    icon: "📥",
    description: "Fetching work item details",
  },
  {
    id: "planning",
    label: "Plan",
    icon: "📋",
    description: "Analyzing codebase and creating implementation plan",
  },
  {
    id: "coding",
    label: "Code",
    icon: "💻",
    description: "Implementing changes and writing tests",
  },
  {
    id: "reviewing",
    label: "Review",
    icon: "🔍",
    description: "Running validation and fixing issues",
  },
  {
    id: "notifying",
    label: "Notify",
    icon: "📢",
    description: "Creating PR and notifying team",
  },
];

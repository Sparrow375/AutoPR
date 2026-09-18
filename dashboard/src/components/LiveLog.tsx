"use client";

import { FC, useEffect, useRef, useState } from "react";
import styles from "./LiveLog.module.css";
import { PipelineEvent, EventType } from "@/lib/types";

interface LiveLogProps {
  events: PipelineEvent[];
}

function eventColor(type: EventType): string {
  switch (type) {
    case "reasoning":         return styles.colorReasoning;
    case "tool_called":       return styles.colorTool;
    case "error":             return styles.colorError;
    case "stage_started":
    case "stage_completed":   return styles.colorStage;
    case "confidence_update": return styles.colorConfidence;
    case "pipeline_started":
    case "pipeline_completed":return styles.colorPipeline;
    case "code_changes":      return styles.colorCode;
    case "validation_result": return styles.colorValidation;
    case "pr_created":        return styles.colorPR;
    case "retry_started":     return styles.colorRetry;
    case "human_input_needed":
    case "human_input_received": return styles.colorHuman;
    default:                  return "";
  }
}

function eventIcon(type: EventType): string {
  switch (type) {
    case "reasoning":          return "💭";
    case "tool_called":        return "🔧";
    case "error":              return "❌";
    case "stage_started":      return "▶️";
    case "stage_completed":    return "✅";
    case "confidence_update":  return "📊";
    case "pipeline_started":   return "🚀";
    case "pipeline_completed": return "🏁";
    case "code_changes":       return "📝";
    case "validation_result":  return "🧪";
    case "pr_created":         return "🔗";
    case "retry_started":      return "🔄";
    case "human_input_needed": return "🙋";
    case "human_input_received": return "✋";
    default:                   return "•";
  }
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

function eventSummary(event: PipelineEvent): string {
  const d = event.data as Record<string, unknown>;
  switch (event.event_type) {
    case "pipeline_started":
      return `Pipeline started for ${d.work_item_id} — "${d.title}"`;
    case "stage_started":
      return `Stage started: ${d.stage ?? event.stage}`;
    case "stage_completed":
      return `Stage completed: ${d.stage ?? event.stage} (${d.result_summary ?? ""})`;
    case "reasoning":
      return `[${d.agent}] ${d.thought}`;
    case "tool_called":
      return `Called ${d.tool_name} (${d.duration_ms}ms)`;
    case "confidence_update":
      return `Confidence: ${((d.score as number) * 100).toFixed(0)}% [${d.agent}]`;
    case "error":
      return `Error in ${d.stage}: ${d.message}`;
    case "retry_started":
      return `Retry ${d.attempt}/${d.max_attempts}: ${d.reason}`;
    case "code_changes": {
      const files = d.files as Array<{ path: string }>;
      return `${files?.length ?? 0} file(s) changed`;
    }
    case "validation_result": {
      const checks = d.checks as Array<{ status: string }>;
      const passed = checks?.filter((c) => c.status === "pass").length ?? 0;
      return `Validation: ${passed}/${checks?.length ?? 0} checks passed`;
    }
    case "pr_created":
      return `PR #${d.number} created: ${d.title}`;
    case "pipeline_completed":
      return d.success ? "✨ Pipeline completed successfully" : "Pipeline failed";
    case "human_input_needed":
      return `Awaiting input: ${d.prompt}`;
    case "human_input_received":
      return `User responded: ${d.response}`;
    default:
      return event.event_type;
  }
}

export const LiveLog: FC<LiveLogProps> = ({ events }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events.length, autoScroll]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const atBottom = scrollHeight - scrollTop - clientHeight < 40;
    setAutoScroll(atBottom);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Live Log</h3>
        <div className={styles.controls}>
          <span className={styles.count}>{events.length} events</span>
          <button
            className={`${styles.scrollBtn} ${autoScroll ? styles.scrollActive : ""}`}
            onClick={() => setAutoScroll(!autoScroll)}
            title={autoScroll ? "Auto-scroll ON" : "Auto-scroll OFF"}
          >
            ↓
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        className={styles.logContainer}
        onScroll={handleScroll}
      >
        {events.length === 0 && (
          <div className={styles.empty}>Waiting for events…</div>
        )}

        {events.map((event, idx) => (
          <div
            key={idx}
            className={`${styles.logEntry} ${eventColor(event.event_type)} ${
              idx === events.length - 1 ? styles.latest : ""
            }`}
            onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
          >
            <span className={styles.time}>{formatTime(event.timestamp)}</span>
            <span className={styles.icon}>{eventIcon(event.event_type)}</span>
            <span className={styles.message}>{eventSummary(event)}</span>

            {expandedIdx === idx && (
              <pre className={styles.detail}>
                {JSON.stringify(event.data, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

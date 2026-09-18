"use client";

import { FC } from "react";
import styles from "./WorkflowGraph.module.css";
import { StageStatus, StageState } from "@/lib/usePipelineEvents";

interface WorkflowGraphProps {
  stages: StageStatus[];
  currentStage: string | null;
  onStageClick?: (stageId: string) => void;
}

function stateIcon(state: StageState, baseIcon: string): string {
  switch (state) {
    case "completed": return "✓";
    case "error":     return "✕";
    case "retry":     return "↻";
    default:          return baseIcon;
  }
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export const WorkflowGraph: FC<WorkflowGraphProps> = ({
  stages,
  currentStage,
  onStageClick,
}) => {
  return (
    <div className={styles.container}>
      <div className={styles.pipeline}>
        {stages.map((stage, i) => (
          <div key={stage.id} className={styles.stageWrapper}>
            {/* Connector line */}
            {i > 0 && (
              <div
                className={`${styles.connector} ${
                  stage.state !== "pending" ? styles.connectorActive : ""
                }`}
              >
                <div className={styles.connectorLine} />
                {stage.state === "active" && (
                  <div className={styles.connectorPulse} />
                )}
              </div>
            )}

            {/* Stage node */}
            <button
              className={`${styles.stageNode} ${styles[stage.state]}`}
              onClick={() => onStageClick?.(stage.id)}
              aria-label={`${stage.label} — ${stage.state}`}
              id={`stage-${stage.id}`}
            >
              <div className={styles.nodeIcon}>
                <span className={styles.iconText}>
                  {stateIcon(stage.state, stage.icon)}
                </span>
                {stage.state === "active" && <div className={styles.activeRing} />}
              </div>

              <div className={styles.nodeLabel}>{stage.label}</div>

              {stage.durationMs !== null && (
                <div className={styles.nodeDuration}>
                  {formatDuration(stage.durationMs)}
                </div>
              )}
            </button>

            {/* Result summary tooltip */}
            {stage.resultSummary && (
              <div className={styles.tooltip}>{stage.resultSummary}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

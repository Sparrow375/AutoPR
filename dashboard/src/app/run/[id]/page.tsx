"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import styles from "./page.module.css";

import { usePipelineEvents } from "@/lib/usePipelineEvents";
import { WorkflowGraph } from "@/components/WorkflowGraph";
import { LiveLog } from "@/components/LiveLog";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { ConfidenceMeter } from "@/components/ConfidenceMeter";
import { CodeDiffPreview } from "@/components/CodeDiffPreview";
import { ValidationResults } from "@/components/ValidationResults";
import { PRSummaryCard } from "@/components/PRSummaryCard";
import { A2UIRenderer } from "@/components/A2UIRenderer";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

import type { FileAction, CheckStatus } from "@/lib/types";

export default function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: runId } = use(params);
  const searchParams = useSearchParams();
  const isMockFromUrl = searchParams.get("mock") === "true";
  const [mockMode, setMockMode] = useState(isMockFromUrl);
  const [humanResponse, setHumanResponse] = useState<string | null>(null);

  const pipeline = usePipelineEvents({ runId, mockMode });

  // Extract specific event data for rich components
  const codeChangesEvent = pipeline.events.find((e) => e.event_type === "code_changes");
  const validationEvent = pipeline.events.find((e) => e.event_type === "validation_result");
  const prEvent = pipeline.events.find((e) => e.event_type === "pr_created");
  const humanInputEvent = pipeline.events
    .filter((e) => e.event_type === "human_input_needed")
    .pop();

  const needsHumanInput = humanInputEvent && !humanResponse;

  const handleHumanResponse = (response: string) => {
    setHumanResponse(response);
    // In live mode, this would send via WebSocket
  };

  return (
    <div className={styles.page}>
      {/* Header bar */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <Link href="/" className={styles.backLink}>← Back</Link>
          <div className={styles.runInfo}>
            <h1 className={styles.runTitle}>
              {pipeline.workItemTitle || `Run ${runId}`}
            </h1>
            {pipeline.workItemId && (
              <Badge variant="neutral" size="md">{pipeline.workItemId}</Badge>
            )}
            {pipeline.isCompleted && (
              <Badge
                variant={pipeline.isSuccess ? "success" : "error"}
                size="md"
                dot
              >
                {pipeline.isSuccess ? "Completed" : "Failed"}
              </Badge>
            )}
            {!pipeline.isCompleted && pipeline.currentStage && (
              <Badge variant="info" size="md" dot>
                {pipeline.currentStage}
              </Badge>
            )}
          </div>
        </div>

        <div className={styles.headerRight}>
          <Button
            variant={mockMode ? "primary" : "ghost"}
            size="sm"
            onClick={() => setMockMode(!mockMode)}
          >
            {mockMode ? "🎬 Mock Mode" : "Mock"}
          </Button>
          <ConnectionStatus state={pipeline.connectionState} />
        </div>
      </header>

      {/* Workflow Graph */}
      <section className={styles.graphSection}>
        <Card variant="default" padding="none">
          <WorkflowGraph
            stages={pipeline.stages}
            currentStage={pipeline.currentStage}
          />
        </Card>
      </section>

      {/* Main content area */}
      <div className={styles.content}>
        {/* Left — Live Log */}
        <div className={styles.logPanel}>
          <LiveLog events={pipeline.events} />
        </div>

        {/* Right — Sidebar */}
        <aside className={styles.sidebar}>
          {/* Confidence Meter */}
          {pipeline.confidence && (
            <Card variant="default" padding="sm">
              <ConfidenceMeter
                score={pipeline.confidence.score}
                threshold={pipeline.confidence.threshold}
                agent={pipeline.confidence.agent}
              />
            </Card>
          )}

          {/* Validation Results */}
          {validationEvent && (
            <ValidationResults
              checks={
                (validationEvent.data.checks as Array<{
                  name: string;
                  status: CheckStatus;
                  output: string;
                }>) || []
              }
            />
          )}
        </aside>
      </div>

      {/* Code Diff */}
      {codeChangesEvent && (
        <section className={styles.diffSection}>
          <CodeDiffPreview
            files={
              (codeChangesEvent.data.files as Array<{
                path: string;
                action: FileAction;
                diff: string;
              }>) || []
            }
          />
        </section>
      )}

      {/* PR Summary */}
      {prEvent && (
        <section className={styles.prSection}>
          <PRSummaryCard
            url={prEvent.data.url as string}
            number={prEvent.data.number as number}
            title={prEvent.data.title as string}
            summary={prEvent.data.summary as string}
            branch={prEvent.data.branch as string}
            success={pipeline.isSuccess ?? true}
          />
        </section>
      )}

      {/* Human Input Modal */}
      {needsHumanInput && (
        <A2UIRenderer
          prompt={humanInputEvent.data.prompt as string}
          options={(humanInputEvent.data.options as string[]) || []}
          onRespond={handleHumanResponse}
          a2uiPayload={
            humanInputEvent.data.a2ui_payload as Record<string, unknown> | undefined
          }
        />
      )}
    </div>
  );
}

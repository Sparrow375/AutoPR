"use client";

import { FC } from "react";
import styles from "./PRSummaryCard.module.css";
import { Card } from "@/components/ui/Card";

interface PRSummaryCardProps {
  url: string;
  number: number;
  title: string;
  summary: string;
  branch: string;
  success?: boolean;
}

const CONFETTI_PIECES = [
  { left: "15%", delay: "0.1s", duration: "1.1s", color: "var(--color-primary-400)" },
  { left: "25%", delay: "0.3s", duration: "1.4s", color: "var(--color-success)" },
  { left: "35%", delay: "0.2s", duration: "0.9s", color: "var(--color-warning)" },
  { left: "45%", delay: "0.4s", duration: "1.2s", color: "var(--color-stage-notifying)" },
  { left: "55%", delay: "0.1s", duration: "1.3s", color: "var(--color-stage-fetching)" },
  { left: "65%", delay: "0.5s", duration: "1.0s", color: "var(--color-primary-400)" },
  { left: "75%", delay: "0.2s", duration: "1.5s", color: "var(--color-success)" },
  { left: "85%", delay: "0.4s", duration: "1.1s", color: "var(--color-warning)" },
  { left: "20%", delay: "0.3s", duration: "1.3s", color: "var(--color-stage-notifying)" },
  { left: "40%", delay: "0.1s", duration: "1.0s", color: "var(--color-stage-fetching)" },
  { left: "60%", delay: "0.5s", duration: "1.4s", color: "var(--color-primary-400)" },
  { left: "80%", delay: "0.2s", duration: "1.2s", color: "var(--color-success)" },
];

export const PRSummaryCard: FC<PRSummaryCardProps> = ({
  url,
  number,
  title,
  summary,
  branch,
  success = true,
}) => {
  return (
    <div className={`${styles.wrapper} ${success ? styles.success : ""}`}>
      {success && (
        <div className={styles.confetti}>
          {CONFETTI_PIECES.map((piece, i) => (
            <span
              key={i}
              className={styles.confettiPiece}
              style={{
                left: piece.left,
                animationDelay: piece.delay,
                animationDuration: piece.duration,
                backgroundColor: piece.color,
              }}
            />
          ))}
        </div>
      )}

      <Card variant="elevated" padding="lg">
        <div className={styles.header}>
          <span className={styles.icon}>🎉</span>
          <h3 className={styles.title}>Pull Request Created</h3>
        </div>

        <div className={styles.prTitle}>
          <span className={styles.prNumber}>#{number}</span>
          {title}
        </div>

        <p className={styles.summary}>{summary}</p>

        <div className={styles.meta}>
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>Branch</span>
            <code className={styles.branch}>{branch}</code>
          </div>
        </div>

        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.viewBtn}
        >
          View on GitHub →
        </a>
      </Card>
    </div>
  );
};

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
          {Array.from({ length: 12 }).map((_, i) => (
            <span
              key={i}
              className={styles.confettiPiece}
              style={{
                left: `${10 + Math.random() * 80}%`,
                animationDelay: `${Math.random() * 0.5}s`,
                animationDuration: `${0.8 + Math.random() * 0.6}s`,
                backgroundColor: [
                  "var(--color-primary-400)", "var(--color-success)",
                  "var(--color-warning)", "var(--color-stage-notifying)",
                  "var(--color-stage-fetching)",
                ][i % 5],
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

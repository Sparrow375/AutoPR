"use client";

import { FC } from "react";
import styles from "./ValidationResults.module.css";
import { CheckStatus } from "@/lib/types";

interface Check {
  name: string;
  status: CheckStatus;
  output: string;
}

interface ValidationResultsProps {
  checks: Check[];
}

function statusIcon(status: CheckStatus): string {
  switch (status) {
    case "pass": return "✅";
    case "fail": return "❌";
    case "skip": return "⏭";
  }
}

export const ValidationResults: FC<ValidationResultsProps> = ({ checks }) => {
  const passed = checks.filter((c) => c.status === "pass").length;
  const failed = checks.filter((c) => c.status === "fail").length;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>🧪 Validation</h3>
        <span className={`${styles.summary} ${failed > 0 ? styles.hasFail : styles.allPass}`}>
          {passed}/{checks.length} passed
        </span>
      </div>

      <div className={styles.checkList}>
        {checks.map((check, idx) => (
          <details key={idx} className={styles.checkItem}>
            <summary className={`${styles.checkHeader} ${styles[check.status]}`}>
              <span className={styles.checkIcon}>{statusIcon(check.status)}</span>
              <span className={styles.checkName}>{check.name}</span>
              <span className={styles.checkStatus}>{check.status}</span>
            </summary>
            {check.output && (
              <pre className={styles.checkOutput}>{check.output}</pre>
            )}
          </details>
        ))}
      </div>
    </div>
  );
};

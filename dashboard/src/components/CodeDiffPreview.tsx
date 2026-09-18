"use client";

import { FC, useState } from "react";
import styles from "./CodeDiffPreview.module.css";
import { FileAction } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";

interface FileChange {
  path: string;
  action: FileAction;
  diff: string;
}

interface CodeDiffPreviewProps {
  files: FileChange[];
}

function actionBadge(action: FileAction) {
  switch (action) {
    case "create": return <Badge variant="success">Created</Badge>;
    case "modify": return <Badge variant="info">Modified</Badge>;
    case "delete": return <Badge variant="error">Deleted</Badge>;
  }
}

export const CodeDiffPreview: FC<CodeDiffPreviewProps> = ({ files }) => {
  const [collapsed, setCollapsed] = useState<Record<number, boolean>>({});

  const toggle = (idx: number) => {
    setCollapsed((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (!files.length) return null;

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>
        📝 Code Changes
        <span className={styles.fileCount}>{files.length} file(s)</span>
      </h3>

      {files.map((file, idx) => (
        <div key={idx} className={styles.fileBlock}>
          <button
            className={styles.fileHeader}
            onClick={() => toggle(idx)}
            aria-expanded={!collapsed[idx]}
          >
            <span className={styles.chevron}>
              {collapsed[idx] ? "▶" : "▼"}
            </span>
            <span className={styles.filePath}>{file.path}</span>
            {actionBadge(file.action)}
          </button>

          {!collapsed[idx] && (
            <pre className={styles.diffContent}>
              {file.diff.split("\n").map((line, i) => {
                let cls = styles.diffLine;
                if (line.startsWith("+")) cls += ` ${styles.added}`;
                else if (line.startsWith("-")) cls += ` ${styles.removed}`;
                else if (line.startsWith("@")) cls += ` ${styles.hunk}`;

                return (
                  <div key={i} className={cls}>
                    <span className={styles.lineNum}>{i + 1}</span>
                    <span className={styles.lineContent}>{line}</span>
                  </div>
                );
              })}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
};

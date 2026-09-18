"use client";

import { FC, useState } from "react";
import styles from "./A2UIRenderer.module.css";
import { Button } from "@/components/ui/Button";

interface A2UIRendererProps {
  prompt: string;
  options: string[];
  onRespond: (response: string) => void;
  a2uiPayload?: Record<string, unknown>;
}

export const A2UIRenderer: FC<A2UIRendererProps> = ({
  prompt,
  options,
  onRespond,
  a2uiPayload,
}) => {
  const [selected, setSelected] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (response: string) => {
    setSelected(response);
    setSubmitted(true);
    onRespond(response);
  };

  if (submitted) {
    return (
      <div className={styles.overlay}>
        <div className={styles.modal}>
          <div className={styles.submitted}>
            <span className={styles.checkmark}>✓</span>
            <p>Response sent: <strong>{selected}</strong></p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <span className={styles.icon}>🙋</span>
          <h3 className={styles.title}>Human Input Required</h3>
        </div>

        <p className={styles.prompt}>{prompt}</p>

        {a2uiPayload && (
          <pre className={styles.payload}>
            {JSON.stringify(a2uiPayload, null, 2)}
          </pre>
        )}

        <div className={styles.options}>
          {options.map((option) => (
            <Button
              key={option}
              variant={selected === option ? "primary" : "secondary"}
              size="lg"
              onClick={() => handleSubmit(option)}
            >
              {option}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};

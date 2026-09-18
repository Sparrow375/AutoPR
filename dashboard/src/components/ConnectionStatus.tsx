"use client";

import { FC } from "react";
import styles from "./ConnectionStatus.module.css";
import { ConnectionState } from "@/lib/websocket";

interface ConnectionStatusProps {
  state: ConnectionState;
  onReconnect?: () => void;
}

const STATE_LABELS: Record<ConnectionState, string> = {
  connecting: "Connecting…",
  connected: "Connected",
  disconnected: "Disconnected",
  error: "Connection error",
};

export const ConnectionStatus: FC<ConnectionStatusProps> = ({
  state,
  onReconnect,
}) => {
  return (
    <div className={`${styles.container} ${styles[state]}`}>
      <span className={styles.dot} />
      <span className={styles.label}>{STATE_LABELS[state]}</span>
      {(state === "disconnected" || state === "error") && onReconnect && (
        <button className={styles.retryBtn} onClick={onReconnect}>
          Retry
        </button>
      )}
    </div>
  );
};

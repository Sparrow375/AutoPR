"use client";

import { FC, useEffect, useRef } from "react";
import styles from "./ConfidenceMeter.module.css";

interface ConfidenceMeterProps {
  score: number;      // 0.0 – 1.0
  threshold: number;  // 0.0 – 1.0
  agent: string;
}

function getColor(score: number): string {
  if (score < 0.5) return "var(--color-error)";
  if (score < 0.7) return "var(--color-warning)";
  return "var(--color-success)";
}

export const ConfidenceMeter: FC<ConfidenceMeterProps> = ({
  score,
  threshold,
  agent,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pct = Math.round(score * 100);
  const belowThreshold = score < threshold;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const size = 140;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    const cx = size / 2;
    const cy = size / 2;
    const r = 56;
    const lw = 8;
    const startAngle = 0.75 * Math.PI;
    const endAngle = 2.25 * Math.PI;
    const totalAngle = endAngle - startAngle;

    // Background arc
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, endAngle);
    ctx.strokeStyle = "rgba(0, 0, 0, 0.06)";
    ctx.lineWidth = lw;
    ctx.lineCap = "round";
    ctx.stroke();

    // Score arc
    const scoreAngle = startAngle + totalAngle * score;
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, scoreAngle);
    ctx.strokeStyle = getColor(score);
    ctx.lineWidth = lw;
    ctx.lineCap = "round";
    ctx.stroke();

    // Threshold marker
    const thAngle = startAngle + totalAngle * threshold;
    const tx = cx + (r + 6) * Math.cos(thAngle);
    const ty = cy + (r + 6) * Math.sin(thAngle);
    ctx.beginPath();
    ctx.arc(tx, ty, 3, 0, Math.PI * 2);
    ctx.fillStyle = "var(--color-neutral-400)";
    ctx.fill();
  }, [score, threshold]);

  return (
    <div className={`${styles.container} ${belowThreshold ? styles.belowThreshold : ""}`}>
      <div className={styles.gaugeWrap}>
        <canvas ref={canvasRef} className={styles.canvas} />
        <div className={styles.scoreOverlay}>
          <span className={styles.scoreValue} style={{ color: getColor(score) }}>
            {pct}%
          </span>
          <span className={styles.scoreLabel}>confidence</span>
        </div>
      </div>

      <div className={styles.meta}>
        <span className={styles.agent}>{agent}</span>
        {belowThreshold && (
          <span className={styles.warning}>⚠ Below threshold ({Math.round(threshold * 100)}%)</span>
        )}
      </div>
    </div>
  );
};

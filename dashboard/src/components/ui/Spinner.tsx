import { FC } from "react";
import styles from "./Spinner.module.css";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const Spinner: FC<SpinnerProps> = ({ size = "md", className = "" }) => {
  return (
    <div className={`${styles.spinner} ${styles[size]} ${className}`} role="status">
      <span className="sr-only">Loading…</span>
    </div>
  );
};

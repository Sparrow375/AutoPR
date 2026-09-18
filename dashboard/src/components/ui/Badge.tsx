import { FC } from "react";
import styles from "./Badge.module.css";

interface BadgeProps {
  variant?: "default" | "success" | "warning" | "error" | "info" | "neutral";
  size?: "sm" | "md";
  dot?: boolean;
  children: React.ReactNode;
}

export const Badge: FC<BadgeProps> = ({
  variant = "default",
  size = "sm",
  dot = false,
  children,
}) => {
  return (
    <span className={`${styles.badge} ${styles[variant]} ${styles[size]}`}>
      {dot && <span className={styles.dot} />}
      {children}
    </span>
  );
};

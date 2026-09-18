import { ButtonHTMLAttributes, FC } from "react";
import styles from "./Button.module.css";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const Button: FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  children,
  className = "",
  ...props
}) => {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]} ${loading ? styles.loading : ""} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className={styles.spinner} />}
      <span className={loading ? styles.hiddenContent : ""}>{children}</span>
    </button>
  );
};

import type { ReactNode } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Info,
} from "lucide-react";

export type AuthAlertVariant =
  | "error"
  | "success"
  | "info";

interface AuthAlertProps {
  variant: AuthAlertVariant;
  children: ReactNode;
}

const alertStyles: Record<
  AuthAlertVariant,
  string
> = {
  error:
    "border-mc-error/30 bg-mc-error/10 text-mc-error",
  success:
    "border-mc-success/30 bg-mc-success/10 text-mc-success",
  info:
    "border-mc-accent/30 bg-mc-accent/10 text-mc-accent",
};

const alertIcons = {
  error: AlertCircle,
  success: CheckCircle2,
  info: Info,
};

export function AuthAlert({
  variant,
  children,
}: AuthAlertProps) {
  const Icon = alertIcons[variant];

  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      aria-live={
        variant === "error"
          ? "assertive"
          : "polite"
      }
      aria-atomic="true"
      className={[
        "flex items-start gap-2.5 rounded-lg border",
        "px-3.5 py-3 text-sm leading-5",
        "wrap-break-word",
        alertStyles[variant],
      ].join(" ")}
    >
      <Icon
        size={15}
        className="mt-0.5 shrink-0"
        aria-hidden="true"
      />

      <div>{children}</div>
    </div>
  );
}
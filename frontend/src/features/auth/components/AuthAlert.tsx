import { forwardRef } from "react";
import type {
  HTMLAttributes,
  ReactNode,
} from "react";
import {
  AlertCircle,
  CheckCircle2,
  Info,
} from "lucide-react";

export type AuthAlertVariant =
  | "error"
  | "success"
  | "info";

interface AuthAlertProps
  extends Omit<
    HTMLAttributes<HTMLDivElement>,
    "children"
  > {
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

export const AuthAlert = forwardRef<
  HTMLDivElement,
  AuthAlertProps
>(function AuthAlert(
  {
    variant,
    children,
    className,
    ...divProps
  },
  ref,
) {
  const Icon = alertIcons[variant];

  return (
    <div
      {...divProps}
      ref={ref}
      role={
        variant === "error"
          ? "alert"
          : "status"
      }
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
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <Icon
        size={15}
        className="mt-0.5 shrink-0"
        aria-hidden="true"
      />

      <div>{children}</div>
    </div>
  );
});
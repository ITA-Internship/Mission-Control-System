import { forwardRef } from "react";
import type {
  HTMLAttributes,
  ReactNode,
} from "react";
import {
  AlertCircle,
  CheckCircle2,
  Info,
  X,
} from "lucide-react";

import { cn } from "../utils/cn";

export type AlertVariant =
  | "error"
  | "success"
  | "info";

interface AlertProps
  extends Omit<
    HTMLAttributes<HTMLDivElement>,
    "children"
  > {
  variant: AlertVariant;
  children: ReactNode;
  /* When provided, renders a trailing dismiss button. */
  onClose?: () => void;
}

const alertStyles: Record<
  AlertVariant,
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

/* Shared inline alert/banner. Used across auth and profile so status messaging
 * stays consistent with the design tokens. Pass `onClose` for a dismissible
 * banner. */
export const Alert = forwardRef<
  HTMLDivElement,
  AlertProps
>(function Alert(
  {
    variant,
    children,
    className,
    onClose,
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
      className={cn(
        "flex items-start gap-2.5 rounded-lg border",
        "px-3.5 py-3 text-sm leading-5",
        "wrap-break-word",
        alertStyles[variant],
        className,
      )}
    >
      <Icon
        size={15}
        className="mt-0.5 shrink-0"
        aria-hidden="true"
      />

      <div className="flex-1">{children}</div>

      {onClose ? (
        <button
          type="button"
          onClick={onClose}
          aria-label="Dismiss message"
          className="shrink-0 opacity-70 transition-opacity hover:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current/40"
        >
          <X size={14} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
});

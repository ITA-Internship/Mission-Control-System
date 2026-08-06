import { Shield } from "lucide-react";
import { useState } from "react";
import type {
  ReactNode,
  RefObject,
} from "react";

import { cn } from "../../../shared/utils/cn";

export function ProfileAvatarImage({
  source,
  alt,
  className,
}: {
  source: string | null;
  alt: string;
  className: string;
}) {
  const [failedSource, setFailedSource] =
    useState<string | null>(null);

  if (!source || failedSource === source) {
    return null;
  }

  return (
    <img
      src={source}
      alt={alt}
      className={className}
      onLoad={() => setFailedSource(null)}
      onError={() => setFailedSource(source)}
    />
  );
}

export function RoleBadge({
  role,
}: {
  role: string;
}) {
  return (
    <span className="inline-flex items-center rounded-full border border-mc-info/30 bg-mc-info/[0.13] px-2.5 py-0.5 text-xs font-semibold tracking-wide text-mc-info">
      {role}
    </span>
  );
}

export function UnitChip({
  unit,
}: {
  unit: string;
}) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-mc-muted/20 bg-mc-muted/[0.08] px-2.5 py-0.5 text-xs font-medium text-mc-muted">
      <Shield size={10} />
      {unit}
    </span>
  );
}

export function FieldLabel({
  children,
  htmlFor,
}: {
  children: ReactNode;
  htmlFor?: string;
}) {
  const className =
    "text-xs font-semibold uppercase tracking-widest text-mc-muted";

  if (!htmlFor) {
    return (
      <span className={className}>{children}</span>
    );
  }

  return (
    <label htmlFor={htmlFor} className={className}>
      {children}
    </label>
  );
}

export function PrimaryButton({
  children,
  onClick,
  loading = false,
  disabled = false,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  loading?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      aria-busy={loading}
      className={cn(
        "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold text-mc-bg transition-colors",
        "bg-mc-accent hover:bg-mc-accent-hover active:bg-mc-accent-active",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40",
        "disabled:cursor-not-allowed disabled:bg-mc-accent/35 disabled:opacity-70 disabled:hover:bg-mc-accent/35",
      )}
    >
      {loading ? (
        <svg
          className="h-3.5 w-3.5 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      ) : null}
      {children}
    </button>
  );
}

export function SecondaryButton({
  children,
  onClick,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-mc-text transition-colors",
        "hover:bg-white/10",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40",
      )}
    >
      {children}
    </button>
  );
}

export function FormTextInput({
  id,
  ariaLabel,
  value,
  onChange,
  placeholder = "",
  type = "text",
  disabled = false,
  error,
  rightElement,
  inputRef,
  autoComplete,
  maxLength,
}: {
  id: string;
  ariaLabel?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
  error?: string;
  rightElement?: ReactNode;
  inputRef?: RefObject<HTMLInputElement | null>;
  autoComplete?: string;
  maxLength?: number;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="relative">
        <input
          id={id}
          ref={inputRef}
          type={type}
          value={value}
          onChange={(event) =>
            onChange(event.target.value)
          }
          placeholder={placeholder}
          disabled={disabled}
          autoComplete={autoComplete}
          maxLength={maxLength}
          className={cn(
            "w-full rounded-lg border bg-mc-panel px-3 py-2.5 text-sm text-mc-text transition-colors",
            "placeholder:text-mc-subtle",
            "focus:outline-none",
            "disabled:bg-mc-panel/50 disabled:text-mc-muted",
            rightElement ? "pr-11" : "",
            error
              ? "border-mc-error focus:border-mc-error"
              : "border-white/10 focus:border-mc-accent focus:ring-2 focus:ring-mc-accent/[0.12]",
          )}
          aria-invalid={Boolean(error)}
          aria-label={ariaLabel}
          aria-describedby={
            error ? `${id}-error` : undefined
          }
        />

        {rightElement ? (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {rightElement}
          </div>
        ) : null}
      </div>

      {error ? (
        <p
          id={`${id}-error`}
          className="text-xs text-mc-error"
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}

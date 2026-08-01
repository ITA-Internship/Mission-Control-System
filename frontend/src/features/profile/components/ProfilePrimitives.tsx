import {
  AlertCircle,
  CheckCircle,
  Shield,
  X,
} from "lucide-react";
import {
  useState,
} from "react";
import type {
  ReactNode,
  RefObject,
} from "react";

export function RoleBadge({
  role,
}: {
  role: string;
}) {
  return (
    <span
      className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide"
      style={{
        color: "#4C8DFF",
        background: "rgba(76,141,255,.13)",
        borderColor: "rgba(76,141,255,.3)",
      }}
    >
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
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium"
      style={{
        color: "#8A94A6",
        background:
          "rgba(138,148,166,.08)",
        borderColor:
          "rgba(138,148,166,.2)",
      }}
    >
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
    "text-xs font-semibold tracking-widest uppercase";
  const style = {
    color: "#8A94A6",
  };

  if (!htmlFor) {
    return (
      <span className={className} style={style}>
        {children}
      </span>
    );
  }

  return (
    <label
      htmlFor={htmlFor}
      className={className}
      style={style}
    >
      {children}
    </label>
  );
}

export function Card({
  id,
  title,
  children,
  accent = false,
}: {
  id?: string;
  title: string;
  children: ReactNode;
  accent?: boolean;
}) {
  return (
    <div
      id={id}
      className="overflow-hidden rounded-xl border"
      style={{
        background: "#161D26",
        borderColor: accent
          ? "rgba(200,162,74,.18)"
          : "rgba(255,255,255,.07)",
      }}
    >
      {accent ? (
        <div
          className="h-px"
          style={{
            background:
              "linear-gradient(90deg, #C8A24A 0%, transparent 55%)",
          }}
        />
      ) : null}

      <div
        className="flex items-center gap-3 border-b px-6 py-4"
        style={{
          borderColor:
            "rgba(255,255,255,.07)",
        }}
      >
        <h2
          className="text-sm font-semibold tracking-wide"
          style={{
            color: "#E6EAF0",
          }}
        >
          {title}
        </h2>
      </div>

      <div className="px-6 py-5">
        {children}
      </div>
    </div>
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
  const isDisabled =
    disabled || loading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all"
      style={{
        background: isDisabled
          ? "rgba(200,162,74,.35)"
          : "#C8A24A",
        color: "#0B0F14",
        cursor: isDisabled
          ? "not-allowed"
          : "pointer",
        opacity: isDisabled ? 0.7 : 1,
      }}
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
}: {
  children: ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-all"
      style={{
        background:
          "rgba(255,255,255,.05)",
        color: "#E6EAF0",
        borderColor:
          "rgba(255,255,255,.1)",
      }}
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
}) {
  const [focused, setFocused] =
    useState(false);

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
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
          style={{
            background: disabled
              ? "rgba(15,22,32,.5)"
              : "#0F1620",
            color: disabled
              ? "#8A94A6"
              : "#E6EAF0",
            border: `1px solid ${
              error
                ? "#E5484D"
                : focused
                  ? "#C8A24A"
                  : "rgba(255,255,255,.1)"
            }`,
            paddingRight: rightElement
              ? "2.75rem"
              : undefined,
            boxShadow:
              focused && !error
                ? "0 0 0 2px rgba(200,162,74,.12)"
                : undefined,
          }}
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
          className="text-xs"
          style={{
            color: "#E5484D",
          }}
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function AlertBanner({
  type,
  message,
  onClose,
}: {
  type: "error" | "success" | "info";
  message: string;
  onClose?: () => void;
}) {
  const config = {
    error: {
      bg: "rgba(229,72,77,.1)",
      border: "rgba(229,72,77,.3)",
      color: "#E5484D",
      Icon: AlertCircle,
    },
    success: {
      bg: "rgba(63,185,80,.1)",
      border: "rgba(63,185,80,.3)",
      color: "#3FB950",
      Icon: CheckCircle,
    },
    info: {
      bg: "rgba(138,148,166,.1)",
      border: "rgba(138,148,166,.3)",
      color: "#8A94A6",
      Icon: AlertCircle,
    },
  }[type];

  const Icon = config.Icon;

  return (
    <div
      className="flex items-start gap-3 rounded-lg border p-3 text-sm"
      style={{
        background: config.bg,
        borderColor: config.border,
      }}
      role={type === "error" ? "alert" : "status"}
      aria-live={
        type === "error"
          ? "assertive"
          : "polite"
      }
    >
      <Icon
        size={15}
        style={{
          color: config.color,
          flexShrink: 0,
          marginTop: 1,
        }}
        aria-hidden="true"
      />

      <span
        className="flex-1 text-sm"
        style={{
          color: config.color,
        }}
      >
        {message}
      </span>

      {onClose ? (
        <button
          type="button"
          onClick={onClose}
          style={{
            color: config.color,
            flexShrink: 0,
          }}
          aria-label="Dismiss message"
        >
          <X size={14} />
        </button>
      ) : null}
    </div>
  );
}

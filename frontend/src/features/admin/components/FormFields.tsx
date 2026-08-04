import { CircleAlert } from "lucide-react";
import type { ReactNode } from "react";

import type { FilterOption } from "./FilterSelect";

const labelClasses =
  "text-[11px] font-semibold tracking-widest text-mc-muted uppercase";

const controlClasses = [
  "w-full rounded-lg border bg-mc-panel px-3 text-sm text-mc-text",
  "transition-colors placeholder:text-mc-subtle",
  "focus:outline-none focus:ring-2",
  "disabled:cursor-not-allowed disabled:opacity-50",
].join(" ");

function stateClasses(
  hasError: boolean,
): string {
  return hasError
    ? "border-mc-error/50 focus:border-mc-error focus:ring-mc-error/20"
    : "border-white/10 focus:border-mc-accent/60 focus:ring-mc-accent/15";
}

/**
 * Point `aria-describedby` at whichever supporting text is actually rendered.
 * The error message replaces the hint (see FieldShell), so the two ids are
 * mutually exclusive.
 */
function describedBy(
  id: string,
  error: string | undefined,
  hint: string | undefined,
): string | undefined {
  if (error) {
    return `${id}-error`;
  }

  if (hint) {
    return `${id}-hint`;
  }

  return undefined;
}

interface FieldShellProps {
  id: string;
  label: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}

function FieldShell({
  id,
  label,
  error,
  hint,
  children,
}: FieldShellProps) {
  return (
    <div className="flex flex-col gap-1">
      <label
        htmlFor={id}
        className={labelClasses}
      >
        {label}
      </label>

      {children}

      {hint && !error ? (
        <p
          id={`${id}-hint`}
          className="text-[11px] leading-4 text-mc-subtle"
        >
          {hint}
        </p>
      ) : null}

      {error ? (
        <p
          id={`${id}-error`}
          role="alert"
          className="flex items-center gap-1.5 text-[11px] text-mc-error"
        >
          <CircleAlert
            size={11}
            className="shrink-0"
            aria-hidden="true"
          />

          <span>{error}</span>
        </p>
      ) : null}
    </div>
  );
}

interface TextFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "email" | "date";
  placeholder?: string;
  error?: string;
  hint?: string;
  disabled?: boolean;
  isMono?: boolean;
}

export function TextField({
  id,
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  error,
  hint,
  disabled,
  isMono = false,
}: TextFieldProps) {
  return (
    <FieldShell
      id={id}
      label={label}
      error={error}
      hint={hint}
    >
      <input
        id={id}
        type={type}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value)
        }
        aria-invalid={
          error ? true : undefined
        }
        aria-describedby={describedBy(
          id,
          error,
          hint,
        )}
        autoComplete="off"
        spellCheck={false}
        className={[
          controlClasses,
          stateClasses(Boolean(error)),
          "h-9",
          isMono ? "font-mono" : "",
        ].join(" ")}
      />
    </FieldShell>
  );
}

interface SelectFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly FilterOption[];
  placeholder?: string;
  error?: string;
  hint?: string;
  disabled?: boolean;
}

export function SelectField({
  id,
  label,
  value,
  onChange,
  options,
  placeholder,
  error,
  hint,
  disabled,
}: SelectFieldProps) {
  return (
    <FieldShell
      id={id}
      label={label}
      error={error}
      hint={hint}
    >
      <select
        id={id}
        value={value}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value)
        }
        aria-invalid={
          error ? true : undefined
        }
        aria-describedby={describedBy(
          id,
          error,
          hint,
        )}
        className={[
          controlClasses,
          stateClasses(Boolean(error)),
          "h-9 cursor-pointer",
        ].join(" ")}
      >
        {placeholder ? (
          <option value="">
            {placeholder}
          </option>
        ) : null}

        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
          >
            {option.label}
          </option>
        ))}
      </select>
    </FieldShell>
  );
}

interface TextAreaFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string;
  hint?: string;
  rows?: number;
  disabled?: boolean;
}

export function TextAreaField({
  id,
  label,
  value,
  onChange,
  placeholder,
  error,
  hint,
  rows = 2,
  disabled,
}: TextAreaFieldProps) {
  return (
    <FieldShell
      id={id}
      label={label}
      error={error}
      hint={hint}
    >
      <textarea
        id={id}
        value={value}
        rows={rows}
        placeholder={placeholder}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value)
        }
        aria-invalid={
          error ? true : undefined
        }
        aria-describedby={describedBy(
          id,
          error,
          hint,
        )}
        className={[
          controlClasses,
          stateClasses(Boolean(error)),
          "resize-none py-2",
        ].join(" ")}
      />
    </FieldShell>
  );
}

export type NoteTone =
  | "accent"
  | "danger"
  | "muted";

const noteStyles: Record<NoteTone, string> = {
  accent:
    "border-mc-accent/20 bg-mc-accent/8 text-mc-accent",
  danger:
    "border-mc-error/20 bg-mc-error/7 text-mc-error",
  muted:
    "border-white/8 bg-white/4 text-mc-muted",
};

interface FormNoteProps {
  tone?: NoteTone;
  icon?: ReactNode;
  /** Announce the note to assistive tech (submission failures). */
  isAlert?: boolean;
  children: ReactNode;
}

export function FormNote({
  tone = "accent",
  icon,
  isAlert = false,
  children,
}: FormNoteProps) {
  return (
    <p
      role={isAlert ? "alert" : undefined}
      aria-live={
        isAlert ? "assertive" : undefined
      }
      className={[
        "flex items-start gap-2 rounded-lg border px-3 py-2.5",
        "text-xs leading-5",
        noteStyles[tone],
      ].join(" ")}
    >
      {icon ? (
        <span
          className="mt-0.5 shrink-0"
          aria-hidden="true"
        >
          {icon}
        </span>
      ) : null}

      <span>{children}</span>
    </p>
  );
}

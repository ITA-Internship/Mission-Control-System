import { forwardRef } from "react";
import type {
  InputHTMLAttributes,
  ReactNode,
} from "react";
import { AlertCircle } from "lucide-react";

export interface TextInputProps
  extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  error?: string;
  leadingIcon?: ReactNode;
  trailingElement?: ReactNode;
}

export const TextInput = forwardRef<
  HTMLInputElement,
  TextInputProps
>(function TextInput(
  {
    id,
    label,
    error,
    leadingIcon,
    trailingElement,
    className,
    "aria-describedby": ariaDescribedBy,
    "aria-invalid": ariaInvalid,
    ...inputProps
  },
  ref,
) {
  const errorId = `${id}-error`;

  const describedBy =
    [
      ariaDescribedBy,
      error ? errorId : undefined,
    ]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="text-xs font-semibold tracking-wider text-mc-muted uppercase"
      >
        {label}
      </label>

      <div className="group relative">
        {leadingIcon ? (
          <span
            className="pointer-events-none absolute inset-y-0 left-0 flex w-10 items-center justify-center text-mc-muted transition-colors group-focus-within:text-mc-accent"
            aria-hidden="true"
          >
            {leadingIcon}
          </span>
        ) : null}

        <input
          {...inputProps}
          ref={ref}
          id={id}
          aria-describedby={describedBy}
          aria-invalid={error ? true : ariaInvalid}
          className={[
            "w-full rounded-lg border bg-mc-field py-2.5 text-sm text-mc-text",
            "placeholder:text-mc-subtle",
            "transition-colors duration-150",
            "focus:outline-none focus:ring-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
            leadingIcon ? "pl-10" : "pl-4",
            trailingElement ? "pr-11" : "pr-4",
            error
              ? "border-mc-error/50 focus:border-mc-error focus:ring-mc-error/20"
              : "border-white/8 focus:border-mc-accent/60 focus:ring-mc-accent/15",
            className,
          ]
            .filter(Boolean)
            .join(" ")}
        />

        {trailingElement ? (
          <span className="absolute inset-y-0 right-0 flex w-11 items-center justify-center">
            {trailingElement}
          </span>
        ) : null}
      </div>

      {error ? (
        <p
          id={errorId}
          role="alert"
          className="flex items-center gap-1.5 text-xs text-mc-error"
        >
          <AlertCircle
            size={12}
            className="shrink-0"
            aria-hidden="true"
          />

          <span>{error}</span>
        </p>
      ) : null}
    </div>
  );
});

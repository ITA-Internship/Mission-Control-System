import type {
  ButtonHTMLAttributes,
  ReactNode,
} from "react";
import { Loader2 } from "lucide-react";

interface SubmitButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  isLoading?: boolean;
  loadingLabel?: string;
}

export function SubmitButton({
  children,
  isLoading = false,
  loadingLabel,
  disabled,
  className,
  type = "submit",
  ...buttonProps
}: SubmitButtonProps) {
  const isDisabled = disabled || isLoading;

  return (
    <button
      {...buttonProps}
      type={type}
      disabled={isDisabled}
      aria-busy={isLoading}
      className={[
        "flex w-full items-center justify-center gap-2 rounded-lg",
        "bg-mc-accent px-4 py-2.5",
        "text-sm font-semibold text-mc-bg",
        "transition-colors duration-150",
        "hover:bg-mc-accent-hover active:bg-mc-accent-active",
        "focus-visible:outline-none focus-visible:ring-2",
        "focus-visible:ring-mc-accent/40",
        "focus-visible:ring-offset-2 focus-visible:ring-offset-mc-card",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {isLoading ? (
        <Loader2
          size={15}
          className="animate-spin"
          aria-hidden="true"
        />
      ) : null}

      <span>
        {isLoading && loadingLabel
          ? loadingLabel
          : children}
      </span>
    </button>
  );
}
import { LoaderCircle } from "lucide-react";
import type {
  ButtonHTMLAttributes,
  ReactNode,
} from "react";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "danger"
  | "success"
  | "accentOutline"
  | "ghost";

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

const variantStyles: Record<
  ButtonVariant,
  string
> = {
  primary:
    "bg-mc-accent text-mc-bg hover:bg-mc-accent-hover active:bg-mc-accent-active",
  secondary:
    "border border-white/10 text-mc-muted hover:bg-white/5 hover:text-mc-text",
  danger:
    "bg-mc-error text-white hover:bg-mc-error/85",
  success:
    "bg-mc-success text-mc-bg hover:bg-mc-success/85",
  accentOutline:
    "border border-mc-accent/35 text-mc-accent hover:bg-mc-accent/10",
  ghost:
    "text-mc-muted hover:bg-white/5 hover:text-mc-text",
};

export function Button({
  variant = "primary",
  isLoading = false,
  icon,
  children,
  className,
  disabled,
  type = "button",
  ...buttonProps
}: ButtonProps) {
  return (
    <button
      {...buttonProps}
      type={type}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      className={[
        "inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-lg px-4",
        "text-sm font-semibold whitespace-nowrap",
        "transition-colors duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40",
        "disabled:cursor-not-allowed disabled:opacity-45",
        variantStyles[variant],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {isLoading ? (
        <LoaderCircle
          size={15}
          className="animate-spin"
          aria-hidden="true"
        />
      ) : (
        icon
      )}

      <span>{children}</span>
    </button>
  );
}

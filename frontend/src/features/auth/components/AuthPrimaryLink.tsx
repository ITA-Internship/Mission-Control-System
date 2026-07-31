import type { ReactNode } from "react";
import { Link } from "react-router";

interface AuthPrimaryLinkProps {
  to: string;
  children: ReactNode;
  className?: string;
}

export function AuthPrimaryLink({
  to,
  children,
  className,
}: AuthPrimaryLinkProps) {
  return (
    <Link
      to={to}
      className={[
        "flex w-full items-center justify-center rounded-lg",
        "bg-mc-accent px-4 py-2.5",
        "text-sm font-semibold text-mc-bg",
        "transition-colors duration-150",
        "hover:bg-mc-accent-hover",
        "active:bg-mc-accent-active",
        "focus-visible:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-mc-accent/40",
        "focus-visible:ring-offset-2",
        "focus-visible:ring-offset-mc-card",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </Link>
  );
}

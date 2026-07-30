import type { ReactNode } from "react";
import { Link } from "react-router";

interface AuthTextLinkProps {
  to: string;
  children: ReactNode;
  icon?: ReactNode;
  className?: string;
}

export function AuthTextLink({
  to,
  children,
  icon,
  className,
}: AuthTextLinkProps) {
  return (
    <Link
      to={to}
      className={[
        "inline-flex items-center gap-1.5 rounded-sm",
        "text-sm text-mc-muted",
        "transition-colors duration-150",
        "hover:text-mc-accent",
        "focus-visible:outline-none focus-visible:ring-2",
        "focus-visible:ring-mc-accent/40",
        "focus-visible:ring-offset-2 focus-visible:ring-offset-mc-card",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {icon ? (
        <span aria-hidden="true">
          {icon}
        </span>
      ) : null}

      <span>{children}</span>
    </Link>
  );
}

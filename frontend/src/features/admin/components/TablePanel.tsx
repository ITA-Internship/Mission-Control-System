import type { ReactNode } from "react";

interface TablePanelProps {
  /** Accessible name for the scrollable table region. */
  label: string;
  footer?: ReactNode;
  children: ReactNode;
}

export function TablePanel({
  label,
  footer,
  children,
}: TablePanelProps) {
  return (
    <section className="overflow-hidden rounded-xl border border-white/7 bg-mc-card">
      <div
        className="mc-scroll overflow-x-auto"
        role="region"
        aria-label={label}
        tabIndex={0}
      >
        {children}
      </div>

      {footer}
    </section>
  );
}

import { Construction } from "lucide-react";
import { useLocation } from "react-router";

import { navTitleFor } from "../layout/navigation";

export function PlaceholderPage({ title }: { title?: string }) {
  const location = useLocation();
  const heading = title ?? navTitleFor(location.pathname);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-mc-border bg-mc-card">
        <Construction className="h-8 w-8 text-mc-muted" />
      </div>
      <div className="text-center">
        <h2 className="text-[16px] font-semibold text-mc-text">
          {heading}
        </h2>
        <p className="mt-1 font-mono text-[12px] text-mc-muted">
          This page is not yet implemented.
        </p>
      </div>
    </div>
  );
}

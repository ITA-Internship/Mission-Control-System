import {
  Shield,
} from "lucide-react";

import { cn } from "../../../shared/utils/cn";
import type { ActiveSection } from "../types/profile";

export function ProfileSectionsSidebar({
  activeSection,
  sections,
  onSelectSection,
}: {
  activeSection: ActiveSection;
  sections: Array<{
    id: ActiveSection;
    label: string;
  }>;
  onSelectSection: (
    section: ActiveSection,
  ) => void;
}) {
  return (
    <div className="sticky top-6 hidden w-44 flex-shrink-0 md:block">
      <div className="overflow-hidden rounded-xl border border-mc-border bg-mc-card">
        <div className="border-b border-mc-border px-4 py-3">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-mc-muted">
            Sections
          </span>
        </div>

        <nav className="p-2">
          {sections.map((section) => {
            const isActive =
              activeSection ===
              section.id;

            return (
              <button
                key={section.id}
                onClick={() =>
                  onSelectSection(section.id)
                }
                aria-current={
                  isActive ? "page" : undefined
                }
                className={cn(
                  "mb-0.5 w-full rounded-lg border-l-2 py-2 pr-3 text-left text-xs font-medium transition-colors",
                  isActive
                    ? "border-mc-accent bg-mc-accent/10 pl-2.5 text-mc-accent"
                    : "border-transparent pl-3 text-mc-muted hover:text-mc-text",
                )}
              >
                {section.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="mt-4 rounded-xl border border-mc-accent/[0.12] bg-mc-accent/[0.04] p-4">
        <Shield
          size={14}
          className="mb-2 text-mc-accent"
        />
        <p className="text-[11px] leading-relaxed text-mc-muted">
          Changes to email, unit, and role require administrator authorization.
        </p>
      </div>
    </div>
  );
}

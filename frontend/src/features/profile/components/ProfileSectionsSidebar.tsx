import {
  Shield,
} from "lucide-react";

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
      <div
        className="overflow-hidden rounded-xl border"
        style={{
          background: "#161D26",
          borderColor:
            "rgba(255,255,255,.07)",
        }}
      >
        <div
          className="border-b px-4 py-3"
          style={{
            borderColor:
              "rgba(255,255,255,.07)",
          }}
        >
          <span
            className="text-[10px] font-semibold uppercase tracking-widest"
            style={{
              color: "#8A94A6",
            }}
          >
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
                className="mb-0.5 w-full rounded-lg px-3 py-2 text-left text-xs font-medium transition-all"
                style={{
                  color: isActive
                    ? "#C8A24A"
                    : "#8A94A6",
                  background:
                    isActive
                      ? "rgba(200,162,74,.1)"
                      : "transparent",
                  borderLeft: `2px solid ${
                    isActive
                      ? "#C8A24A"
                      : "transparent"
                  }`,
                  paddingLeft: isActive
                    ? "10px"
                    : "12px",
                }}
              >
                {section.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div
        className="mt-4 rounded-xl border p-4"
        style={{
          background:
            "rgba(200,162,74,.04)",
          borderColor:
            "rgba(200,162,74,.12)",
        }}
      >
        <Shield
          size={14}
          style={{
            color: "#C8A24A",
          }}
          className="mb-2"
        />
        <p
          className="text-[11px] leading-relaxed"
          style={{
            color: "#8A94A6",
          }}
        >
          Changes to email, unit, and role require administrator authorization.
        </p>
      </div>
    </div>
  );
}

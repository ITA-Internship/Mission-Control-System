import { X } from "lucide-react";

export interface ActiveFilter {
  key: string;
  label: string;
  onRemove: () => void;
}

interface ActiveFilterChipsProps {
  filters: ActiveFilter[];
  onClearAll: () => void;
}

export function ActiveFilterChips({
  filters,
  onClearAll,
}: ActiveFilterChipsProps) {
  if (filters.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {filters.map((filter) => (
        <span
          key={filter.key}
          className="inline-flex items-center gap-1.5 rounded-full border border-mc-accent/30 bg-mc-accent/10 py-0.5 pr-1.5 pl-2.5 text-xs font-medium text-mc-accent"
        >
          {filter.label}

          <button
            type="button"
            onClick={filter.onRemove}
            className="rounded-full p-0.5 transition-opacity hover:opacity-70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40"
          >
            <X
              size={12}
              aria-hidden="true"
            />

            <span className="sr-only">
              {`Remove filter ${filter.label}`}
            </span>
          </button>
        </span>
      ))}

      <button
        type="button"
        onClick={onClearAll}
        className="rounded text-xs text-mc-muted transition-colors hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40"
      >
        Clear all
      </button>
    </div>
  );
}

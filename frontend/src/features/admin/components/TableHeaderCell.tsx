import {
  ChevronDown,
  ChevronsUpDown,
  ChevronUp,
} from "lucide-react";
import type { ReactNode } from "react";

import type {
  SortDirection,
  SortState,
} from "../types/admin";

type Align = "left" | "right" | "center";

const alignClasses: Record<Align, string> = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
};

const headerClasses = [
  "px-4 py-2.5 text-[11px] font-semibold",
  "tracking-widest whitespace-nowrap uppercase",
].join(" ");

interface HeaderCellProps {
  children: ReactNode;
  align?: Align;
  srOnly?: boolean;
}

export function HeaderCell({
  children,
  align = "left",
  srOnly = false,
}: HeaderCellProps) {
  return (
    <th
      scope="col"
      className={`${headerClasses} ${alignClasses[align]} text-mc-muted`}
    >
      {srOnly ? (
        <span className="sr-only">
          {children}
        </span>
      ) : (
        children
      )}
    </th>
  );
}

interface SortableHeaderCellProps<
  TColumn extends string,
> {
  label: string;
  column: TColumn;
  sort: SortState<TColumn>;
  align?: Align;
  onSort: (column: TColumn) => void;
}

function SortIcon({
  direction,
}: {
  direction: SortDirection | null;
}) {
  if (direction === "asc") {
    return (
      <ChevronUp
        size={12}
        className="text-mc-accent"
        aria-hidden="true"
      />
    );
  }

  if (direction === "desc") {
    return (
      <ChevronDown
        size={12}
        className="text-mc-accent"
        aria-hidden="true"
      />
    );
  }

  return (
    <ChevronsUpDown
      size={12}
      className="opacity-30"
      aria-hidden="true"
    />
  );
}

export function SortableHeaderCell<
  TColumn extends string,
>({
  label,
  column,
  sort,
  align = "left",
  onSort,
}: SortableHeaderCellProps<TColumn>) {
  const isActive = sort.column === column;

  const direction = isActive
    ? sort.direction
    : null;

  return (
    <th
      scope="col"
      aria-sort={
        isActive
          ? direction === "asc"
            ? "ascending"
            : "descending"
          : "none"
      }
      className={`${headerClasses} ${alignClasses[align]} p-0`}
    >
      <button
        type="button"
        onClick={() => onSort(column)}
        className={[
          "flex w-full items-center gap-1 px-4 py-2.5",
          "text-[11px] font-semibold tracking-widest uppercase",
          "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-mc-accent/40",
          align === "right"
            ? "justify-end"
            : "justify-start",
          isActive
            ? "text-mc-accent"
            : "text-mc-muted hover:text-mc-text",
        ].join(" ")}
      >
        {label}

        <SortIcon direction={direction} />
      </button>
    </th>
  );
}

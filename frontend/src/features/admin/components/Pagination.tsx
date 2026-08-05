import {
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import type { ReactNode } from "react";

interface PaginationProps {
  page: number;
  pageSize: number;
  count: number;
  /** Extra content rendered on the left of the footer (e.g. immutability note). */
  note?: ReactNode;
  onChange: (page: number) => void;
}

const MAX_PAGE_BUTTONS = 5;

function getPageWindow(
  page: number,
  pageCount: number,
): number[] {
  const size = Math.min(
    MAX_PAGE_BUTTONS,
    pageCount,
  );

  const start = Math.min(
    Math.max(page - Math.floor(size / 2), 1),
    pageCount - size + 1,
  );

  return Array.from(
    { length: size },
    (_, index) => start + index,
  );
}

export function Pagination({
  page,
  pageSize,
  count,
  note,
  onChange,
}: PaginationProps) {
  const pageCount = Math.max(
    Math.ceil(count / pageSize),
    1,
  );

  const firstRow =
    count === 0
      ? 0
      : (page - 1) * pageSize + 1;

  const lastRow = Math.min(
    page * pageSize,
    count,
  );

  return (
    <div className="flex flex-col gap-2 border-t border-white/7 bg-mc-panel px-4 py-2.5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-col gap-1 text-xs text-mc-muted sm:flex-row sm:items-center sm:gap-4">
        {note}

        <p aria-live="polite">
          {count === 0
            ? "No records"
            : `Showing ${firstRow}–${lastRow} of ${count}`}
        </p>
      </div>

      {pageCount > 1 ? (
        <nav
          className="flex items-center gap-1"
          aria-label="Pagination"
        >
          <button
            type="button"
            onClick={() => onChange(page - 1)}
            disabled={page <= 1}
            className="rounded p-1.5 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40 disabled:cursor-not-allowed disabled:opacity-30"
          >
            <ChevronLeft
              size={15}
              aria-hidden="true"
            />

            <span className="sr-only">
              Previous page
            </span>
          </button>

          {getPageWindow(page, pageCount).map(
            (pageNumber) => (
              <button
                key={pageNumber}
                type="button"
                onClick={() =>
                  onChange(pageNumber)
                }
                aria-current={
                  pageNumber === page
                    ? "page"
                    : undefined
                }
                className={[
                  "size-7 rounded text-xs font-medium transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40",
                  pageNumber === page
                    ? "bg-mc-accent text-mc-bg"
                    : "text-mc-muted hover:bg-white/5 hover:text-mc-text",
                ].join(" ")}
              >
                {pageNumber}
              </button>
            ),
          )}

          <button
            type="button"
            onClick={() => onChange(page + 1)}
            disabled={page >= pageCount}
            className="rounded p-1.5 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40 disabled:cursor-not-allowed disabled:opacity-30"
          >
            <ChevronRight
              size={15}
              aria-hidden="true"
            />

            <span className="sr-only">
              Next page
            </span>
          </button>
        </nav>
      ) : null}
    </div>
  );
}

import {
  CircleAlert,
  PlugZap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Button } from "./Button";
import type { TableErrorInfo } from "../utils/adminErrors";

interface TableEmptyStateProps {
  colSpan: number;
  icon: LucideIcon;
  title: string;
  hint: string;
}

export function TableEmptyState({
  colSpan,
  icon: Icon,
  title,
  hint,
}: TableEmptyStateProps) {
  return (
    <tr>
      <td colSpan={colSpan}>
        <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
          <span className="flex size-12 items-center justify-center rounded-xl bg-white/4">
            <Icon
              size={20}
              className="text-mc-muted"
              aria-hidden="true"
            />
          </span>

          <p className="text-sm font-semibold text-mc-text">
            {title}
          </p>

          <p className="text-xs text-mc-muted">
            {hint}
          </p>
        </div>
      </td>
    </tr>
  );
}

interface TableErrorStateProps {
  colSpan: number;
  error: TableErrorInfo;
  onRetry: () => void;
}

export function TableErrorState({
  colSpan,
  error,
  onRetry,
}: TableErrorStateProps) {
  const Icon = error.isEndpointMissing
    ? PlugZap
    : CircleAlert;

  return (
    <tr>
      <td colSpan={colSpan}>
        <div
          className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center"
          role="alert"
        >
          <span className="flex size-12 items-center justify-center rounded-xl bg-mc-error/10">
            <Icon
              size={20}
              className="text-mc-error"
              aria-hidden="true"
            />
          </span>

          <p className="text-sm font-semibold text-mc-text">
            {error.title}
          </p>

          <p className="max-w-md text-xs leading-5 text-mc-muted">
            {error.message}
          </p>

          {error.canRetry ? (
            <Button
              variant="secondary"
              onClick={onRetry}
              className="mt-1"
            >
              Retry
            </Button>
          ) : null}
        </div>
      </td>
    </tr>
  );
}

interface TableSkeletonProps {
  columns: number;
  rows?: number;
}

export function TableSkeleton({
  columns,
  rows = 5,
}: TableSkeletonProps) {
  return (
    <>
      {Array.from({ length: rows }).map(
        (_, rowIndex) => (
          <tr
            key={rowIndex}
            className="border-b border-white/5 last:border-b-0"
          >
            {Array.from({
              length: columns,
            }).map((__, columnIndex) => (
              <td
                key={columnIndex}
                className="px-4 py-3"
              >
                <span
                  className="block h-3 animate-pulse rounded bg-white/8"
                  style={{
                    width: `${55 + ((rowIndex + columnIndex) % 4) * 12}%`,
                  }}
                />
              </td>
            ))}
          </tr>
        ),
      )}

      <tr>
        <td colSpan={columns}>
          <span
            className="sr-only"
            role="status"
          >
            Loading data
          </span>
        </td>
      </tr>
    </>
  );
}

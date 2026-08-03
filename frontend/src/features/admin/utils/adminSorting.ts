import type {
  SortDirection,
  SortState,
} from "../types/admin";

export function toggleSort<
  TColumn extends string,
>(
  sort: SortState<TColumn>,
  column: TColumn,
): SortState<TColumn> {
  if (sort.column !== column) {
    return {
      column,
      direction: "asc",
    };
  }

  return {
    column,
    direction:
      sort.direction === "asc"
        ? "desc"
        : "asc",
  };
}

type SortValue = string | number | null;

function compareValues(
  left: SortValue,
  right: SortValue,
): number {
  if (left === right) {
    return 0;
  }

  // Empty cells always sort last, regardless of direction.
  if (left === null || left === "") {
    return 1;
  }

  if (right === null || right === "") {
    return -1;
  }

  if (
    typeof left === "number" &&
    typeof right === "number"
  ) {
    return left - right;
  }

  return String(left).localeCompare(
    String(right),
    undefined,
    { sensitivity: "base" },
  );
}

/** Stable, direction-aware sort that leaves the input array untouched. */
export function sortRows<TRow>(
  rows: TRow[],
  select: (row: TRow) => SortValue,
  direction: SortDirection,
): TRow[] {
  return [...rows].sort((left, right) => {
    const result = compareValues(
      select(left),
      select(right),
    );

    return direction === "asc"
      ? result
      : -result;
  });
}

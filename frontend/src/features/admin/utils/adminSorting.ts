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

function isEmpty(value: SortValue): boolean {
  return value === null || value === "";
}

function compareValues(
  left: SortValue,
  right: SortValue,
): number {
  if (left === right) {
    return 0;
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
    const leftValue = select(left);
    const rightValue = select(right);

    // Empty cells always sort last, regardless of direction. Resolve them
    // before the direction flip below so the sentinel is never negated.
    const leftEmpty = isEmpty(leftValue);
    const rightEmpty = isEmpty(rightValue);

    if (leftEmpty || rightEmpty) {
      if (leftEmpty === rightEmpty) {
        return 0;
      }

      return leftEmpty ? 1 : -1;
    }

    const result = compareValues(
      leftValue,
      rightValue,
    );

    return direction === "asc"
      ? result
      : -result;
  });
}

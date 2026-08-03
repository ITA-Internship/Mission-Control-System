type ClassValue =
  | string
  | number
  | null
  | false
  | undefined;

/**
 * Join truthy class-name values into a single string.
 *
 * A dependency-free stand-in for `clsx`; sufficient for the conditional
 * class composition used across the app.
 */
export function cn(...values: ClassValue[]): string {
  return values
    .filter((value): value is string | number =>
      Boolean(value),
    )
    .join(" ");
}

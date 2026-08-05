const EM_DASH = "—";

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** `2026-07-30 08:14` in the viewer's local time. */
export function formatDateTime(
  value: string | null,
): string {
  if (!value) {
    return EM_DASH;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    ` ${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

/** Same as `formatDateTime`, with seconds — audit entries need them. */
export function formatTimestamp(
  value: string | null,
): string {
  if (!value) {
    return EM_DASH;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return `${formatDateTime(value)}:${pad(date.getSeconds())}`;
}

export function formatCount(
  value: number | null,
): string {
  return value === null
    ? EM_DASH
    : String(value);
}

export function formatText(
  value: string | null,
): string {
  return value?.trim() ? value : EM_DASH;
}

export { EM_DASH };

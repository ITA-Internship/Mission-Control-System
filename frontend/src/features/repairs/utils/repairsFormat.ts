export function formatOrderId(id: number): string {
  return `RO-${String(id).padStart(4, "0")}`;
}

export function formatDefectId(id: number): string {
  return `DEF-${String(id).padStart(4, "0")}`;
}

export function formatDroneLabel(droneId: number): string {
  return `Drone #${droneId}`;
}

export function formatUserLabel(userId: number | null): string {
  return userId === null ? "—" : `User #${userId}`;
}

export function toLocalDatetimeInput(
  value: Date = new Date(),
): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}` +
    `T${pad(value.getHours())}:${pad(value.getMinutes())}`
  );
}

export function localDatetimeToIso(value: string): string {
  const date = new Date(value);
  return date.toISOString();
}

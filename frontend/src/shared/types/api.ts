/* Transport-level shapes shared by every feature: the envelopes the Django API
 * wraps its payloads in, and the async state a panel derives from a request. */

/* Single-message response used by most write endpoints. */
export interface DetailResponse {
  detail: string;
}

/* Django REST Framework paginated list envelope. */
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/* ---- Per-section async state ----
 *
 * The terminal state of one page section. `restricted` is distinct from
 * `error`: it is the UI's reaction to a backend 403 and is never retryable. */
export type SectionStatus =
  | "loading"
  | "success"
  | "error"
  | "restricted";

export interface SectionState<T> {
  status: SectionStatus;
  data: T | null;
}

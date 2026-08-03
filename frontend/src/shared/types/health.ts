export interface HealthResponse {
  status: string;
  dependencies: Record<string, string>;
}

export type HealthState = "operational" | "degraded" | "unknown";

export interface Role {
  id: number;
  code: string;
  name: string;
}

export interface MilitaryUnit {
  id: number;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
  drone_count: number | null;
  user_count: number | null;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  /** `first_name last_name`, falling back to the username. */
  full_name: string;
  role: Role | null;
  unit: MilitaryUnit | null;
  is_active: boolean;
  created_by: string | null;
  last_login: string | null;
}

export type AuditResult = "SUCCESS" | "FAILED";

export interface AuditLogEntry {
  id: number;
  actor: number | null;
  actor_username: string | null;
  target_user: number | null;
  target_user_username: string | null;
  action_type: string;
  result: AuditResult;
  description: string;
  ip_address: string | null;
  user_agent: string;
  created_at: string;
}

export interface Page<T> {
  count: number;
  results: T[];
}

export type SortDirection = "asc" | "desc";

export interface SortState<TColumn extends string> {
  column: TColumn;
  direction: SortDirection;
}

export interface CreateUserPayload {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: number | null;
  unit: number | null;
  rank?: string;
}

export interface UnitPayload {
  name: string;
  code: string;
  description: string;
}

export interface UserListParams {
  page?: number;
  page_size?: number;
  search?: string;
  role?: number | null;
  unit?: number | null;
  is_active?: boolean | null;
}

export interface AuditLogParams {
  page?: number;
  page_size?: number;
  action_type?: string;
  result?: string;
  start_date?: string;
  end_date?: string;
}

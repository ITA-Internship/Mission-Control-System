export type Role = "Admin" | "Commander" | "Dispatcher" | "Operator" | "Technician" | "Viewer";

export interface User {
  name: string;
  rank: string;
  role: Role;
  initials: string;
}

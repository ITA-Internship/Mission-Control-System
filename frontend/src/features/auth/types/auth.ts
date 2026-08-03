export type { DetailResponse } from "../../../shared/types/api";

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  rank: string | null;
  contact: string | null;
  profile_picture: string | null;
  role: number | null;
  unit: number | null;
  is_active: boolean;
  must_change_password: boolean;
}

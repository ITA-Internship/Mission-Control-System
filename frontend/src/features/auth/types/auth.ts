export interface DetailResponse {
  detail: string;
}

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
  role_name?: string | null;
  role_code?: string | null;
  unit: number | null;
  unit_name?: string | null;
  unit_code?: string | null;
  is_active: boolean;
  must_change_password: boolean;
  last_login?: string | null;
  created_at?: string | null;
  created_by_username?: string | null;
}

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
  role_code: string | null;
  role_name: string | null;
  unit: number | null;
  is_active: boolean;
  must_change_password: boolean;
}
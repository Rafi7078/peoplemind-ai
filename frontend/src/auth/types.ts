export type AdminUser = {
  id: number;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
};
export type TokenResponse = {
  access_token: string;
  token_type: string;
};
export type AuthContextValue = {
  user: AdminUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (
    email: string,
    password: string,
  ) => Promise<void>;
  logout: () => void;
};

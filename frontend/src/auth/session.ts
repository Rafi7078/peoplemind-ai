const TOKEN_KEY = "peoplemind_access_token";
export const AUTH_EXPIRED_EVENT = "peoplemind:auth-expired";
export const tokenSession = {
  get(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  },
  set(token: string): void {
    sessionStorage.setItem(TOKEN_KEY, token);
  },
  clear(): void {
    sessionStorage.removeItem(TOKEN_KEY);
  },
};

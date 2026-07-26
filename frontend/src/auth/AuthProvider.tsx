import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { PropsWithChildren } from "react";
import { apiClient } from "../api/client";
import { AuthContext } from "./AuthContext";
import {
  AUTH_EXPIRED_EVENT,
  tokenSession,
} from "./session";
import type {
  AdminUser,
  AuthContextValue,
  TokenResponse,
} from "./types";
export function AuthProvider({
  children,
}: PropsWithChildren) {
  const [user, setUser] =
    useState<AdminUser | null>(null);
  const [isLoading, setIsLoading] =
    useState(
      () => tokenSession.get() !== null,
    );
  useEffect(() => {
    const token = tokenSession.get();
    if (!token) {
      return;
    }
    const controller = new AbortController();
    apiClient
      .get<AdminUser>(
        "/api/auth/me",
        {
          signal: controller.signal,
        },
      )
      .then((response) => {
        if (!controller.signal.aborted) {
          setUser(response.data);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          tokenSession.clear();
          setUser(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });
    return () => {
      controller.abort();
    };
  }, []);
  useEffect(() => {
    const handleExpiredSession = () => {
      setUser(null);
      setIsLoading(false);
    };
    window.addEventListener(
      AUTH_EXPIRED_EVENT,
      handleExpiredSession,
    );
    return () => {
      window.removeEventListener(
        AUTH_EXPIRED_EVENT,
        handleExpiredSession,
      );
    };
  }, []);
  const login = useCallback(
    async (
      email: string,
      password: string,
    ): Promise<void> => {
      const formData = new URLSearchParams();
      formData.set(
        "username",
        email.trim(),
      );
      formData.set(
        "password",
        password,
      );
      const tokenResponse =
        await apiClient.post<TokenResponse>(
          "/api/auth/login",
          formData,
          {
            headers: {
              "Content-Type":
                "application/x-www-form-urlencoded",
            },
          },
        );
      tokenSession.set(
        tokenResponse.data.access_token,
      );
      try {
        const profileResponse =
          await apiClient.get<AdminUser>(
            "/api/auth/me",
          );
        setUser(profileResponse.data);
      } catch (error) {
        tokenSession.clear();
        setUser(null);
        throw error;
      }
    },
    [],
  );
  const logout = useCallback((): void => {
    tokenSession.clear();
    setUser(null);
    setIsLoading(false);
  }, []);
  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      login,
      logout,
    }),
    [
      isLoading,
      login,
      logout,
      user,
    ],
  );
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

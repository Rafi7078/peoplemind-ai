import axios from "axios";
import {
  AUTH_EXPIRED_EVENT,
  tokenSession,
} from "../auth/session";
const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";
export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30_000,
});
apiClient.interceptors.request.use((config) => {
  const token = tokenSession.get();
  if (token) {
    config.headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }
  return config;
});
apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (
      axios.isAxiosError(error) &&
      error.response?.status === 401 &&
      !error.config?.url?.endsWith(
        "/api/auth/login",
      )
    ) {
      tokenSession.clear();
      window.dispatchEvent(
        new Event(AUTH_EXPIRED_EVENT),
      );
    }
    return Promise.reject(error);
  },
);

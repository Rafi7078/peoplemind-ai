import {
  Navigate,
  Outlet,
} from "react-router-dom";
import { useAuth } from "../auth/useAuth";
export function ProtectedRoute() {
  const {
    isAuthenticated,
    isLoading,
  } = useAuth();
  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-700 border-t-sky-400" />
          <p className="mt-4 text-sm font-medium text-slate-300">
            Restoring secure session...
          </p>
        </div>
      </main>
    );
  }
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }
  return <Outlet />;
}

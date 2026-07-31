import {
  NavLink,
  Outlet,
} from "react-router-dom";
import { useAuth } from "../auth/useAuth";
export function AppShell() {
  const {
    user,
    logout,
  } = useAuth();
  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-5 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 font-black text-sky-400">
              PM
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">
                PeopleMind AI
              </p>
              <p className="text-sm text-slate-500">
                HR Intelligence and Management
              </p>
            </div>
          </div>
          <nav className="order-3 flex w-full gap-2 sm:order-2 sm:w-auto">
            <NavLink
              className={({ isActive }) =>
                [
                  "rounded-xl px-4 py-2 text-sm font-semibold transition",
                  isActive
                    ? "bg-slate-950 text-white"
                    : "text-slate-600 hover:bg-slate-100",
                ].join(" ")
              }
              end
              to="/"
            >
              Dashboard
            </NavLink>
            <NavLink
              className={({ isActive }) =>
                [
                  "rounded-xl px-4 py-2 text-sm font-semibold transition",
                  isActive
                    ? "bg-slate-950 text-white"
                    : "text-slate-600 hover:bg-slate-100",
                ].join(" ")
              }
              to="/documents"
            >
              Document Assistant
            </NavLink>
            <NavLink
              className={({ isActive }) =>
                [
                  "rounded-xl px-4 py-2 text-sm font-semibold transition",
                  isActive
                    ? "bg-slate-950 text-white"
                    : "text-slate-600 hover:bg-slate-100",
                ].join(" ")
              }
              to="/cv-intelligence"
            >
              CV Intelligence
            </NavLink>
          </nav>
          <div className="order-2 flex items-center gap-4 sm:order-3">
            <div className="hidden text-right md:block">
              <p className="text-sm font-semibold text-slate-800">
                HR Administrator
              </p>
              <p className="text-xs text-slate-500">
                {user?.email}
              </p>
            </div>
            <button
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
              onClick={logout}
              type="button"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <Outlet />
    </div>
  );
}

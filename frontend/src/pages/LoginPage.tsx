import {
  useEffect,
  useState,
} from "react";
import type { FormEvent } from "react";
import axios from "axios";
import {
  Navigate,
  useNavigate,
} from "react-router-dom";
import { useAuth } from "../auth/useAuth";
export function LoginPage() {
  const navigate = useNavigate();
  const {
    isAuthenticated,
    login,
  } = useAuth();
  const [email, setEmail] =
    useState("");
  const [password, setPassword] =
    useState("");
  const [errorMessage, setErrorMessage] =
    useState("");
  const [isSubmitting, setIsSubmitting] =
    useState(false);
  useEffect(() => {
    document.title =
      "Admin Login | PeopleMind AI";
  }, []);
  if (isAuthenticated) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }
  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/", {
        replace: true,
      });
    } catch (error) {
      if (
        axios.isAxiosError(error) &&
        !error.response
      ) {
        setErrorMessage(
          "Backend server is not reachable. Start FastAPI and try again.",
        );
      } else if (
        axios.isAxiosError(error) &&
        typeof error.response?.data?.detail ===
          "string"
      ) {
        setErrorMessage(
          error.response.data.detail,
        );
      } else {
        setErrorMessage(
          "Login failed. Please try again.",
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }
  return (
    <main className="grid min-h-screen bg-slate-950 lg:grid-cols-2">
      <section className="hidden border-r border-slate-800 p-12 lg:flex lg:flex-col lg:justify-between">
        <div>
          <div className="inline-flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-400 font-black text-slate-950">
              PM
            </div>
            <div>
              <p className="text-lg font-bold text-white">
                PeopleMind AI
              </p>
              <p className="text-sm text-slate-400">
                Local HR Intelligence
              </p>
            </div>
          </div>
          <div className="mt-24 max-w-xl">
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-400">
              Private by design
            </p>
            <h1 className="mt-5 text-5xl font-bold leading-tight text-white">
              Your secure workspace for
              intelligent HR operations.
            </h1>
            <p className="mt-6 text-lg leading-8 text-slate-400">
              Analyse internal documents using
              local AI without sending private
              company information to external
              services.
            </p>
          </div>
        </div>
        <p className="text-sm text-slate-500">
          Human review remains required for all
          AI-assisted HR decisions.
        </p>
      </section>
      <section className="flex items-center justify-center bg-slate-100 px-6 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <p className="text-2xl font-black text-slate-900">
              PeopleMind AI
            </p>
            <p className="mt-1 text-sm text-slate-500">
              HR Intelligence and Management
              Assistant
            </p>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/70">
            <div>
              <p className="text-sm font-semibold text-sky-600">
                SECURE ADMIN ACCESS
              </p>
              <h2 className="mt-2 text-3xl font-bold text-slate-950">
                Welcome back
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Sign in with your authorised
                HR/Admin account.
              </p>
            </div>
            <form
              className="mt-8 space-y-5"
              onSubmit={handleSubmit}
            >
              <div>
                <label
                  className="text-sm font-semibold text-slate-700"
                  htmlFor="email"
                >
                  Admin email
                </label>
                <input
                  autoComplete="username"
                  className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
                  id="email"
                  onChange={(event) => {
                    setEmail(event.target.value);
                  }}
                  placeholder="admin@company.com"
                  required
                  type="email"
                  value={email}
                />
              </div>
              <div>
                <label
                  className="text-sm font-semibold text-slate-700"
                  htmlFor="password"
                >
                  Password
                </label>
                <input
                  autoComplete="current-password"
                  className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
                  id="password"
                  minLength={8}
                  onChange={(event) => {
                    setPassword(
                      event.target.value,
                    );
                  }}
                  placeholder="Enter your password"
                  required
                  type="password"
                  value={password}
                />
              </div>
              {errorMessage ? (
                <div
                  className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
                  role="alert"
                >
                  {errorMessage}
                </div>
              ) : null}
              <button
                className="flex w-full items-center justify-center rounded-xl bg-slate-950 px-4 py-3 font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting
                  ? "Signing in..."
                  : "Sign in securely"}
              </button>
            </form>
            <p className="mt-6 text-center text-xs leading-5 text-slate-400">
              The access token is stored only for
              the current browser session.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

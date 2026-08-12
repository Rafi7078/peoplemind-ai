import axios from "axios";
import {
  useEffect,
  useState,
} from "react";
import type {
  FormEvent,
} from "react";
import {
  Navigate,
  useNavigate,
} from "react-router-dom";
import {
  useAuth,
} from "../auth/useAuth";
export function LoginPage() {
  const navigate =
    useNavigate();
  const {
    isAuthenticated,
    login,
  } = useAuth();
  const [
    email,
    setEmail,
  ] = useState("");
  const [
    password,
    setPassword,
  ] = useState("");
  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");
  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);
  const [
    showPassword,
    setShowPassword,
  ] = useState(false);
  useEffect(() => {
    document.title =
      "Login | PeopleMind AI";
  }, []);
  if (isAuthenticated) {
    return (
      <Navigate
        replace
        to="/"
      />
    );
  }
  async function handleSubmit(
    event:
      FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);
    try {
      await login(
        email,
        password,
      );
      navigate(
        "/",
        {
          replace: true,
        },
      );
    } catch (error) {
      if (
        axios.isAxiosError(error)
        && !error.response
      ) {
        setErrorMessage(
          "Backend server is not reachable. Start FastAPI and try again.",
        );
      } else if (
        axios.isAxiosError(error)
        && typeof error
          .response
          ?.data
          ?.detail
          === "string"
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
    <main className="relative min-h-[100dvh] overflow-hidden bg-[#eef3f8] lg:grid lg:h-[100dvh] lg:grid-cols-[1.08fr_0.92fr]">
      <section className="relative hidden overflow-hidden bg-[#020817] px-12 py-7 text-white lg:flex lg:h-[100dvh] lg:flex-col lg:justify-between xl:px-16 xl:py-8">
        <div className="pm-login-grid absolute inset-0 opacity-40" />
        <div className="pm-login-orb pm-login-orb-one" />
        <div className="pm-login-orb pm-login-orb-two" />
        <div className="pm-login-orb pm-login-orb-three" />
        <div className="pm-login-scan absolute inset-y-0 w-28" />
        <div className="relative z-10">
          <div className="inline-flex items-center gap-3">
            <div className="pm-logo-pulse flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400 font-black text-slate-950 shadow-lg shadow-cyan-400/20">
              PM
            </div>
            <div>
              <p className="text-lg font-black tracking-tight text-white">
                PeopleMind AI
              </p>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Local HR Intelligence
              </p>
            </div>
          </div>
          <div className="mt-10 max-w-2xl xl:mt-12">
            <div className="pm-rise pm-rise-one inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2">
              <span className="h-2 w-2 rounded-full bg-cyan-300" />
              <span className="text-xs font-black uppercase tracking-[0.2em] text-cyan-300">
                Private by design
              </span>
            </div>
            <h1 className="pm-rise pm-rise-two mt-5 max-w-xl text-5xl font-black leading-[1.02] tracking-[-0.04em] text-white xl:text-[56px]">
              Intelligent HR.
              <span className="block text-slate-400">
                Private by default.
              </span>
            </h1>
            <p className="pm-rise pm-rise-three mt-5 max-w-xl text-base leading-7 text-slate-400">
              Work with policies, candidate
              intelligence and workforce
              attendance from one secure local
              workspace.
            </p>
            <div className="pm-rise pm-rise-four mt-6 grid max-w-2xl gap-4 xl:grid-cols-[245px_1fr] xl:items-center">
              <div className="pm-ai-core-wrap relative mx-auto h-[220px] w-[220px] scale-90 xl:scale-100">
                <div className="pm-core-glow absolute inset-[34px] rounded-full" />
                <div className="pm-orbit pm-orbit-one absolute inset-[12px] rounded-full border border-cyan-400/20">
                  <span className="pm-orbit-dot bg-cyan-300" />
                </div>
                <div className="pm-orbit pm-orbit-two absolute inset-[35px] rounded-full border border-violet-400/20">
                  <span className="pm-orbit-dot bg-violet-300" />
                </div>
                <div className="pm-orbit pm-orbit-three absolute inset-[58px] rounded-full border border-emerald-400/20">
                  <span className="pm-orbit-dot bg-emerald-300" />
                </div>
                <div className="pm-ai-core absolute inset-[76px] flex flex-col items-center justify-center rounded-full border border-cyan-300/30 bg-slate-950/80 backdrop-blur-xl">
                  <span className="text-lg font-black text-cyan-300">
                    PM
                  </span>
                  <span className="mt-1 text-[8px] font-black uppercase tracking-[0.2em] text-slate-500">
                    AI CORE
                  </span>
                </div>
                <div className="pm-node pm-node-doc">
                  DOC
                </div>
                <div className="pm-node pm-node-cv">
                  CV
                </div>
                <div className="pm-node pm-node-att">
                  ATT
                </div>
              </div>
              <div className="grid gap-3">
                <div className="pm-intelligence-tile pm-tile-one">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.16em] text-cyan-300">
                      Document Intelligence
                    </p>
                    <p className="mt-1 text-sm font-bold text-white">
                      Grounded HR knowledge
                    </p>
                  </div>
                  <span className="pm-live-dot" />
                </div>
                <div className="pm-intelligence-tile pm-tile-two">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.16em] text-violet-300">
                      Candidate Intelligence
                    </p>
                    <p className="mt-1 text-sm font-bold text-white">
                      ATS and job-match analysis
                    </p>
                  </div>
                  <span className="pm-live-dot pm-live-dot-violet" />
                </div>
                <div className="pm-intelligence-tile pm-tile-three">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.16em] text-emerald-300">
                      Workforce Intelligence
                    </p>
                    <p className="mt-1 text-sm font-bold text-white">
                      Attendance and HR operations
                    </p>
                  </div>
                  <span className="pm-live-dot pm-live-dot-green" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="relative z-10 flex items-center justify-between border-t border-white/10 pt-4 text-xs text-slate-500">
          <span>
            PeopleMind AI
          </span>
          <span>
            Secure local HR workspace
          </span>
        </div>
      </section>
      <section className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden px-5 py-8 sm:px-8 lg:h-[100dvh] lg:min-h-0 lg:px-12">
        <div className="pm-right-grid absolute inset-0" />
        <div className="pm-light-orb pm-light-orb-one" />
        <div className="pm-light-orb pm-light-orb-two" />
        <div className="pm-security-ring pm-security-ring-one" />
        <div className="pm-security-ring pm-security-ring-two" />
        <div className="pm-security-ring pm-security-ring-three" />
        <div className="pm-right-beam" />
        <div className="pm-secure-chip pm-secure-chip-one">
          <span className="pm-chip-dot bg-emerald-400" />
          Local AI
        </div>
        <div className="pm-secure-chip pm-secure-chip-two">
          <span className="pm-chip-dot bg-cyan-400" />
          Encrypted Session
        </div>
        <div className="pm-secure-chip pm-secure-chip-three">
          <span className="pm-chip-dot bg-violet-400" />
          Human Review
        </div>
        <div className="pm-network-dot pm-network-dot-one" />
        <div className="pm-network-dot pm-network-dot-two" />
        <div className="pm-network-dot pm-network-dot-three" />
        <div className="pm-network-dot pm-network-dot-four" />
        <div className="relative z-10 w-full max-w-[420px]">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 font-black text-cyan-300">
              PM
            </div>
            <div>
              <p className="font-black text-slate-950">
                PeopleMind AI
              </p>
              <p className="text-xs text-slate-500">
                HR Intelligence and Management
              </p>
            </div>
          </div>
          <div className="pm-login-card pm-login-card-premium relative overflow-hidden rounded-[30px] bg-white/92 p-6 shadow-[0_28px_90px_rgba(15,23,42,0.15)] backdrop-blur-2xl sm:p-8">
            <div className="relative z-10">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.2em] text-sky-600">
                    Secure workspace access
                  </p>
                  <h2 className="mt-3 text-3xl font-black tracking-tight text-slate-950">
                    Welcome back
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    Sign in to your authorised
                    PeopleMind account.
                  </p>
                </div>
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-[11px] font-black text-cyan-300">
                  PM
                </div>
              </div>
              <div className="mt-7 flex items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50/80 px-4 py-3">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
                </span>
                <div>
                  <p className="text-xs font-black text-emerald-800">
                    Secure session gateway ready
                  </p>
                  <p className="mt-0.5 text-[11px] text-emerald-600">
                    Credentials are protected in transit.
                  </p>
                </div>
              </div>
              <form
                className="mt-7 space-y-5"
                onSubmit={
                  handleSubmit
                }
              >
                <div>
                  <label
                    className="text-xs font-bold uppercase tracking-wide text-slate-600"
                    htmlFor="email"
                  >
                    Account email
                  </label>
                  <div className="relative mt-2">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex w-12 items-center justify-center text-sm font-black text-slate-400">
                      @
                    </div>
                    <input
                      autoComplete="username"
                      className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 py-3.5 pl-12 pr-4 text-sm font-medium text-slate-900 outline-none transition duration-200 placeholder:text-slate-400 focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100"
                      id="email"
                      onChange={(event) => {
                        setEmail(
                          event.target.value,
                        );
                      }}
                      placeholder="name@company.com"
                      required
                      type="email"
                      value={email}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between gap-3">
                    <label
                      className="text-xs font-bold uppercase tracking-wide text-slate-600"
                      htmlFor="password"
                    >
                      Password
                    </label>
                    <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                      Protected
                    </span>
                  </div>
                  <div className="relative mt-2">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex w-12 items-center justify-center text-sm font-black text-slate-400">
                      *
                    </div>
                    <input
                      autoComplete="current-password"
                      className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 py-3.5 pl-12 pr-20 text-sm font-medium text-slate-900 outline-none transition duration-200 placeholder:text-slate-400 focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100"
                      id="password"
                      minLength={8}
                      onChange={(event) => {
                        setPassword(
                          event.target.value,
                        );
                      }}
                      placeholder="Enter your password"
                      required
                      type={
                        showPassword
                          ? "text"
                          : "password"
                      }
                      value={password}
                    />
                    <button
                      className="absolute inset-y-0 right-0 px-4 text-xs font-bold text-slate-500 transition hover:text-slate-900"
                      onClick={() => {
                        setShowPassword(
                          (current) =>
                            !current,
                        );
                      }}
                      type="button"
                    >
                      {showPassword
                        ? "Hide"
                        : "Show"}
                    </button>
                  </div>
                </div>
                {errorMessage ? (
                  <div
                    className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700"
                    role="alert"
                  >
                    {errorMessage}
                  </div>
                ) : null}
                <button
                  className="pm-login-button relative flex w-full items-center justify-center overflow-hidden rounded-2xl bg-slate-950 px-5 py-3.5 text-sm font-black text-white shadow-lg shadow-slate-950/10 transition hover:-translate-y-0.5 hover:bg-slate-900 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={
                    isSubmitting
                  }
                  type="submit"
                >
                  <span className="relative z-10 flex items-center gap-3">
                    {isSubmitting ? (
                      <>
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                        Signing in...
                      </>
                    ) : (
                      <>
                        Sign in securely
                        <span className="text-cyan-300">
                          &gt;
                        </span>
                      </>
                    )}
                  </span>
                </button>
              </form>
              <div className="mt-7 flex items-center justify-center gap-2 border-t border-slate-100 pt-5">
                <span className="h-1.5 w-1.5 rounded-full bg-slate-300" />
                <p className="text-center text-[11px] leading-5 text-slate-400">
                  Access token remains in the
                  current browser session only.
                </p>
              </div>
            </div>
          </div>
          <p className="mt-4 text-center text-[11px] leading-5 text-slate-400">
            Local-first HR intelligence with
            human oversight.
          </p>
        </div>
      </section>
    </main>
  );
}

import { useEffect } from "react";
import { useAuth } from "../auth/useAuth";
const modules = [
  {
    title: "Document Assistant",
    description:
      "Upload HR documents and receive grounded answers with page citations.",
    status: "Available",
    statusClass:
      "bg-emerald-100 text-emerald-700",
  },
  {
    title: "CV Screening",
    description:
      "Compare candidates against job requirements with human review.",
    status: "Planned",
    statusClass:
      "bg-amber-100 text-amber-700",
  },
  {
    title: "Attendance Management",
    description:
      "Manage attendance records, leave status and basic summaries.",
    status: "Planned",
    statusClass:
      "bg-amber-100 text-amber-700",
  },
  {
    title: "Email Assistant",
    description:
      "Generate professional HR drafts that require explicit approval.",
    status: "Planned",
    statusClass:
      "bg-amber-100 text-amber-700",
  },
];
export function DashboardPage() {
  const {
    user,
    logout,
  } = useAuth();
  useEffect(() => {
    document.title =
      "Dashboard | PeopleMind AI";
  }, []);
  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 font-black text-sky-400">
              PM
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                PeopleMind AI
              </h1>
              <p className="text-sm text-slate-500">
                HR Intelligence and Management
                Assistant
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden text-right sm:block">
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
      <main className="mx-auto max-w-7xl px-6 py-10">
        <section className="overflow-hidden rounded-3xl bg-slate-950 px-8 py-10 text-white shadow-xl">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-400">
              Local-first HR intelligence
            </p>
            <h2 className="mt-4 text-3xl font-bold leading-tight md:text-5xl">
              Welcome to your secure PeopleMind
              workspace.
            </h2>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">
              Your authenticated dashboard is
              connected to the PeopleMind AI
              backend. Document intelligence is
              ready for frontend integration.
            </p>
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            <span className="rounded-full bg-emerald-400/15 px-4 py-2 text-sm font-semibold text-emerald-300">
              Secure session active
            </span>
            <span className="rounded-full bg-sky-400/15 px-4 py-2 text-sm font-semibold text-sky-300">
              Local AI configured
            </span>
            <span className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-slate-200">
              Document RAG ready
            </span>
          </div>
        </section>
        <section className="mt-10">
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-slate-950">
              HR modules
            </h3>
            <p className="mt-1 text-slate-600">
              Build and verify each module through
              the PeopleMind AI roadmap.
            </p>
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            {modules.map((module) => (
              <article
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                key={module.title}
              >
                <div className="flex items-start justify-between gap-4">
                  <h4 className="text-lg font-bold text-slate-900">
                    {module.title}
                  </h4>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${module.statusClass}`}
                  >
                    {module.status}
                  </span>
                </div>
                <p className="mt-3 leading-6 text-slate-600">
                  {module.description}
                </p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

import {
  useEffect,
} from "react";
import { Link } from "react-router-dom";
const modules = [
  {
    title: "Document Assistant",
    description:
      "Upload HR documents and receive grounded answers with page citations.",
    status: "Available",
    statusClass:
      "bg-emerald-100 text-emerald-700",
    href: "/documents",
  },
  {
    title: "CV Screening",
    description:
      "Compare candidates against job requirements with human review.",
    status: "Planned",
    statusClass:
      "bg-amber-100 text-amber-700",
    href: null,
  },
  {
    title: "Attendance Management",
    description:
      "Manage attendance records, leave status and basic summaries.",
    status: "Planned",
    statusClass:
      "bg-amber-100 text-amber-700",
    href: null,
  },
  {
    title: "Email Assistant",
    description:
      "Generate professional HR drafts that require explicit approval.",
    status: "Planned",
    statusClass:
      "bg-amber-100 text-amber-700",
    href: null,
  },
];
export function DashboardPage() {
  useEffect(() => {
    document.title =
      "Dashboard | PeopleMind AI";
  }, []);
  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <section className="overflow-hidden rounded-3xl bg-slate-950 px-8 py-10 text-white shadow-xl">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-400">
            Local-first HR intelligence
          </p>
          <h1 className="mt-4 text-3xl font-bold leading-tight md:text-5xl">
            Welcome to your secure PeopleMind
            workspace.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">
            Use local AI to work with private HR
            information while keeping human review
            at the centre of every important
            decision.
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
          <h2 className="text-2xl font-bold text-slate-950">
            HR modules
          </h2>
          <p className="mt-1 text-slate-600">
            Access available modules and follow the
            PeopleMind AI development roadmap.
          </p>
        </div>
        <div className="grid gap-5 md:grid-cols-2">
          {modules.map((module) => (
            <article
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              key={module.title}
            >
              <div className="flex items-start justify-between gap-4">
                <h3 className="text-lg font-bold text-slate-900">
                  {module.title}
                </h3>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${module.statusClass}`}
                >
                  {module.status}
                </span>
              </div>
              <p className="mt-3 leading-6 text-slate-600">
                {module.description}
              </p>
              <div className="mt-6">
                {module.href ? (
                  <Link
                    className="inline-flex rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                    to={module.href}
                  >
                    Open module
                  </Link>
                ) : (
                  <span className="text-sm font-medium text-slate-400">
                    Coming in a later stage
                  </span>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

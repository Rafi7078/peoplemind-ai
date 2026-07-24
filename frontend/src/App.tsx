const modules = [
  {
    title: "Document Assistant",
    description: "Ask questions from HR policies and employee handbooks.",
    status: "Planned",
  },
  {
    title: "CV Screening",
    description: "Analyse and rank candidates against a job description.",
    status: "Planned",
  },
  {
    title: "Attendance Management",
    description: "Manage employees, attendance records and reports.",
    status: "Planned",
  },
  {
    title: "Email Assistant",
    description: "Generate, review and approve professional HR emails.",
    status: "Planned",
  },
];
function App() {
  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900">
              PeopleMind AI
            </h1>
            <p className="text-sm text-slate-500">
              HR Intelligence and Management Assistant
            </p>
          </div>
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">
            Frontend Running
          </span>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-10">
        <section className="rounded-2xl bg-slate-900 px-8 py-10 text-white shadow-lg">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-sky-300">
            PeopleMind AI v0.1.0
          </p>
          <h2 className="max-w-3xl text-3xl font-bold leading-tight md:text-4xl">
            A privacy-focused intelligent workspace for modern HR teams.
          </h2>
          <p className="mt-4 max-w-2xl text-slate-300">
            The project foundation is ready. Each HR module will be developed
            and tested step by step.
          </p>
        </section>
        <section className="mt-10">
          <div className="mb-5">
            <h3 className="text-2xl font-bold text-slate-900">
              Project Modules
            </h3>
            <p className="mt-1 text-slate-600">
              Current development roadmap for the PeopleMind AI platform.
            </p>
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            {modules.map((module) => (
              <article
                key={module.title}
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <h4 className="text-lg font-semibold text-slate-900">
                    {module.title}
                  </h4>
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
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
export default App;

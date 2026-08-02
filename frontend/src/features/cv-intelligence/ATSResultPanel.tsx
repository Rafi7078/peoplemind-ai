
import type {
  CandidateATSCheckStatus,
  CandidateATSResult,
} from "./types";
type ATSResultPanelProps = {
  result: CandidateATSResult | null;
  isLoading: boolean;
};
const categoryMaximumScores: Record<
  string,
  number
> = {
  machine_readability: 25,
  contact_information: 15,
  standard_sections: 20,
  content_structure: 20,
  date_consistency: 10,
  layout_and_parsing: 10,
};
function displayCategory(
  value: string,
): string {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}
function checkStatusClass(
  status: CandidateATSCheckStatus,
): string {
  switch (status) {
    case "pass":
      return (
        "border-emerald-200 bg-emerald-50 text-emerald-700"
      );
    case "warning":
      return (
        "border-amber-200 bg-amber-50 text-amber-700"
      );
    case "fail":
      return (
        "border-red-200 bg-red-50 text-red-700"
      );
  }
}
function scoreClass(
  score: number,
): string {
  if (score >= 85) {
    return (
      "border-emerald-200 bg-emerald-50 text-emerald-700"
    );
  }
  if (score >= 70) {
    return (
      "border-sky-200 bg-sky-50 text-sky-700"
    );
  }
  if (score >= 50) {
    return (
      "border-amber-200 bg-amber-50 text-amber-700"
    );
  }
  return (
    "border-red-200 bg-red-50 text-red-700"
  );
}
export function ATSResultPanel({
  result,
  isLoading,
}: ATSResultPanelProps) {
  if (isLoading) {
    return (
      <section className="mt-7 rounded-3xl border border-slate-200 bg-white p-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
          ATS compatibility
        </p>
        <div className="mt-4 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">
          Loading ATS analysis...
        </div>
      </section>
    );
  }
  if (!result) {
    return (
      <section className="mt-7 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
          ATS compatibility
        </p>
        <h3 className="mt-2 text-xl font-bold text-slate-900">
          ATS analysis not completed
        </h3>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          Run ATS analysis to check machine
          readability, contact details, standard
          sections, content structure, dates and
          parsing risks.
        </p>
      </section>
    );
  }
  const passedChecks =
    result.checks.filter(
      (check) =>
        check.status === "pass",
    ).length;
  const warningChecks =
    result.checks.filter(
      (check) =>
        check.status === "warning",
    ).length;
  const failedChecks =
    result.checks.filter(
      (check) =>
        check.status === "fail",
    ).length;
  return (
    <section className="mt-7 rounded-3xl border border-slate-200 bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
            ATS compatibility
          </p>
          <h3 className="mt-2 text-2xl font-bold text-slate-950">
            ATS Compatibility Report
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            This score evaluates CV structure and
            machine readability. It does not measure
            suitability for a particular job and does
            not make a hiring decision.
          </p>
        </div>
        <div
          className={[
            "min-w-36 rounded-2xl border px-5 py-4 text-center",
            scoreClass(
              result.score,
            ),
          ].join(" ")}
        >
          <p className="text-4xl font-bold">
            {result.score}
          </p>
          <p className="mt-1 text-xs font-bold uppercase tracking-wide">
            Out of 100
          </p>
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        <span className="rounded-full bg-slate-950 px-3 py-1.5 text-xs font-bold text-white">
          {result.rating}
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700">
          Risk:{" "}
          {displayCategory(
            result.risk_level,
          )}
        </span>
        <span className="rounded-full bg-emerald-100 px-3 py-1.5 text-xs font-bold text-emerald-700">
          {passedChecks} passed
        </span>
        <span className="rounded-full bg-amber-100 px-3 py-1.5 text-xs font-bold text-amber-700">
          {warningChecks} warning
        </span>
        <span className="rounded-full bg-red-100 px-3 py-1.5 text-xs font-bold text-red-700">
          {failedChecks} failed
        </span>
      </div>
      <div className="mt-7">
        <h4 className="text-lg font-bold text-slate-900">
          Category scores
        </h4>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Object.entries(
            result.category_scores,
          ).map(
            ([
              category,
              score,
            ]) => (
              <article
                className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                key={category}
              >
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  {displayCategory(
                    category,
                  )}
                </p>
                <p className="mt-2 text-2xl font-bold text-slate-950">
                  {score}
                  <span className="text-sm font-semibold text-slate-400">
                    {" "}/{" "}
                    {categoryMaximumScores[
                      category
                    ] ?? 0}
                  </span>
                </p>
              </article>
            ),
          )}
        </div>
      </div>
      <div className="mt-7">
        <h4 className="text-lg font-bold text-slate-900">
          ATS checks
        </h4>
        <div className="mt-4 space-y-3">
          {result.checks.map(
            (check) => (
              <article
                className="rounded-2xl border border-slate-200 p-4"
                key={check.check_id}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
                      {check.category}
                    </p>
                    <h5 className="mt-1 font-bold text-slate-900">
                      {check.title}
                    </h5>
                  </div>
                  <span
                    className={[
                      "rounded-full border px-3 py-1 text-xs font-bold uppercase",
                      checkStatusClass(
                        check.status,
                      ),
                    ].join(" ")}
                  >
                    {check.status}
                    {" | "}
                    {check.points_awarded}
                    /
                    {check.max_points}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  {check.message}
                </p>
                {check.evidence.length
                > 0 ? (
                  <div className="mt-3 space-y-1">
                    {check.evidence.map(
                      (
                        evidence,
                        index,
                      ) => (
                        <p
                          className="text-xs leading-5 text-slate-500"
                          key={`${check.check_id}-${index}`}
                        >
                          - {evidence}
                        </p>
                      ),
                    )}
                  </div>
                ) : null}
              </article>
            ),
          )}
        </div>
      </div>
      <div className="mt-7 rounded-2xl border border-amber-200 bg-amber-50 p-5">
        <h4 className="font-bold text-amber-900">
          Improvement suggestions
        </h4>
        <div className="mt-3 space-y-2">
          {result.suggestions.map(
            (
              suggestion,
              index,
            ) => (
              <p
                className="text-sm leading-6 text-amber-800"
                key={`suggestion-${index}`}
              >
                {index + 1}.{" "}
                {suggestion}
              </p>
            ),
          )}
        </div>
      </div>
      <p className="mt-4 text-xs text-slate-400">
        Engine: {result.engine_version}
      </p>
    </section>
  );
}

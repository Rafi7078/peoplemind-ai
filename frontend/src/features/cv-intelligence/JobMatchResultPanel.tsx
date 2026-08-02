
import type {
  JobMatchCheckStatus,
  JobMatchResult,
} from "./types";
type JobMatchResultPanelProps = {
  result: JobMatchResult | null;
  isLoading: boolean;
  jobTitle: string;
};
const categoryCheckIds: Record<
  string,
  string
> = {
  skill_match: "skill-match",
  role_relevance: "role-relevance",
  experience_requirement:
    "experience-requirement",
  education_requirement:
    "education-requirement",
  supporting_evidence:
    "supporting-evidence",
};
const categoryMaximumScores: Record<
  string,
  number
> = {
  skill_match: 45,
  role_relevance: 20,
  experience_requirement: 15,
  education_requirement: 10,
  supporting_evidence: 10,
};
function displayValue(
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
function statusClass(
  status: JobMatchCheckStatus,
): string {
  switch (status) {
    case "match":
      return (
        "border-emerald-200 bg-emerald-50 text-emerald-700"
      );
    case "partial":
      return (
        "border-amber-200 bg-amber-50 text-amber-700"
      );
    case "missing":
      return (
        "border-red-200 bg-red-50 text-red-700"
      );
    case "not_specified":
      return (
        "border-slate-200 bg-slate-100 text-slate-600"
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
  if (score >= 55) {
    return (
      "border-amber-200 bg-amber-50 text-amber-700"
    );
  }
  return (
    "border-red-200 bg-red-50 text-red-700"
  );
}
export function JobMatchResultPanel({
  result,
  isLoading,
  jobTitle,
}: JobMatchResultPanelProps) {
  if (isLoading) {
    return (
      <section className="mt-7 rounded-3xl border border-slate-200 bg-white p-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Job match and screening
        </p>
        <div className="mt-4 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">
          Loading job-match analysis...
        </div>
      </section>
    );
  }
  if (!result) {
    return (
      <section className="mt-7 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Job match and screening
        </p>
        <h3 className="mt-2 text-xl font-bold text-slate-900">
          Job-match analysis not completed
        </h3>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          Analyze this candidate against{" "}
          <strong>{jobTitle}</strong> to compare
          skills, role relevance, experience,
          education and supporting evidence.
        </p>
        <p className="mt-3 text-xs leading-5 text-slate-400">
          A structured candidate profile is
          required. The result supports human
          review and does not make a hiring or
          rejection decision.
        </p>
      </section>
    );
  }
  const matchedChecks =
    result.checks.filter(
      (check) =>
        check.status === "match",
    ).length;
  const partialChecks =
    result.checks.filter(
      (check) =>
        check.status === "partial",
    ).length;
  const missingChecks =
    result.checks.filter(
      (check) =>
        check.status === "missing",
    ).length;
  return (
    <section className="mt-7 rounded-3xl border border-slate-200 bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Job match and screening
          </p>
          <h3 className="mt-2 text-2xl font-bold text-slate-950">
            Candidate-Job Match Report
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            Compared against{" "}
            <strong>{jobTitle}</strong>. Candidate
            name, contact information and protected
            attributes are not used in the score.
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
        <span className="rounded-full bg-violet-100 px-3 py-1.5 text-xs font-bold text-violet-700">
          {displayValue(
            result.recommendation,
          )}
        </span>
        <span className="rounded-full bg-emerald-100 px-3 py-1.5 text-xs font-bold text-emerald-700">
          {matchedChecks} matched
        </span>
        <span className="rounded-full bg-amber-100 px-3 py-1.5 text-xs font-bold text-amber-700">
          {partialChecks} partial
        </span>
        <span className="rounded-full bg-red-100 px-3 py-1.5 text-xs font-bold text-red-700">
          {missingChecks} missing
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
            ]) => {
              const relatedCheck =
                result.checks.find(
                  (check) =>
                    check.check_id
                    === categoryCheckIds[
                      category
                    ],
                );
              const isNotSpecified =
                relatedCheck?.status
                === "not_specified";
              return (
                <article
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                  key={category}
                >
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    {displayValue(
                      category,
                    )}
                  </p>
                  {isNotSpecified ? (
                    <>
                      <p className="mt-2 text-2xl font-bold text-slate-500">
                        N/A
                      </p>
                      <p className="mt-1 text-xs font-semibold text-slate-400">
                        Not scored
                      </p>
                    </>
                  ) : (
                    <p className="mt-2 text-2xl font-bold text-slate-950">
                      {score}
                      <span className="text-sm font-semibold text-slate-400">
                        {" "}/{" "}
                        {categoryMaximumScores[
                          category
                        ] ?? 0}
                      </span>
                    </p>
                  )}
                </article>
              );
            },
          )}
        </div>
      </div>
      <div className="mt-7 rounded-2xl border border-violet-200 bg-violet-50 p-5">
        <h4 className="font-bold text-violet-950">
          Recognized job requirements
        </h4>
        <div className="mt-3 grid gap-3 text-sm text-violet-800 sm:grid-cols-2">
          <p>
            <strong>Skills:</strong>{" "}
            {result.requirements
              .recognized_job_skills
              ?.join(", ")
            || "No explicit skills recognized"}
          </p>
          <p>
            <strong>Role family:</strong>{" "}
            {result.requirements
              .job_role_groups
              ?.join(", ")
            || "Not specified"}
          </p>
          <p>
            <strong>Minimum experience:</strong>{" "}
            {result.requirements
              .minimum_experience_years
            !== null
            && result.requirements
              .minimum_experience_years
            !== undefined
              ? `${result.requirements.minimum_experience_years} year(s)`
              : "Not specified"}
          </p>
          <p>
            <strong>Education:</strong>{" "}
            {result.requirements
              .education_requirement
            || "Not specified"}
          </p>
        </div>
      </div>
      <div className="mt-7">
        <h4 className="text-lg font-bold text-slate-900">
          Match checks
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
                      statusClass(
                        check.status,
                      ),
                    ].join(" ")}
                  >
                    {displayValue(
                      check.status,
                    )}
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
      <div className="mt-7 grid gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
          <h4 className="font-bold text-emerald-900">
            Matched requirements
          </h4>
          {result.matched_requirements.length
          > 0 ? (
            <div className="mt-3 space-y-2">
              {result.matched_requirements.map(
                (
                  requirement,
                  index,
                ) => (
                  <p
                    className="text-sm leading-6 text-emerald-800"
                    key={`matched-${index}`}
                  >
                    {index + 1}.{" "}
                    {requirement}
                  </p>
                ),
              )}
            </div>
          ) : (
            <p className="mt-3 text-sm text-emerald-800">
              No confirmed requirement match was
              recorded.
            </p>
          )}
        </article>
        <article className="rounded-2xl border border-red-200 bg-red-50 p-5">
          <h4 className="font-bold text-red-900">
            Missing or unconfirmed requirements
          </h4>
          {result.missing_requirements.length
          > 0 ? (
            <div className="mt-3 space-y-2">
              {result.missing_requirements.map(
                (
                  requirement,
                  index,
                ) => (
                  <p
                    className="text-sm leading-6 text-red-800"
                    key={`missing-${index}`}
                  >
                    {index + 1}.{" "}
                    {requirement}
                  </p>
                ),
              )}
            </div>
          ) : (
            <p className="mt-3 text-sm text-red-800">
              No missing recognized requirement
              was recorded.
            </p>
          )}
        </article>
      </div>
      <div className="mt-7 rounded-2xl border border-slate-200 bg-slate-50 p-5">
        <h4 className="font-bold text-slate-900">
          Human-review notes
        </h4>
        <div className="mt-3 space-y-2">
          {result.notes.map(
            (
              note,
              index,
            ) => (
              <p
                className="text-sm leading-6 text-slate-600"
                key={`note-${index}`}
              >
                {index + 1}. {note}
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

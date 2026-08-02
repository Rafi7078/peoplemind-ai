
import axios from "axios";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  listJobCandidateRanking,
  updateJobCandidateReview,
} from "./api";
import type {
  JobCandidateRankingItem,
  JobProfile,
  JobReviewStatus,
} from "./types";
type JobRankingDashboardProps = {
  jobs: JobProfile[];
  initialJobId: number | null;
  onOpenCandidate: (
    jobId: number,
    candidateId: number,
  ) => void;
};
const reviewOptions: Array<{
  value: JobReviewStatus;
  label: string;
}> = [
  {
    value: "not_reviewed",
    label: "Not reviewed",
  },
  {
    value: "in_review",
    label: "In review",
  },
  {
    value: "shortlisted",
    label: "Shortlisted",
  },
  {
    value: "on_hold",
    label: "On hold",
  },
  {
    value: "not_selected",
    label: "Not selected",
  },
];
function displayStatus(
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
function formatDate(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(
    new Date(value),
  );
}
function getErrorMessage(
  error: unknown,
  fallbackMessage: string,
): string {
  if (
    axios.isAxiosError(error)
  ) {
    const detail =
      error.response?.data?.detail;
    if (
      typeof detail === "string"
      && detail.trim()
    ) {
      return detail;
    }
  }
  return fallbackMessage;
}
function reviewStatusClass(
  status: JobReviewStatus,
): string {
  switch (status) {
    case "shortlisted":
      return (
        "bg-emerald-100 text-emerald-700"
      );
    case "in_review":
      return (
        "bg-sky-100 text-sky-700"
      );
    case "on_hold":
      return (
        "bg-amber-100 text-amber-700"
      );
    case "not_selected":
      return (
        "bg-red-100 text-red-700"
      );
    case "not_reviewed":
      return (
        "bg-slate-100 text-slate-600"
      );
  }
}
function matchScoreClass(
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
export function JobRankingDashboard({
  jobs,
  initialJobId,
  onOpenCandidate,
}: JobRankingDashboardProps) {
  const [
    selectedJobId,
    setSelectedJobId,
  ] = useState<number | null>(
    () =>
      initialJobId
      ?? jobs[0]?.id
      ?? null,
  );
  const [
    rankingItems,
    setRankingItems,
  ] = useState<
    JobCandidateRankingItem[]
  >([]);
  const [
    selectedCandidateId,
    setSelectedCandidateId,
  ] = useState<number | null>(
    null,
  );
  const [
    reviewStatus,
    setReviewStatus,
  ] = useState<JobReviewStatus>(
    "not_reviewed",
  );
  const [
    reviewNotes,
    setReviewNotes,
  ] = useState("");
  const [
    isLoading,
    setIsLoading,
  ] = useState(
    selectedJobId !== null,
  );
  const [
    isSaving,
    setIsSaving,
  ] = useState(false);
  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );
  const [
    activityMessage,
    setActivityMessage,
  ] = useState<string | null>(
    null,
  );
  const selectedJob = useMemo(
    () =>
      jobs.find(
        (job) =>
          job.id
          === selectedJobId,
      )
      ?? null,
    [
      jobs,
      selectedJobId,
    ],
  );
  const selectedItem = useMemo(
    () =>
      rankingItems.find(
        (item) =>
          item.candidate.id
          === selectedCandidateId,
      )
      ?? null,
    [
      rankingItems,
      selectedCandidateId,
    ],
  );
  const analyzedCount =
    rankingItems.filter(
      (item) =>
        item.analysis_status
        === "analyzed",
    ).length;
  const shortlistedCount =
    rankingItems.filter(
      (item) =>
        item.review_status
        === "shortlisted",
    ).length;
  const pendingReviewCount =
    rankingItems.filter(
      (item) =>
        item.review_status
        === "not_reviewed",
    ).length;
  useEffect(() => {
    if (
      selectedJobId === null
    ) {
      return;
    }
    let isActive = true;
    listJobCandidateRanking(
      selectedJobId,
    )
      .then((result) => {
        if (!isActive) {
          return;
        }
        setRankingItems(result);
        const firstItem =
          result[0] ?? null;
        setSelectedCandidateId(
          firstItem?.candidate.id
          ?? null,
        );
        setReviewStatus(
          firstItem?.review_status
          ?? "not_reviewed",
        );
        setReviewNotes(
          firstItem?.review?.notes
          ?? "",
        );
      })
      .catch(
        (error: unknown) => {
          if (!isActive) {
            return;
          }
          setErrorMessage(
            getErrorMessage(
              error,
              "Could not load the candidate ranking.",
            ),
          );
        },
      )
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });
    return () => {
      isActive = false;
    };
  }, [selectedJobId]);
  function selectRankingItem(
    item: JobCandidateRankingItem,
  ): void {
    setErrorMessage(null);
    setActivityMessage(null);
    setSelectedCandidateId(
      item.candidate.id,
    );
    setReviewStatus(
      item.review_status,
    );
    setReviewNotes(
      item.review?.notes
      ?? "",
    );
  }
  function handleJobChange(
    value: string,
  ): void {
    const nextJobId = Number(value);
    if (
      !Number.isFinite(nextJobId)
    ) {
      return;
    }
    setErrorMessage(null);
    setActivityMessage(null);
    setIsLoading(true);
    setRankingItems([]);
    setSelectedCandidateId(null);
    setReviewStatus(
      "not_reviewed",
    );
    setReviewNotes("");
    setSelectedJobId(nextJobId);
  }
  async function handleSaveReview():
    Promise<void> {
    if (
      selectedJobId === null
      || selectedItem === null
    ) {
      return;
    }
    setErrorMessage(null);
    setActivityMessage(null);
    setIsSaving(true);
    try {
      const savedReview =
        await updateJobCandidateReview(
          selectedJobId,
          selectedItem.candidate.id,
          {
            status: reviewStatus,
            notes:
              reviewNotes.trim()
              || null,
          },
        );
      setRankingItems(
        (current) =>
          current.map(
            (item) =>
              item.candidate.id
              === selectedItem.candidate.id
                ? {
                    ...item,
                    review_status:
                      savedReview.status,
                    review:
                      savedReview,
                  }
                : item,
          ),
      );
      setReviewNotes(
        savedReview.notes
        ?? "",
      );
      setActivityMessage(
        "Human HR review saved successfully.",
      );
    } catch (error) {
      setErrorMessage(
        getErrorMessage(
          error,
          "Could not save the HR review.",
        ),
      );
    } finally {
      setIsSaving(false);
    }
  }
  if (jobs.length === 0) {
    return (
      <section className="mt-8 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
        <h2 className="text-2xl font-bold text-slate-900">
          No job profile available
        </h2>
        <p className="mt-2 text-slate-500">
          Create a job profile before opening
          candidate ranking and HR review.
        </p>
      </section>
    );
  }
  return (
    <section className="mt-8">
      <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <div className="grid gap-5 lg:grid-cols-[1fr_0.7fr] lg:items-end">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
              Human-reviewed candidate ranking
            </p>
            <h2 className="mt-2 text-3xl font-bold text-slate-950">
              Ranking &amp; HR Review
            </h2>
            <p className="mt-3 max-w-3xl leading-7 text-slate-600">
              Candidates are ranked only by their
              job-match score. ATS compatibility
              is shown for information and does
              not affect the ranking.
            </p>
          </div>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Job profile
            </span>
            <select
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                handleJobChange(
                  event.target.value,
                );
              }}
              value={
                selectedJobId
                ?? ""
              }
            >
              {jobs.map(
                (job) => (
                  <option
                    key={job.id}
                    value={job.id}
                  >
                    {job.title}
                  </option>
                ),
              )}
            </select>
          </label>
        </div>
      </article>
      {errorMessage ? (
        <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {errorMessage}
        </div>
      ) : null}
      {activityMessage ? (
        <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-semibold text-emerald-700">
          {activityMessage}
        </div>
      ) : null}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: "Assigned candidates",
            value:
              rankingItems.length,
          },
          {
            label: "Analyzed",
            value:
              analyzedCount,
          },
          {
            label: "Shortlisted",
            value:
              shortlistedCount,
          },
          {
            label: "Not reviewed",
            value:
              pendingReviewCount,
          },
        ].map((item) => (
          <article
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
            key={item.label}
          >
            <p className="text-sm font-semibold text-slate-500">
              {item.label}
            </p>
            <p className="mt-2 text-3xl font-bold text-slate-950">
              {item.value}
            </p>
          </article>
        ))}
      </div>
      <div className="mt-7 grid gap-7 lg:grid-cols-[0.9fr_1.1fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <h3 className="text-xl font-bold text-slate-950">
              Candidate ranking
            </h3>
            <p className="mt-1 text-sm text-slate-500">
              {selectedJob?.title
              ?? "Selected job"}
            </p>
          </div>
          {isLoading ? (
            <div className="mt-6 rounded-2xl bg-slate-50 p-7 text-center text-sm text-slate-500">
              Loading ranking...
            </div>
          ) : null}
          {!isLoading
          && rankingItems.length
          === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
              No candidate is assigned to this job.
            </div>
          ) : null}
          <div className="mt-6 space-y-3">
            {rankingItems.map(
              (item) => (
                <button
                  className={[
                    "w-full rounded-2xl border p-4 text-left transition",
                    item.candidate.id
                    === selectedCandidateId
                      ? "border-violet-400 bg-violet-50"
                      : "border-slate-200 hover:bg-slate-50",
                  ].join(" ")}
                  key={
                    item.candidate.id
                  }
                  onClick={() => {
                    selectRankingItem(
                      item,
                    );
                  }}
                  type="button"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-950 text-sm font-bold text-white">
                      {item.rank
                      !== null
                        ? `#${item.rank}`
                        : "-"}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-bold text-slate-900">
                        {item.candidate_name
                        ?? item.candidate
                          .original_name}
                      </p>
                      <p className="mt-1 truncate text-xs text-slate-500">
                        {item.candidate
                          .original_name}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {item.match ? (
                          <span
                            className={[
                              "rounded-full border px-2.5 py-1 text-xs font-bold",
                              matchScoreClass(
                                item.match.score,
                              ),
                            ].join(" ")}
                          >
                            Match{" "}
                            {item.match.score}/100
                          </span>
                        ) : (
                          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">
                            Not analyzed
                          </span>
                        )}
                        <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-bold text-indigo-600">
                          ATS{" "}
                          {item.ats_score
                          !== null
                            ? item.ats_score
                            : "N/A"}
                        </span>
                        <span
                          className={[
                            "rounded-full px-2.5 py-1 text-xs font-bold",
                            reviewStatusClass(
                              item.review_status,
                            ),
                          ].join(" ")}
                        >
                          {displayStatus(
                            item.review_status,
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ),
            )}
          </div>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          {!selectedItem ? (
            <div className="flex min-h-96 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
              Select a ranked candidate to review.
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
                    Human HR review
                  </p>
                  <h3 className="mt-2 text-2xl font-bold text-slate-950">
                    {selectedItem.candidate_name
                    ?? selectedItem.candidate
                      .original_name}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    {selectedItem.candidate
                      .original_name}
                  </p>
                </div>
                <span
                  className={[
                    "rounded-full px-3 py-1.5 text-xs font-bold",
                    reviewStatusClass(
                      selectedItem
                        .review_status,
                    ),
                  ].join(" ")}
                >
                  {displayStatus(
                    selectedItem
                      .review_status,
                  )}
                </span>
              </div>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <article className="rounded-2xl border border-violet-200 bg-violet-50 p-5">
                  <p className="text-xs font-bold uppercase tracking-wide text-violet-600">
                    Job match
                  </p>
                  {selectedItem.match ? (
                    <>
                      <p className="mt-2 text-3xl font-bold text-violet-950">
                        {selectedItem.match.score}
                        <span className="text-sm text-violet-500">
                          /100
                        </span>
                      </p>
                      <p className="mt-1 text-sm font-semibold text-violet-700">
                        {selectedItem.match.rating}
                      </p>
                    </>
                  ) : (
                    <p className="mt-2 font-bold text-violet-800">
                      Not analyzed
                    </p>
                  )}
                </article>
                <article className="rounded-2xl border border-indigo-200 bg-indigo-50 p-5">
                  <p className="text-xs font-bold uppercase tracking-wide text-indigo-600">
                    ATS compatibility
                  </p>
                  <p className="mt-2 text-3xl font-bold text-indigo-950">
                    {selectedItem.ats_score
                    !== null
                      ? selectedItem.ats_score
                      : "N/A"}
                  </p>
                  <p className="mt-1 text-xs text-indigo-600">
                    Informational only; not used
                    in job ranking.
                  </p>
                </article>
              </div>
              <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <label className="block">
                  <span className="text-sm font-bold text-slate-800">
                    Review status
                  </span>
                  <select
                    className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
                    onChange={(event) => {
                      setReviewStatus(
                        event.target.value as JobReviewStatus,
                      );
                    }}
                    value={
                      reviewStatus
                    }
                  >
                    {reviewOptions.map(
                      (option) => (
                        <option
                          key={option.value}
                          value={option.value}
                        >
                          {option.label}
                        </option>
                      ),
                    )}
                  </select>
                </label>
                <label className="mt-5 block">
                  <span className="text-sm font-bold text-slate-800">
                    Private HR notes
                  </span>
                  <textarea
                    className="mt-2 min-h-40 w-full resize-y rounded-xl border border-slate-300 bg-white px-4 py-3"
                    maxLength={5000}
                    onChange={(event) => {
                      setReviewNotes(
                        event.target.value,
                      );
                    }}
                    placeholder="Record interview observations, verification needs or the reason for the human review status."
                    value={
                      reviewNotes
                    }
                  />
                  <span className="mt-1 block text-right text-xs text-slate-400">
                    {reviewNotes.length}/5000
                  </span>
                </label>
                <div className="mt-5 flex flex-wrap gap-3">
                  <button
                    className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={
                      isSaving
                    }
                    onClick={() => {
                      void handleSaveReview();
                    }}
                    type="button"
                  >
                    {isSaving
                      ? "Saving review..."
                      : "Save HR review"}
                  </button>
                  {selectedJobId
                  !== null ? (
                    <button
                      className="rounded-xl border border-violet-300 px-5 py-3 text-sm font-semibold text-violet-700"
                      onClick={() => {
                        onOpenCandidate(
                          selectedJobId,
                          selectedItem
                            .candidate.id,
                        );
                      }}
                      type="button"
                    >
                      Open candidate evidence
                    </button>
                  ) : null}
                </div>
              </div>
              {selectedItem.review ? (
                <p className="mt-4 text-xs text-slate-400">
                  Last reviewed{" "}
                  {formatDate(
                    selectedItem.review
                      .reviewed_at,
                  )}
                  {" | "}Reviewer user ID:{" "}
                  {selectedItem.review
                    .reviewed_by_id}
                </p>
              ) : null}
              <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5">
                <p className="font-bold text-amber-900">
                  Human decision required
                </p>
                <p className="mt-2 text-sm leading-6 text-amber-800">
                  Review status is recorded by an
                  HR user. The system never
                  automatically shortlists, hires
                  or rejects a candidate, and the
                  status does not change the
                  candidate's job-match rank.
                </p>
              </div>
            </>
          )}
        </article>
      </div>
    </section>
  );
}

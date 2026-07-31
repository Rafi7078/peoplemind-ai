
import axios from "axios";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import type {
  FormEvent,
} from "react";
import {
  createJobProfile,
  fetchCandidateCVFile,
  listCandidateCVPages,
  listCandidateCVs,
  listJobProfiles,
  processCandidateCV,
  uploadCandidateCV,
} from "../features/cv-intelligence/api";
import type {
  CandidateCV,
  CandidateCVPagePreview,
  JobProfile,
  JobProfileCreate,
} from "../features/cv-intelligence/types";
type Section =
  | "overview"
  | "jobs"
  | "candidates";
const emptyJobForm: JobProfileCreate = {
  title: "",
  department: "",
  location: "",
  employment_type: "",
  description: "",
  status: "draft",
};
function formatBytes(
  size: number,
): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(
      size / 1024
    ).toFixed(1)} KB`;
  }
  return `${(
    size /
    (1024 * 1024)
  ).toFixed(1)} MB`;
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
function statusClass(
  status: string,
): string {
  switch (
    status.toLowerCase()
  ) {
    case "active":
    case "ready":
      return (
        "bg-emerald-100 " +
        "text-emerald-700"
      );
    case "uploaded":
    case "draft":
      return (
        "bg-amber-100 " +
        "text-amber-700"
      );
    case "processing":
      return (
        "bg-violet-100 " +
        "text-violet-700"
      );
    case "closed":
      return (
        "bg-slate-200 " +
        "text-slate-700"
      );
    case "needs_ocr":
    case "failed":
      return (
        "bg-red-100 " +
        "text-red-700"
      );
    default:
      return (
        "bg-slate-100 " +
        "text-slate-600"
      );
  }
}
function displayStatus(
  status: string,
): string {
  return status
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}
function getApiErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (
    !axios.isAxiosError(error)
  ) {
    return fallback;
  }
  if (
    error.code === "ECONNABORTED" ||
    error.code === "ETIMEDOUT"
  ) {
    return (
      "The request took too long. " +
      "Confirm that the backend server " +
      "is running and try again."
    );
  }
  if (!error.response) {
    return (
      "Backend server is not reachable. " +
      "Confirm that FastAPI is running."
    );
  }
  const responseData =
    error.response.data as {
      detail?: unknown;
    };
  if (
    typeof responseData.detail
    === "string"
  ) {
    return responseData.detail;
  }
  return fallback;
}
export function CVIntelligencePage() {
  const [
    activeSection,
    setActiveSection,
  ] = useState<Section>(
    "overview",
  );
  const [
    jobProfiles,
    setJobProfiles,
  ] = useState<JobProfile[]>(
    [],
  );
  const [
    candidates,
    setCandidates,
  ] = useState<CandidateCV[]>(
    [],
  );
  const [
    jobForm,
    setJobForm,
  ] = useState<JobProfileCreate>({
    ...emptyJobForm,
  });
  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(
    null,
  );
  const [
    fileInputKey,
    setFileInputKey,
  ] = useState(0);
  const [
    selectedCandidateId,
    setSelectedCandidateId,
  ] = useState<number | null>(
    null,
  );
  const [
    candidatePages,
    setCandidatePages,
  ] = useState<
    CandidateCVPagePreview[]
  >([]);
  const [
    isLoading,
    setIsLoading,
  ] = useState(true);
  const [
    isPageLoading,
    setIsPageLoading,
  ] = useState(false);
  const [
    busyAction,
    setBusyAction,
  ] = useState<string | null>(
    null,
  );
  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");
  const [
    activityMessage,
    setActivityMessage,
  ] = useState("");
  const selectedCandidate =
    useMemo(
      () =>
        candidates.find(
          (candidate) =>
            candidate.id
            === selectedCandidateId,
        ) ?? null,
      [
        candidates,
        selectedCandidateId,
      ],
    );
  const activeJobCount =
    useMemo(
      () =>
        jobProfiles.filter(
          (job) =>
            job.status === "active",
        ).length,
      [jobProfiles],
    );
  const readyCandidateCount =
    useMemo(
      () =>
        candidates.filter(
          (candidate) =>
            candidate.status
            === "ready",
        ).length,
      [candidates],
    );
  const needsOcrCount =
    useMemo(
      () =>
        candidates.filter(
          (candidate) =>
            candidate.status
            === "needs_ocr",
        ).length,
      [candidates],
    );
  useEffect(() => {
    document.title =
      "CV Intelligence | PeopleMind AI";
    let isActive = true;
    Promise.all([
      listJobProfiles(),
      listCandidateCVs(),
    ])
      .then(
        ([
          jobResult,
          candidateResult,
        ]) => {
          if (!isActive) {
            return;
          }
          setJobProfiles(
            jobResult,
          );
          setCandidates(
            candidateResult,
          );
          if (
            candidateResult.length > 0
          ) {
            setCandidatePages([]);
            setIsPageLoading(true);
            setSelectedCandidateId(
              candidateResult[0].id,
            );
          }
        },
      )
      .catch(
        (error: unknown) => {
          if (!isActive) {
            return;
          }
          setErrorMessage(
            getApiErrorMessage(
              error,
              "Could not load CV Intelligence data.",
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
  }, []);
  useEffect(() => {
    if (
      selectedCandidateId === null
    ) {
      return;
    }
    let isActive = true;
    listCandidateCVPages(
      selectedCandidateId,
    )
      .then((result) => {
        if (isActive) {
          setCandidatePages(
            result,
          );
        }
      })
      .catch(
        (error: unknown) => {
          if (!isActive) {
            return;
          }
          setErrorMessage(
            getApiErrorMessage(
              error,
              "Could not load extracted CV pages.",
            ),
          );
        },
      )
      .finally(() => {
        if (isActive) {
          setIsPageLoading(
            false,
          );
        }
      });
    return () => {
      isActive = false;
    };
  }, [selectedCandidateId]);
  function clearMessages(): void {
    setErrorMessage("");
    setActivityMessage("");
  }
  function updateJobField(
    field: keyof JobProfileCreate,
    value: string,
  ): void {
    setJobForm(
      (current) => ({
        ...current,
        [field]: value,
      }),
    );
  }
  async function handleCreateJob(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    clearMessages();
    if (
      jobForm.title.trim().length < 2
    ) {
      setErrorMessage(
        "Enter a valid job title.",
      );
      return;
    }
    if (
      jobForm.description
        .trim().length < 20
    ) {
      setErrorMessage(
        "Job description must contain " +
        "at least 20 characters.",
      );
      return;
    }
    setBusyAction(
      "create-job",
    );
    try {
      const createdJob =
        await createJobProfile({
          title:
            jobForm.title.trim(),
          department:
            jobForm.department
              ?.trim() || null,
          location:
            jobForm.location
              ?.trim() || null,
          employment_type:
            jobForm.employment_type
              ?.trim() || null,
          description:
            jobForm.description.trim(),
          status:
            jobForm.status,
        });
      setJobProfiles(
        (current) => [
          createdJob,
          ...current,
        ],
      );
      setJobForm({
        ...emptyJobForm,
      });
      setActivityMessage(
        "Job profile created successfully.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not create the job profile.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleUploadCandidate(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    clearMessages();
    if (!selectedFile) {
      setErrorMessage(
        "Select a candidate CV PDF first.",
      );
      return;
    }
    if (
      selectedFile.type
      && selectedFile.type
      !== "application/pdf"
    ) {
      setErrorMessage(
        "Only PDF candidate CVs are supported.",
      );
      return;
    }
    setBusyAction(
      "upload-candidate",
    );
    try {
      const uploadedCandidate =
        await uploadCandidateCV(
          selectedFile,
        );
      setCandidates(
        (current) => [
          uploadedCandidate,
          ...current,
        ],
      );
      setCandidatePages([]);
      setIsPageLoading(true);
      setSelectedCandidateId(
        uploadedCandidate.id,
      );
      setSelectedFile(null);
      setFileInputKey(
        (current) =>
          current + 1,
      );
      setActivityMessage(
        "Candidate CV uploaded successfully. " +
        "Process it to extract the CV text.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not upload the candidate CV.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleOpenOriginalCV(
    candidate: CandidateCV,
  ): Promise<void> {
    clearMessages();
    const previewWindow =
      window.open(
        "about:blank",
        "_blank",
      );
    if (!previewWindow) {
      setErrorMessage(
        "The browser blocked the CV viewer. " +
        "Allow pop-ups for this local application.",
      );
      return;
    }
    previewWindow.opener = null;
    previewWindow.document.title =
      "Loading candidate CV...";
    setBusyAction(
      `open-${candidate.id}`,
    );
    try {
      const fileBlob =
        await fetchCandidateCVFile(
          candidate.id,
        );
      const fileUrl =
        URL.createObjectURL(
          fileBlob,
        );
      previewWindow.location.replace(
        fileUrl,
      );
      window.setTimeout(
        () => {
          URL.revokeObjectURL(
            fileUrl,
          );
        },
        60_000,
      );
    } catch (error) {
      previewWindow.close();
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not open the original candidate CV.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleProcessCandidate(
    candidate: CandidateCV,
  ): Promise<void> {
    clearMessages();
    setBusyAction(
      `process-${candidate.id}`,
    );
    setCandidates(
      (current) =>
        current.map(
          (item) =>
            item.id === candidate.id
              ? {
                  ...item,
                  status: "processing",
                }
              : item,
        ),
    );
    try {
      const result =
        await processCandidateCV(
          candidate.id,
        );
      setCandidates(
        (current) =>
          current.map(
            (item) =>
              item.id === candidate.id
                ? {
                    ...item,
                    status:
                      result.status,
                    page_count:
                      result.page_count,
                  }
                : item,
          ),
      );
      setSelectedCandidateId(
        candidate.id,
      );
      setIsPageLoading(true);
      const pages =
        await listCandidateCVPages(
          candidate.id,
        );
      setCandidatePages(
        pages,
      );
      if (
        result.status === "needs_ocr"
      ) {
        setActivityMessage(
          "CV processing completed, but " +
          "no selectable text was found. " +
          "This CV requires OCR.",
        );
      } else {
        setActivityMessage(
          "CV text extracted successfully. " +
          `${result.text_pages} text page(s) and ` +
          `${result.total_characters} characters found.`,
        );
      }
    } catch (error) {
      setCandidates(
        (current) =>
          current.map(
            (item) =>
              item.id === candidate.id
                ? {
                    ...item,
                    status: "failed",
                  }
                : item,
          ),
      );
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not process the candidate CV.",
        ),
      );
    } finally {
      setBusyAction(null);
      setIsPageLoading(false);
    }
  }
  if (isLoading) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="font-semibold text-slate-700">
            Loading CV Intelligence...
          </p>
        </div>
      </main>
    );
  }
  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <section className="overflow-hidden rounded-3xl bg-slate-950 px-8 py-9 text-white shadow-xl">
        <div className="max-w-4xl">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-400">
            Human-reviewed recruitment intelligence
          </p>
          <h1 className="mt-4 text-3xl font-bold md:text-5xl">
            CV Intelligence
          </h1>
          <p className="mt-5 max-w-3xl leading-7 text-slate-300">
            Create job profiles, securely upload
            candidate CVs and prepare structured
            evidence for ATS analysis and
            job-matching workflows.
          </p>
        </div>
        <div className="mt-8 flex flex-wrap gap-3">
          <span className="rounded-full bg-sky-400/15 px-4 py-2 text-sm font-semibold text-sky-300">
            {jobProfiles.length} job profile(s)
          </span>
          <span className="rounded-full bg-emerald-400/15 px-4 py-2 text-sm font-semibold text-emerald-300">
            {candidates.length} candidate CV(s)
          </span>
          <span className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-slate-200">
            Human decision required
          </span>
        </div>
      </section>
      <section className="mt-7 flex flex-wrap gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
        {(
          [
            {
              key: "overview",
              label: "Overview",
            },
            {
              key: "jobs",
              label: "Job Profiles",
            },
            {
              key: "candidates",
              label: "Candidate CVs",
            },
          ] as const
        ).map((section) => (
          <button
            className={[
              "rounded-xl px-5 py-3 text-sm font-semibold transition",
              activeSection
              === section.key
                ? "bg-slate-950 text-white"
                : "text-slate-600 hover:bg-slate-100",
            ].join(" ")}
            key={section.key}
            onClick={() => {
              setActiveSection(
                section.key,
              );
            }}
            type="button"
          >
            {section.label}
          </button>
        ))}
      </section>
      {errorMessage ? (
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">
          {errorMessage}
        </div>
      ) : null}
      {activityMessage ? (
        <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-medium text-emerald-700">
          {activityMessage}
        </div>
      ) : null}
      {activeSection
      === "overview" ? (
        <section className="mt-8">
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold text-slate-500">
                Job profiles
              </p>
              <p className="mt-3 text-4xl font-bold text-slate-950">
                {jobProfiles.length}
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold text-slate-500">
                Active jobs
              </p>
              <p className="mt-3 text-4xl font-bold text-slate-950">
                {activeJobCount}
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold text-slate-500">
                CVs ready
              </p>
              <p className="mt-3 text-4xl font-bold text-slate-950">
                {readyCandidateCount}
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold text-slate-500">
                Needs OCR
              </p>
              <p className="mt-3 text-4xl font-bold text-slate-950">
                {needsOcrCount}
              </p>
            </article>
          </div>
          <div className="mt-7 grid gap-6 lg:grid-cols-2">
            <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
              <h2 className="text-xl font-bold text-slate-950">
                Current workflow
              </h2>
              <div className="mt-6 space-y-4">
                {[
                  "Create and review a job profile.",
                  "Upload one or more candidate CV PDFs.",
                  "Process each CV to extract page-wise text.",
                  "Run ATS compatibility analysis.",
                  "Match candidates against job requirements.",
                  "HR reviews evidence before any decision.",
                ].map(
                  (
                    step,
                    index,
                  ) => (
                    <div
                      className="flex gap-4"
                      key={step}
                    >
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-950 text-sm font-bold text-white">
                        {index + 1}
                      </span>
                      <p className="pt-1 leading-6 text-slate-600">
                        {step}
                      </p>
                    </div>
                  ),
                )}
              </div>
            </article>
            <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
              <h2 className="text-xl font-bold text-slate-950">
                Foundation status
              </h2>
              <div className="mt-6 space-y-4">
                {[
                  {
                    label:
                      "Secure CV PDF upload",
                    status:
                      "Available",
                  },
                  {
                    label:
                      "Duplicate detection",
                    status:
                      "Available",
                  },
                  {
                    label:
                      "Page-wise text extraction",
                    status:
                      "Available",
                  },
                  {
                    label:
                      "Scanned CV detection",
                    status:
                      "Available",
                  },
                  {
                    label:
                      "ATS scoring engine",
                    status:
                      "Next stage",
                  },
                  {
                    label:
                      "Job matching and ranking",
                    status:
                      "Next stage",
                  },
                ].map((item) => (
                  <div
                    className="flex items-center justify-between gap-4 rounded-xl bg-slate-50 px-4 py-3"
                    key={item.label}
                  >
                    <span className="text-sm font-medium text-slate-700">
                      {item.label}
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </article>
          </div>
        </section>
      ) : null}
      {activeSection === "jobs" ? (
        <section className="mt-8 grid gap-7 lg:grid-cols-[0.9fr_1.1fr]">
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              Create job profile
            </h2>
            <p className="mt-2 leading-6 text-slate-600">
              Add the original job description.
              Structured requirements and scoring
              weights will be added in the next
              stage.
            </p>
            <form
              className="mt-7 space-y-5"
              onSubmit={
                handleCreateJob
              }
            >
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Job title
                </span>
                <input
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
                  onChange={(event) => {
                    updateJobField(
                      "title",
                      event.target.value,
                    );
                  }}
                  placeholder="Software QA Engineer"
                  required
                  value={jobForm.title}
                />
              </label>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-semibold text-slate-700">
                    Department
                  </span>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
                    onChange={(event) => {
                      updateJobField(
                        "department",
                        event.target.value,
                      );
                    }}
                    placeholder="Engineering"
                    value={
                      jobForm.department
                      ?? ""
                    }
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-semibold text-slate-700">
                    Location
                  </span>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
                    onChange={(event) => {
                      updateJobField(
                        "location",
                        event.target.value,
                      );
                    }}
                    placeholder="Dhaka"
                    value={
                      jobForm.location
                      ?? ""
                    }
                  />
                </label>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-semibold text-slate-700">
                    Employment type
                  </span>
                  <select
                    className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
                    onChange={(event) => {
                      updateJobField(
                        "employment_type",
                        event.target.value,
                      );
                    }}
                    value={
                      jobForm.employment_type
                      ?? ""
                    }
                  >
                    <option value="">
                      Select type
                    </option>
                    <option value="Full-time">
                      Full-time
                    </option>
                    <option value="Part-time">
                      Part-time
                    </option>
                    <option value="Contract">
                      Contract
                    </option>
                    <option value="Internship">
                      Internship
                    </option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-semibold text-slate-700">
                    Status
                  </span>
                  <select
                    className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
                    onChange={(event) => {
                      updateJobField(
                        "status",
                        event.target.value,
                      );
                    }}
                    value={jobForm.status}
                  >
                    <option value="draft">
                      Draft
                    </option>
                    <option value="active">
                      Active
                    </option>
                    <option value="closed">
                      Closed
                    </option>
                  </select>
                </label>
              </div>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Job description
                </span>
                <textarea
                  className="mt-2 min-h-56 w-full resize-y rounded-xl border border-slate-300 px-4 py-3 leading-6 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
                  onChange={(event) => {
                    updateJobField(
                      "description",
                      event.target.value,
                    );
                  }}
                  placeholder="Paste the complete job description, required skills, experience and responsibilities..."
                  required
                  value={
                    jobForm.description
                  }
                />
              </label>
              <button
                className="w-full rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={
                  busyAction !== null
                }
                type="submit"
              >
                {busyAction
                === "create-job"
                  ? "Creating..."
                  : "Create job profile"}
              </button>
            </form>
          </article>
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-950">
                  Job profiles
                </h2>
                <p className="mt-1 text-slate-600">
                  {jobProfiles.length} profile(s)
                  available.
                </p>
              </div>
            </div>
            {jobProfiles.length === 0 ? (
              <div className="mt-7 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                No job profiles have been created.
              </div>
            ) : (
              <div className="mt-7 space-y-4">
                {jobProfiles.map(
                  (job) => (
                    <article
                      className="rounded-2xl border border-slate-200 p-5"
                      key={job.id}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <h3 className="text-lg font-bold text-slate-900">
                            {job.title}
                          </h3>
                          <p className="mt-1 text-sm text-slate-500">
                            {[
                              job.department,
                              job.location,
                              job.employment_type,
                            ]
                              .filter(Boolean)
                              .join(" ? ")
                              || "Additional details not provided"}
                          </p>
                        </div>
                        <span
                          className={[
                            "rounded-full px-3 py-1 text-xs font-bold",
                            statusClass(
                              job.status,
                            ),
                          ].join(" ")}
                        >
                          {displayStatus(
                            job.status,
                          )}
                        </span>
                      </div>
                      <p className="mt-4 line-clamp-4 whitespace-pre-wrap leading-6 text-slate-600">
                        {job.description}
                      </p>
                      <p className="mt-4 text-xs font-medium text-slate-400">
                        Created{" "}
                        {formatDate(
                          job.created_at,
                        )}
                      </p>
                    </article>
                  ),
                )}
              </div>
            )}
          </article>
        </section>
      ) : null}
      {activeSection
      === "candidates" ? (
        <section className="mt-8">
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <div className="grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end">
              <div>
                <h2 className="text-2xl font-bold text-slate-950">
                  Upload candidate CV
                </h2>
                <p className="mt-2 leading-6 text-slate-600">
                  Upload a selectable-text PDF.
                  Scanned PDFs will be marked as
                  requiring OCR.
                </p>
              </div>
              <form
                className="flex flex-col gap-3 sm:flex-row sm:items-center"
                onSubmit={
                  handleUploadCandidate
                }
              >
                <input
                  accept=".pdf,application/pdf"
                  className="block max-w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-950 file:px-4 file:py-2 file:font-semibold file:text-white"
                  key={fileInputKey}
                  onChange={(event) => {
                    setSelectedFile(
                      event.target.files?.[0]
                      ?? null,
                    );
                  }}
                  type="file"
                />
                <button
                  className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={
                    busyAction !== null
                  }
                  type="submit"
                >
                  {busyAction
                  === "upload-candidate"
                    ? "Uploading..."
                    : "Upload CV"}
                </button>
              </form>
            </div>
          </article>
          <div className="mt-7 grid gap-7 lg:grid-cols-[0.85fr_1.15fr]">
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div>
                <h2 className="text-xl font-bold text-slate-950">
                  Candidate CVs
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {candidates.length} uploaded
                  candidate(s)
                </p>
              </div>
              {candidates.length === 0 ? (
                <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                  No candidate CV has been uploaded.
                </div>
              ) : (
                <div className="mt-6 space-y-3">
                  {candidates.map(
                    (candidate) => {
                      const isSelected =
                        candidate.id
                        === selectedCandidateId;
                      return (
                        <button
                          className={[
                            "w-full rounded-2xl border p-4 text-left transition",
                            isSelected
                              ? "border-sky-400 bg-sky-50"
                              : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50",
                          ].join(" ")}
                          key={
                            candidate.id
                          }
                          onClick={() => {
                            setCandidatePages([]);
                            setIsPageLoading(true);
                            setSelectedCandidateId(
                              candidate.id,
                            );
                          }}
                          type="button"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="truncate font-semibold text-slate-900">
                                {
                                  candidate.original_name
                                }
                              </p>
                              <p className="mt-1 text-xs text-slate-500">
                                {formatBytes(
                                  candidate.size_bytes,
                                )}
                                {" ? "}
                                {formatDate(
                                  candidate.created_at,
                                )}
                              </p>
                            </div>
                            <span
                              className={[
                                "shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold",
                                statusClass(
                                  candidate.status,
                                ),
                              ].join(" ")}
                            >
                              {displayStatus(
                                candidate.status,
                              )}
                            </span>
                          </div>
                        </button>
                      );
                    },
                  )}
                </div>
              )}
            </article>
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              {!selectedCandidate ? (
                <div className="flex min-h-72 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                  Select a candidate CV to view
                  processing details.
                </div>
              ) : (
                <>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold uppercase tracking-wide text-sky-600">
                        Candidate CV
                      </p>
                      <h2 className="mt-2 break-words text-2xl font-bold text-slate-950">
                        {
                          selectedCandidate.original_name
                        }
                      </h2>
                      <p className="mt-2 text-sm text-slate-500">
                        {formatBytes(
                          selectedCandidate.size_bytes,
                        )}
                        {" ? "}
                        {selectedCandidate.page_count
                        !== null
                          ? `${selectedCandidate.page_count} page(s)`
                          : "Not processed"}
                      </p>
                    </div>
                    <span
                      className={[
                        "rounded-full px-3 py-1 text-xs font-bold",
                        statusClass(
                          selectedCandidate.status,
                        ),
                      ].join(" ")}
                    >
                      {displayStatus(
                        selectedCandidate.status,
                      )}
                    </span>
                  </div>
                  {selectedCandidate.status
                  === "needs_ocr" ? (
                    <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-700">
                      No selectable text was found.
                      This appears to be a scanned or
                      image-based CV and requires OCR.
                    </div>
                  ) : null}
                  <div className="mt-6 flex flex-wrap gap-3">
                    <button
                      className="rounded-xl bg-sky-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={
                        busyAction !== null
                      }
                      onClick={() => {
                        void handleOpenOriginalCV(
                          selectedCandidate,
                        );
                      }}
                      type="button"
                    >
                      {busyAction
                      === `open-${selectedCandidate.id}`
                        ? "Opening..."
                        : "Open original CV"}
                    </button>
                    <button
                      className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={
                        busyAction !== null
                      }
                      onClick={() => {
                        void handleProcessCandidate(
                          selectedCandidate,
                        );
                      }}
                      type="button"
                    >
                      {busyAction
                      === `process-${selectedCandidate.id}`
                        ? "Processing..."
                        : selectedCandidate.status
                          === "ready"
                          ? "Process again"
                          : "Process CV"}
                    </button>
                  </div>
                  <details className="mt-7 border-t border-slate-200 pt-6">
                    <summary className="cursor-pointer rounded-xl bg-slate-100 px-4 py-3 font-semibold text-slate-800 transition hover:bg-slate-200">
                      Show extraction audit (raw text)
                    </summary>
                    <p className="mt-4 text-sm leading-6 text-slate-500">
                      This technical view shows layout-aware
                      text returned by the PDF parser. Use the
                      original CV for normal human review.
                    </p>
                    <div className="mt-5">
                    <div className="flex items-center justify-between gap-4">
                      <h3 className="text-lg font-bold text-slate-900">
                        Extracted page text
                      </h3>
                      <span className="text-sm text-slate-500">
                        {candidatePages.length} page(s)
                      </span>
                    </div>
                    {isPageLoading ? (
                      <div className="mt-5 rounded-xl bg-slate-50 p-5 text-sm text-slate-500">
                        Loading extracted pages...
                      </div>
                    ) : null}
                    {!isPageLoading
                    && candidatePages.length
                    === 0 ? (
                      <div className="mt-5 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
                        Process this CV to extract and
                        preview page text.
                      </div>
                    ) : null}
                    {!isPageLoading
                    && candidatePages.length
                    > 0 ? (
                      <div className="mt-5 space-y-4">
                        {candidatePages.map(
                          (page) => (
                            <article
                              className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
                              key={
                                page.page_number
                              }
                            >
                              <div className="flex items-center justify-between gap-4">
                                <h4 className="font-bold text-slate-800">
                                  Page{" "}
                                  {
                                    page.page_number
                                  }
                                </h4>
                                <span className="text-xs font-medium text-slate-500">
                                  {
                                    page.char_count
                                  }{" "}
                                  characters
                                </span>
                              </div>
                              <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap break-words font-sans text-sm leading-6 text-slate-600">
                                {page.text
                                || "No selectable text found on this page."}
                              </pre>
                            </article>
                          ),
                        )}
                      </div>
                    ) : null}
                  </div>
                  </details>
                </>
              )}
            </article>
          </div>
        </section>
      ) : null}
    </main>
  );
}

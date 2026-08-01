
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
  CandidateProfilePanel,
} from "../features/cv-intelligence/CandidateProfilePanel";
import {
  assignCandidateToJob,
  createJobProfile,
  deleteCandidatePermanently,
  deleteJobProfile,
  extractCandidateProfile,
  fetchCandidateCVFile,
  getCandidateProfile,
  listCandidateCVPages,
  listCandidateCVs,
  listJobCandidateCVs,
  listJobProfiles,
  listUnassignedCandidateCVs,
  processCandidateCV,
  removeCandidateFromJob,
  updateJobProfile,
  uploadCandidateCV,
} from "../features/cv-intelligence/api";
import type {
  CandidateCV,
  CandidateCVPagePreview,
  CandidateProfile,
  JobProfile,
  JobProfileCreate,
  JobProfileStatus,
} from "../features/cv-intelligence/types";
type ActiveSection =
  | "overview"
  | "jobs"
  | "candidates";
type CandidateScope =
  | "all"
  | "unassigned"
  | `job:${number}`;
const emptyJobForm: JobProfileCreate = {
  title: "",
  department: null,
  location: null,
  employment_type: null,
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
    size / (1024 * 1024)
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
function statusClass(
  value: string,
): string {
  switch (value.toLowerCase()) {
    case "active":
    case "ready":
      return (
        "bg-emerald-100 text-emerald-700"
      );
    case "draft":
    case "uploaded":
      return (
        "bg-amber-100 text-amber-700"
      );
    case "closed":
    case "archived":
      return (
        "bg-slate-200 text-slate-700"
      );
    case "processing":
      return (
        "bg-sky-100 text-sky-700"
      );
    case "needs_ocr":
    case "failed":
      return (
        "bg-red-100 text-red-700"
      );
    default:
      return (
        "bg-slate-100 text-slate-600"
      );
  }
}
function getApiErrorMessage(
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
    if (
      error.code
      === "ECONNABORTED"
    ) {
      return (
        "The request took too long. " +
        "Confirm that the backend server is running and try again."
      );
    }
  }
  return fallbackMessage;
}
function getScopeJobId(
  scope: CandidateScope,
): number | null {
  if (
    !scope.startsWith("job:")
  ) {
    return null;
  }
  const jobId = Number(
    scope.replace(
      "job:",
      "",
    ),
  );
  return Number.isFinite(jobId)
    ? jobId
    : null;
}
export function CVIntelligencePage() {
  const [
    activeSection,
    setActiveSection,
  ] = useState<ActiveSection>(
    "overview",
  );
  const [
    jobProfiles,
    setJobProfiles,
  ] = useState<JobProfile[]>([]);
  const [
    candidates,
    setCandidates,
  ] = useState<CandidateCV[]>([]);
  const [
    scopedCandidates,
    setScopedCandidates,
  ] = useState<CandidateCV[]>([]);
  const [
    candidateScope,
    setCandidateScope,
  ] = useState<CandidateScope>(
    "all",
  );
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
    candidateProfile,
    setCandidateProfile,
  ] = useState<
    CandidateProfile | null
  >(null);
  const [
    isProfileLoading,
    setIsProfileLoading,
  ] = useState(false);
  const [
    isPageLoading,
    setIsPageLoading,
  ] = useState(false);
  const [
    isLoading,
    setIsLoading,
  ] = useState(true);
  const [
    busyAction,
    setBusyAction,
  ] = useState<string | null>(
    null,
  );
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
  const [
    jobForm,
    setJobForm,
  ] = useState<JobProfileCreate>({
    ...emptyJobForm,
  });
  const [
    editingJobId,
    setEditingJobId,
  ] = useState<number | null>(
    null,
  );
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
    assignmentJobId,
    setAssignmentJobId,
  ] = useState("");
  const displayedCandidates =
    useMemo(
      () =>
        candidateScope === "all"
          ? candidates
          : scopedCandidates,
      [
        candidateScope,
        candidates,
        scopedCandidates,
      ],
    );
  const selectedCandidate =
    useMemo(
      () =>
        candidates.find(
          (candidate) =>
            candidate.id
            === selectedCandidateId,
        )
        ?? null,
      [
        candidates,
        selectedCandidateId,
      ],
    );
  const currentScopeJobId =
    getScopeJobId(
      candidateScope,
    );
  const currentScopeJob =
    useMemo(
      () =>
        currentScopeJobId === null
          ? null
          : (
              jobProfiles.find(
                (job) =>
                  job.id
                  === currentScopeJobId,
              )
              ?? null
            ),
      [
        currentScopeJobId,
        jobProfiles,
      ],
    );
  const activeJobCount =
    jobProfiles.filter(
      (job) =>
        job.status === "active",
    ).length;
  const readyCandidateCount =
    candidates.filter(
      (candidate) =>
        candidate.status === "ready",
    ).length;
  const needsOcrCount =
    candidates.filter(
      (candidate) =>
        candidate.status
        === "needs_ocr",
    ).length;
  useEffect(() => {
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
          setSelectedCandidateId(
            candidateResult[0]?.id
            ?? null,
          );
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
      candidateScope === "all"
    ) {
      return;
    }
    let isActive = true;
    const jobId = getScopeJobId(
      candidateScope,
    );
    const request =
      candidateScope
      === "unassigned"
        ? listUnassignedCandidateCVs()
        : (
            jobId === null
              ? Promise.resolve([])
              : listJobCandidateCVs(
                  jobId,
                )
          );
    request
      .then((result) => {
        if (!isActive) {
          return;
        }
        setScopedCandidates(
          result,
        );
        setSelectedCandidateId(
          result[0]?.id
          ?? null,
        );
      })
      .catch(
        (error: unknown) => {
          if (!isActive) {
            return;
          }
          setErrorMessage(
            getApiErrorMessage(
              error,
              "Could not load candidates for the selected filter.",
            ),
          );
        },
      );
    return () => {
      isActive = false;
    };
  }, [candidateScope]);
  useEffect(() => {
    if (
      selectedCandidateId === null
    ) {
      return;
    }
    let isActive = true;
    Promise.all([
      listCandidateCVPages(
        selectedCandidateId,
      ),
      getCandidateProfile(
        selectedCandidateId,
      ).catch(
        (error: unknown) => {
          if (
            axios.isAxiosError(error)
            && error.response?.status
            === 404
          ) {
            return null;
          }
          throw error;
        },
      ),
    ])
      .then(
        ([
          pageResult,
          profileResult,
        ]) => {
          if (!isActive) {
            return;
          }
          setCandidatePages(
            pageResult,
          );
          setCandidateProfile(
            profileResult,
          );
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
              "Could not load candidate details.",
            ),
          );
        },
      )
      .finally(() => {
        if (!isActive) {
          return;
        }
        setIsPageLoading(false);
        setIsProfileLoading(false);
      });
    return () => {
      isActive = false;
    };
  }, [selectedCandidateId]);
  function clearMessages(): void {
    setErrorMessage(null);
    setActivityMessage(null);
  }
  function selectCandidate(
    candidateId: number,
  ): void {
    setCandidatePages([]);
    setCandidateProfile(null);
    setIsPageLoading(true);
    setIsProfileLoading(true);
    setSelectedCandidateId(
      candidateId,
    );
  }
  async function reloadAllCandidates():
    Promise<CandidateCV[]> {
    const result =
      await listCandidateCVs();
    setCandidates(result);
    return result;
  }
  async function reloadCurrentScope():
    Promise<void> {
    if (
      candidateScope === "all"
    ) {
      return;
    }
    const jobId = getScopeJobId(
      candidateScope,
    );
    const result =
      candidateScope
      === "unassigned"
        ? await listUnassignedCandidateCVs()
        : (
            jobId === null
              ? []
              : await listJobCandidateCVs(
                  jobId,
                )
          );
    setScopedCandidates(result);
  }
  function handleScopeChange(
    value: string,
  ): void {
    const nextScope =
      value as CandidateScope;
    clearMessages();
    setCandidateScope(
      nextScope,
    );
    setCandidatePages([]);
    setCandidateProfile(null);
    setSelectedCandidateId(
      nextScope === "all"
        ? candidates[0]?.id
          ?? null
        : null,
    );
  }
  function updateJobField(
    field: keyof JobProfileCreate,
    value: string,
  ): void {
    setJobForm(
      (current) => ({
        ...current,
        [field]:
          field === "status"
            ? (
                value as JobProfileStatus
              )
            : value,
      }),
    );
  }
  function beginJobEdit(
    job: JobProfile,
  ): void {
    clearMessages();
    setEditingJobId(
      job.id,
    );
    setJobForm({
      title: job.title,
      department:
        job.department,
      location:
        job.location,
      employment_type:
        job.employment_type,
      description:
        job.description,
      status:
        job.status,
    });
    window.scrollTo({
      top: 300,
      behavior: "smooth",
    });
  }
  function cancelJobEdit(): void {
    setEditingJobId(null);
    setJobForm({
      ...emptyJobForm,
    });
  }
  async function handleSaveJob(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    clearMessages();
    const payload: JobProfileCreate = {
      title:
        jobForm.title.trim(),
      department:
        jobForm.department
          ?.trim()
        || null,
      location:
        jobForm.location
          ?.trim()
        || null,
      employment_type:
        jobForm.employment_type
          ?.trim()
        || null,
      description:
        jobForm.description.trim(),
      status:
        jobForm.status,
    };
    const actionKey =
      editingJobId === null
        ? "create-job"
        : `edit-job-${editingJobId}`;
    setBusyAction(actionKey);
    try {
      if (
        editingJobId === null
      ) {
        const createdJob =
          await createJobProfile(
            payload,
          );
        setJobProfiles(
          (current) => [
            createdJob,
            ...current,
          ],
        );
        setActivityMessage(
          "Job profile created successfully.",
        );
      } else {
        const updatedJob =
          await updateJobProfile(
            editingJobId,
            payload,
          );
        setJobProfiles(
          (current) =>
            current.map(
              (job) =>
                job.id
                === updatedJob.id
                  ? updatedJob
                  : job,
            ),
        );
        setActivityMessage(
          "Job profile updated successfully.",
        );
      }
      setEditingJobId(null);
      setJobForm({
        ...emptyJobForm,
      });
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not save the job profile.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleArchiveJob(
    job: JobProfile,
  ): Promise<void> {
    clearMessages();
    setBusyAction(
      `archive-job-${job.id}`,
    );
    try {
      const updatedJob =
        await updateJobProfile(
          job.id,
          {
            status:
              job.status
              === "archived"
                ? "draft"
                : "archived",
          },
        );
      setJobProfiles(
        (current) =>
          current.map(
            (item) =>
              item.id === job.id
                ? updatedJob
                : item,
          ),
      );
      setActivityMessage(
        updatedJob.status
        === "archived"
          ? "Job profile archived successfully."
          : "Job profile restored as a draft.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not update the job status.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleDeleteJob(
    job: JobProfile,
  ): Promise<void> {
    const confirmed =
      window.confirm(
        `Delete "${job.title}"?\n\n` +
        "Its candidate assignments will be removed, " +
        "but the candidate CV files will be preserved.",
      );
    if (!confirmed) {
      return;
    }
    clearMessages();
    setBusyAction(
      `delete-job-${job.id}`,
    );
    try {
      await deleteJobProfile(
        job.id,
      );
      setJobProfiles(
        (current) =>
          current.filter(
            (item) =>
              item.id !== job.id,
          ),
      );
      if (
        currentScopeJobId
        === job.id
      ) {
        setCandidateScope(
          "all",
        );
        setScopedCandidates([]);
      }
      setActivityMessage(
        "Job profile deleted. Candidate CV files were preserved.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not delete the job profile.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  function openJobCandidates(
    job: JobProfile,
  ): void {
    clearMessages();
    setCandidateScope(
      `job:${job.id}`,
    );
    setActiveSection(
      "candidates",
    );
    setSelectedCandidateId(null);
    setCandidatePages([]);
    setCandidateProfile(null);
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
      const scopeJobId =
        getScopeJobId(
          candidateScope,
        );
      if (
        scopeJobId !== null
      ) {
        await assignCandidateToJob(
          scopeJobId,
          uploadedCandidate.id,
        );
      }
      await reloadAllCandidates();
      await reloadCurrentScope();
      selectCandidate(
        uploadedCandidate.id,
      );
      setSelectedFile(null);
      setFileInputKey(
        (current) =>
          current + 1,
      );
      setActivityMessage(
        scopeJobId === null
          ? (
              "Candidate CV uploaded successfully. " +
              "It is currently unassigned."
            )
          : (
              "Candidate CV uploaded and assigned " +
              "to the selected job successfully."
            ),
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
  async function handleAssignCandidate():
    Promise<void> {
    if (
      selectedCandidateId === null
    ) {
      setErrorMessage(
        "Select a candidate first.",
      );
      return;
    }
    const jobId = Number(
      assignmentJobId,
    );
    if (
      !Number.isFinite(jobId)
      || jobId <= 0
    ) {
      setErrorMessage(
        "Select a job profile first.",
      );
      return;
    }
    clearMessages();
    setBusyAction(
      `assign-${selectedCandidateId}`,
    );
    try {
      await assignCandidateToJob(
        jobId,
        selectedCandidateId,
      );
      await reloadCurrentScope();
      setActivityMessage(
        "Candidate assigned to the selected job successfully.",
      );
      setAssignmentJobId("");
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not assign the candidate to the job.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleRemoveFromCurrentJob():
    Promise<void> {
    if (
      selectedCandidateId === null
      || currentScopeJobId === null
    ) {
      return;
    }
    const confirmed =
      window.confirm(
        "Remove this candidate from the selected job?\n\n" +
        "The candidate CV and structured profile will be preserved.",
      );
    if (!confirmed) {
      return;
    }
    clearMessages();
    setBusyAction(
      `remove-${selectedCandidateId}`,
    );
    try {
      await removeCandidateFromJob(
        currentScopeJobId,
        selectedCandidateId,
      );
      await reloadCurrentScope();
      setSelectedCandidateId(null);
      setCandidatePages([]);
      setCandidateProfile(null);
      setActivityMessage(
        "Candidate removed from this job. The CV was preserved.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not remove the candidate from this job.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleDeleteCandidate():
    Promise<void> {
    if (
      selectedCandidate === null
    ) {
      return;
    }
    const confirmed =
      window.confirm(
        `Permanently delete "${selectedCandidate.original_name}"?\n\n` +
        "This will remove the original PDF, extracted pages, " +
        "structured profile and all job assignments.\n\n" +
        "This action cannot be undone.",
      );
    if (!confirmed) {
      return;
    }
    clearMessages();
    setBusyAction(
      `delete-candidate-${selectedCandidate.id}`,
    );
    try {
      await deleteCandidatePermanently(
        selectedCandidate.id,
      );
      await reloadAllCandidates();
      await reloadCurrentScope();
      setSelectedCandidateId(null);
      setCandidatePages([]);
      setCandidateProfile(null);
      setActivityMessage(
        "Candidate CV and all related records were permanently deleted.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not permanently delete the candidate.",
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
      const pages =
        await listCandidateCVPages(
          candidate.id,
        );
      setCandidatePages(
        pages,
      );
      setCandidateProfile(null);
      if (
        result.status
        === "needs_ocr"
      ) {
        setActivityMessage(
          "CV processing completed, but no selectable text was found.",
        );
      } else {
        setActivityMessage(
          "CV text extracted successfully.",
        );
      }
    } catch (error) {
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
  async function handleExtractCandidateProfile(
    candidate: CandidateCV,
  ): Promise<void> {
    clearMessages();
    setBusyAction(
      `profile-${candidate.id}`,
    );
    setIsProfileLoading(true);
    try {
      const profile =
        await extractCandidateProfile(
          candidate.id,
        );
      setCandidateProfile(
        profile,
      );
      setActivityMessage(
        "Structured candidate profile extracted successfully. " +
        "Verify the result against the original CV.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not extract the structured candidate profile.",
        ),
      );
    } finally {
      setBusyAction(null);
      setIsProfileLoading(false);
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
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-400">
          Human-reviewed recruitment intelligence
        </p>
        <h1 className="mt-4 text-3xl font-bold md:text-5xl">
          CV Intelligence
        </h1>
        <p className="mt-5 max-w-3xl leading-7 text-slate-300">
          Manage job profiles, organize candidate
          CVs and prepare structured evidence for
          ATS and job-matching workflows.
        </p>
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
      {activeSection === "overview" ? (
        <section className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {[
            {
              label: "Job profiles",
              value:
                jobProfiles.length,
            },
            {
              label: "Active jobs",
              value:
                activeJobCount,
            },
            {
              label: "CVs ready",
              value:
                readyCandidateCount,
            },
            {
              label: "Needs OCR",
              value:
                needsOcrCount,
            },
          ].map((item) => (
            <article
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
              key={item.label}
            >
              <p className="text-sm font-semibold text-slate-500">
                {item.label}
              </p>
              <p className="mt-3 text-4xl font-bold text-slate-950">
                {item.value}
              </p>
            </article>
          ))}
        </section>
      ) : null}
      {activeSection === "jobs" ? (
        <section className="mt-8 grid gap-7 lg:grid-cols-[0.9fr_1.1fr]">
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              {editingJobId === null
                ? "Create job profile"
                : "Edit job profile"}
            </h2>
            <p className="mt-2 leading-6 text-slate-600">
              Candidate CVs can be assigned to one
              or more job profiles.
            </p>
            <form
              className="mt-7 space-y-5"
              onSubmit={
                handleSaveJob
              }
            >
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Job title
                </span>
                <input
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                  onChange={(event) => {
                    updateJobField(
                      "title",
                      event.target.value,
                    );
                  }}
                  required
                  value={jobForm.title}
                />
              </label>
              <div className="grid gap-4 sm:grid-cols-2">
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Department
                  </span>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                    onChange={(event) => {
                      updateJobField(
                        "department",
                        event.target.value,
                      );
                    }}
                    value={
                      jobForm.department
                      ?? ""
                    }
                  />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Location
                  </span>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                    onChange={(event) => {
                      updateJobField(
                        "location",
                        event.target.value,
                      );
                    }}
                    value={
                      jobForm.location
                      ?? ""
                    }
                  />
                </label>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Employment type
                  </span>
                  <select
                    className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
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
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Status
                  </span>
                  <select
                    className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
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
                    {editingJobId !== null ? (
                      <option value="archived">
                        Archived
                      </option>
                    ) : null}
                  </select>
                </label>
              </div>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Job description
                </span>
                <textarea
                  className="mt-2 min-h-56 w-full resize-y rounded-xl border border-slate-300 px-4 py-3"
                  onChange={(event) => {
                    updateJobField(
                      "description",
                      event.target.value,
                    );
                  }}
                  required
                  value={
                    jobForm.description
                  }
                />
              </label>
              <div className="flex gap-3">
                <button
                  className="flex-1 rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white disabled:opacity-60"
                  disabled={
                    busyAction !== null
                  }
                  type="submit"
                >
                  {busyAction
                  === "create-job"
                    ? "Creating..."
                    : editingJobId !== null
                      ? "Save changes"
                      : "Create job profile"}
                </button>
                {editingJobId !== null ? (
                  <button
                    className="rounded-xl border border-slate-300 px-5 py-3 font-semibold text-slate-700"
                    onClick={
                      cancelJobEdit
                    }
                    type="button"
                  >
                    Cancel
                  </button>
                ) : null}
              </div>
            </form>
          </article>
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              Job profiles
            </h2>
            <p className="mt-1 text-slate-600">
              {jobProfiles.length} profile(s)
              available.
            </p>
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
                    <div className="mt-5 flex flex-wrap gap-2">
                      <button
                        className="rounded-lg bg-sky-600 px-3 py-2 text-sm font-semibold text-white"
                        onClick={() => {
                          openJobCandidates(
                            job,
                          );
                        }}
                        type="button"
                      >
                        View candidates
                      </button>
                      <button
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700"
                        onClick={() => {
                          beginJobEdit(job);
                        }}
                        type="button"
                      >
                        Edit
                      </button>
                      <button
                        className="rounded-lg border border-amber-300 px-3 py-2 text-sm font-semibold text-amber-700"
                        onClick={() => {
                          void handleArchiveJob(
                            job,
                          );
                        }}
                        type="button"
                      >
                        {job.status
                        === "archived"
                          ? "Restore"
                          : "Archive"}
                      </button>
                      <button
                        className="rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold text-red-700"
                        onClick={() => {
                          void handleDeleteJob(
                            job,
                          );
                        }}
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  </article>
                ),
              )}
            </div>
          </article>
        </section>
      ) : null}
      {activeSection === "candidates" ? (
        <section className="mt-8">
          <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid gap-5 lg:grid-cols-2">
              <label>
                <span className="text-sm font-semibold text-slate-700">
                  Candidate list
                </span>
                <select
                  className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
                  onChange={(event) => {
                    handleScopeChange(
                      event.target.value,
                    );
                  }}
                  value={
                    candidateScope
                  }
                >
                  <option value="all">
                    All candidates
                  </option>
                  <option value="unassigned">
                    Unassigned candidates
                  </option>
                  {jobProfiles.map(
                    (job) => (
                      <option
                        key={job.id}
                        value={`job:${job.id}`}
                      >
                        {job.title}
                      </option>
                    ),
                  )}
                </select>
              </label>
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-800">
                  Current view
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  {candidateScope
                  === "all"
                    ? "Showing every uploaded candidate."
                    : candidateScope
                      === "unassigned"
                      ? "Showing CVs not assigned to any job."
                      : `Showing candidates for ${currentScopeJob?.title ?? "the selected job"}.`}
                </p>
              </div>
            </div>
          </article>
          <article className="mt-6 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <div className="grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end">
              <div>
                <h2 className="text-2xl font-bold text-slate-950">
                  Upload candidate CV
                </h2>
                <p className="mt-2 leading-6 text-slate-600">
                  {currentScopeJob
                    ? `The uploaded CV will automatically be assigned to ${currentScopeJob.title}.`
                    : "The uploaded CV will remain unassigned until it is linked to a job."}
                </p>
              </div>
              <form
                className="flex flex-col gap-3 sm:flex-row"
                onSubmit={
                  handleUploadCandidate
                }
              >
                <input
                  accept=".pdf,application/pdf"
                  className="rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm"
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
                  className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white"
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
              <h2 className="text-xl font-bold text-slate-950">
                Candidate CVs
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                {displayedCandidates.length}
                {" "}candidate(s) in this view
              </p>
              {displayedCandidates.length
              === 0 ? (
                <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                  No candidate CV is available in this view.
                </div>
              ) : (
                <div className="mt-6 space-y-3">
                  {displayedCandidates.map(
                    (candidate) => (
                      <button
                        className={[
                          "w-full rounded-2xl border p-4 text-left transition",
                          candidate.id
                          === selectedCandidateId
                            ? "border-sky-400 bg-sky-50"
                            : "border-slate-200 hover:bg-slate-50",
                        ].join(" ")}
                        key={candidate.id}
                        onClick={() => {
                          selectCandidate(
                            candidate.id,
                          );
                        }}
                        type="button"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate font-semibold text-slate-900">
                              {candidate.original_name}
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
                    ),
                  )}
                </div>
              )}
            </article>
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              {!selectedCandidate ? (
                <div className="flex min-h-72 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                  Select a candidate CV to view its details.
                </div>
              ) : (
                <>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-wide text-sky-600">
                        Candidate CV
                      </p>
                      <h2 className="mt-2 break-words text-2xl font-bold text-slate-950">
                        {selectedCandidate.original_name}
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
                  <div className="mt-6 flex flex-wrap gap-3">
                    <button
                      className="rounded-xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white"
                      onClick={() => {
                        void handleOpenOriginalCV(
                          selectedCandidate,
                        );
                      }}
                      type="button"
                    >
                      Open original CV
                    </button>
                    <button
                      className="rounded-xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
                      onClick={() => {
                        void handleProcessCandidate(
                          selectedCandidate,
                        );
                      }}
                      type="button"
                    >
                      {selectedCandidate.status
                      === "ready"
                        ? "Process again"
                        : "Process CV"}
                    </button>
                    <button
                      className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
                      disabled={
                        selectedCandidate.status
                        !== "ready"
                      }
                      onClick={() => {
                        void handleExtractCandidateProfile(
                          selectedCandidate,
                        );
                      }}
                      type="button"
                    >
                      {candidateProfile
                        ? "Re-extract structured profile"
                        : "Extract structured profile"}
                    </button>
                  </div>
                  <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="font-semibold text-slate-900">
                      Job assignment
                    </p>
                    <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                      <select
                        className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3"
                        onChange={(event) => {
                          setAssignmentJobId(
                            event.target.value,
                          );
                        }}
                        value={
                          assignmentJobId
                        }
                      >
                        <option value="">
                          Select job profile
                        </option>
                        {jobProfiles.map(
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
                      <button
                        className="rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white"
                        onClick={() => {
                          void handleAssignCandidate();
                        }}
                        type="button"
                      >
                        Assign to job
                      </button>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {currentScopeJobId
                      !== null ? (
                        <button
                          className="rounded-lg border border-amber-300 px-3 py-2 text-sm font-semibold text-amber-700"
                          onClick={() => {
                            void handleRemoveFromCurrentJob();
                          }}
                          type="button"
                        >
                          Remove from this job
                        </button>
                      ) : null}
                      <button
                        className="rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold text-red-700"
                        onClick={() => {
                          void handleDeleteCandidate();
                        }}
                        type="button"
                      >
                        Delete candidate permanently
                      </button>
                    </div>
                  </div>
                  <CandidateProfilePanel
                    isLoading={
                      isProfileLoading
                    }
                    profile={
                      candidateProfile
                    }
                  />
                  <details className="mt-7 border-t border-slate-200 pt-6">
                    <summary className="cursor-pointer rounded-xl bg-slate-100 px-4 py-3 font-semibold text-slate-800">
                      Show extraction audit (raw text)
                    </summary>
                    {isPageLoading ? (
                      <p className="mt-5 text-sm text-slate-500">
                        Loading extracted pages...
                      </p>
                    ) : null}
                    {!isPageLoading
                    && candidatePages.length
                    === 0 ? (
                      <p className="mt-5 text-sm text-slate-500">
                        No extracted page text is available.
                      </p>
                    ) : null}
                    <div className="mt-5 space-y-4">
                      {candidatePages.map(
                        (page) => (
                          <article
                            className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
                            key={page.page_number}
                          >
                            <div className="flex justify-between gap-4">
                              <h4 className="font-bold text-slate-800">
                                Page {page.page_number}
                              </h4>
                              <span className="text-xs text-slate-500">
                                {page.char_count} characters
                              </span>
                            </div>
                            <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap break-words font-sans text-sm leading-6 text-slate-600">
                              {page.text
                              || "No selectable text found."}
                            </pre>
                          </article>
                        ),
                      )}
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

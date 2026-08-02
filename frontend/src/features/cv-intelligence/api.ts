
import { apiClient } from "../../api/client";
import type {
  CandidateATSResult,
  CandidateCV,
  CandidateCVPagePreview,
  CandidateCVProcessResult,
  CandidateProfile,
  JobCandidateAssignment,
  JobProfile,
  JobProfileCreate,
  JobProfileUpdate,
} from "./types";
export async function listJobProfiles(): Promise<
  JobProfile[]
> {
  const response =
    await apiClient.get<JobProfile[]>(
      "/api/jobs",
    );
  return response.data;
}
export async function createJobProfile(
  payload: JobProfileCreate,
): Promise<JobProfile> {
  const response =
    await apiClient.post<JobProfile>(
      "/api/jobs",
      payload,
    );
  return response.data;
}
export async function updateJobProfile(
  jobId: number,
  payload: JobProfileUpdate,
): Promise<JobProfile> {
  const response =
    await apiClient.patch<JobProfile>(
      `/api/jobs/${jobId}`,
      payload,
    );
  return response.data;
}
export async function deleteJobProfile(
  jobId: number,
): Promise<void> {
  await apiClient.delete(
    `/api/jobs/${jobId}`,
  );
}
export async function listCandidateCVs(): Promise<
  CandidateCV[]
> {
  const response =
    await apiClient.get<CandidateCV[]>(
      "/api/candidates",
    );
  return response.data;
}
export async function listUnassignedCandidateCVs(): Promise<
  CandidateCV[]
> {
  const response =
    await apiClient.get<CandidateCV[]>(
      "/api/candidates/unassigned",
    );
  return response.data;
}
export async function listJobCandidateCVs(
  jobId: number,
): Promise<CandidateCV[]> {
  const response =
    await apiClient.get<CandidateCV[]>(
      `/api/jobs/${jobId}/candidates`,
    );
  return response.data;
}
export async function assignCandidateToJob(
  jobId: number,
  candidateId: number,
): Promise<JobCandidateAssignment> {
  const response =
    await apiClient.post<JobCandidateAssignment>(
      `/api/jobs/${jobId}/candidates/${candidateId}`,
    );
  return response.data;
}
export async function removeCandidateFromJob(
  jobId: number,
  candidateId: number,
): Promise<void> {
  await apiClient.delete(
    `/api/jobs/${jobId}/candidates/${candidateId}`,
  );
}
export async function deleteCandidatePermanently(
  candidateId: number,
): Promise<void> {
  await apiClient.delete(
    `/api/candidates/${candidateId}`,
  );
}
export async function uploadCandidateCV(
  file: File,
): Promise<CandidateCV> {
  const formData = new FormData();
  formData.append(
    "file",
    file,
  );
  const response =
    await apiClient.post<CandidateCV>(
      "/api/candidates/upload",
      formData,
    );
  return response.data;
}
export async function fetchCandidateCVFile(
  candidateId: number,
): Promise<Blob> {
  const response =
    await apiClient.get<Blob>(
      `/api/candidates/${candidateId}/file`,
      {
        responseType: "blob",
        timeout: 120_000,
      },
    );
  return response.data;
}
export async function processCandidateCV(
  candidateId: number,
): Promise<CandidateCVProcessResult> {
  const response =
    await apiClient.post<CandidateCVProcessResult>(
      `/api/candidates/${candidateId}/process`,
    );
  return response.data;
}
export async function listCandidateCVPages(
  candidateId: number,
): Promise<CandidateCVPagePreview[]> {
  const response =
    await apiClient.get<CandidateCVPagePreview[]>(
      `/api/candidates/${candidateId}/pages`,
    );
  return response.data;
}
export async function extractCandidateProfile(
  candidateId: number,
): Promise<CandidateProfile> {
  const response =
    await apiClient.post<CandidateProfile>(
      `/api/candidates/${candidateId}/profile/extract`,
      undefined,
      {
        timeout: 600_000,
      },
    );
  return response.data;
}
export async function getCandidateProfile(
  candidateId: number,
): Promise<CandidateProfile> {
  const response =
    await apiClient.get<CandidateProfile>(
      `/api/candidates/${candidateId}/profile`,
    );
  return response.data;
}

export async function analyzeCandidateATS(
  candidateId: number,
): Promise<CandidateATSResult> {
  const response =
    await apiClient.post<CandidateATSResult>(
      `/api/candidates/${candidateId}/ats/analyze`,
    );
  return response.data;
}
export async function getCandidateATSResult(
  candidateId: number,
): Promise<CandidateATSResult> {
  const response =
    await apiClient.get<CandidateATSResult>(
      `/api/candidates/${candidateId}/ats`,
    );
  return response.data;
}

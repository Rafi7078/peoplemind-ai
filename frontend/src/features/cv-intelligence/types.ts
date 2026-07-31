
export type JobProfileStatus =
  | "draft"
  | "active"
  | "closed";
export type JobProfile = {
  id: number;
  title: string;
  department: string | null;
  location: string | null;
  employment_type: string | null;
  description: string;
  status: JobProfileStatus;
  created_by_id: number;
  created_at: string;
  updated_at: string;
};
export type JobProfileCreate = {
  title: string;
  department: string | null;
  location: string | null;
  employment_type: string | null;
  description: string;
  status: JobProfileStatus;
};
export type CandidateCV = {
  id: number;
  original_name: string;
  size_bytes: number;
  mime_type: string;
  status: string;
  page_count: number | null;
  uploaded_by_id: number;
  created_at: string;
};
export type CandidateCVProcessResult = {
  candidate_id: number;
  status: string;
  page_count: number;
  text_pages: number;
  total_characters: number;
};
export type CandidateCVPagePreview = {
  page_number: number;
  char_count: number;
  text: string;
};

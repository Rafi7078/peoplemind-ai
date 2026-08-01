
export type JobProfileStatus =
  | "draft"
  | "active"
  | "closed"
  | "archived";
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
export type JobProfileUpdate = Partial<
  JobProfileCreate
>;
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
export type JobCandidateAssignment = {
  id: number;
  job_profile_id: number;
  candidate_cv_id: number;
  assigned_by_id: number;
  created_at: string;
};
export type CandidateContactInformation = {
  email: string | null;
  phone: string | null;
  linkedin: string | null;
  github: string | null;
  portfolio: string | null;
};
export type CandidateLatestEducation = {
  degree_or_qualification: string | null;
  institution: string | null;
  completion_year: string | null;
  cgpa_or_gpa: string | null;
};
export type CandidateWorkExperience = {
  company: string | null;
  job_title: string | null;
  start_date: string | null;
  end_date: string | null;
  duration: string | null;
};
export type CandidateSkills = {
  technical_skills: string[];
  tools_and_platforms: string[];
  operational_skills: string[];
};
export type CandidateProject = {
  project_title: string | null;
  technologies: string[];
};
export type CandidateCertification = {
  certification_title: string | null;
  issuing_organization: string | null;
  completion_date: string | null;
};
export type CandidateProfile = {
  id: number;
  candidate_cv_id: number;
  candidate_name: string | null;
  contact_information:
    CandidateContactInformation;
  latest_completed_education:
    CandidateLatestEducation | null;
  work_experience:
    CandidateWorkExperience[];
  skills: CandidateSkills;
  projects: CandidateProject[];
  certifications:
    CandidateCertification[];
  extraction_model: string;
  created_at: string;
  updated_at: string;
};

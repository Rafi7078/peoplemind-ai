
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

export type CandidateATSCheckStatus =
  | "pass"
  | "warning"
  | "fail";
export type CandidateATSCheck = {
  check_id: string;
  category: string;
  title: string;
  status: CandidateATSCheckStatus;
  points_awarded: number;
  max_points: number;
  message: string;
  evidence: string[];
};
export type CandidateATSResult = {
  id: number;
  candidate_cv_id: number;
  score: number;
  rating: string;
  risk_level: string;
  category_scores: Record<
    string,
    number
  >;
  checks: CandidateATSCheck[];
  suggestions: string[];
  engine_version: string;
  created_at: string;
  updated_at: string;
};

export type JobMatchCheckStatus =
  | "match"
  | "partial"
  | "missing"
  | "not_specified";
export type JobMatchCheck = {
  check_id: string;
  category: string;
  title: string;
  status: JobMatchCheckStatus;
  points_awarded: number;
  max_points: number;
  message: string;
  evidence: string[];
};
export type JobMatchResult = {
  id: number;
  job_profile_id: number;
  candidate_cv_id: number;
  score: number;
  rating: string;
  recommendation: string;
  category_scores: Record<
    string,
    number
  >;
  requirements: {
    recognized_job_skills?: string[];
    minimum_experience_years?:
      number | null;
    education_requirement?:
      string | null;
    job_role_groups?: string[];
    [key: string]: unknown;
  };
  checks: JobMatchCheck[];
  matched_requirements: string[];
  missing_requirements: string[];
  notes: string[];
  engine_version: string;
  created_at: string;
  updated_at: string;
};

export type JobReviewStatus =
  | "not_reviewed"
  | "in_review"
  | "shortlisted"
  | "on_hold"
  | "not_selected";
export type JobCandidateReview = {
  id: number;
  job_profile_id: number;
  candidate_cv_id: number;
  status: JobReviewStatus;
  notes: string | null;
  reviewed_by_id: number;
  reviewed_at: string;
  created_at: string;
  updated_at: string;
};
export type JobCandidateReviewUpdate = {
  status: JobReviewStatus;
  notes: string | null;
};
export type JobMatchRankingSummary = {
  score: number;
  rating: string;
  recommendation: string;
  engine_version: string;
  updated_at: string;
};
export type JobCandidateRankingItem = {
  rank: number | null;
  analysis_status:
    | "analyzed"
    | "not_analyzed";
  candidate: CandidateCV;
  candidate_name: string | null;
  match: JobMatchRankingSummary | null;
  ats_score: number | null;
  ats_rating: string | null;
  review_status: JobReviewStatus;
  review: JobCandidateReview | null;
};

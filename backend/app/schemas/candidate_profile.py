
from datetime import datetime
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
class CandidateContactInformation(
    BaseModel
):
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
class CandidateLatestEducation(
    BaseModel
):
    degree_or_qualification: (
        str | None
    ) = None
    institution: str | None = None
    completion_year: (
        str | None
    ) = None
    cgpa_or_gpa: str | None = None
class CandidateWorkExperience(
    BaseModel
):
    company: str | None = None
    job_title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration: str | None = None
class CandidateSkills(BaseModel):
    technical_skills: list[str] = Field(
        default_factory=list,
    )
    tools_and_platforms: list[str] = Field(
        default_factory=list,
    )
    operational_skills: list[str] = Field(
        default_factory=list,
    )
class CandidateProject(BaseModel):
    project_title: str | None = None
    technologies: list[str] = Field(
        default_factory=list,
    )
class CandidateCertification(
    BaseModel
):
    certification_title: (
        str | None
    ) = None
    issuing_organization: (
        str | None
    ) = None
    completion_date: (
        str | None
    ) = None
class CandidateProfileData(BaseModel):
    candidate_name: str | None = None
    contact_information: (
        CandidateContactInformation
    ) = Field(
        default_factory=(
            CandidateContactInformation
        )
    )
    latest_completed_education: (
        CandidateLatestEducation
        | None
    ) = None
    work_experience: list[
        CandidateWorkExperience
    ] = Field(
        default_factory=list,
    )
    skills: CandidateSkills = Field(
        default_factory=CandidateSkills,
    )
    projects: list[
        CandidateProject
    ] = Field(
        default_factory=list,
    )
    certifications: list[
        CandidateCertification
    ] = Field(
        default_factory=list,
    )
class CandidateProfileRead(
    CandidateProfileData
):
    id: int
    candidate_cv_id: int
    extraction_model: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )

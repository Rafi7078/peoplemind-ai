
import type {
  CandidateProfile,
} from "./types";
type CandidateProfilePanelProps = {
  profile: CandidateProfile | null;
  isLoading: boolean;
};
function displayValue(
  value: string | null | undefined,
): string {
  const cleanedValue = value?.trim();
  return cleanedValue
    ? cleanedValue
    : "Not found";
}
function formatProfileDate(
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
function SkillGroup({
  title,
  skills,
}: {
  title: string;
  skills: string[];
}) {
  return (
    <div>
      <h4 className="text-sm font-bold text-slate-700">
        {title}
      </h4>
      {skills.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">
          Not found
        </p>
      ) : (
        <div className="mt-3 flex flex-wrap gap-2">
          {skills.map(
            (
              skill,
              index,
            ) => (
              <span
                className="rounded-full bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700"
                key={`${skill}-${index}`}
              >
                {skill}
              </span>
            ),
          )}
        </div>
      )}
    </div>
  );
}
export function CandidateProfilePanel({
  profile,
  isLoading,
}: CandidateProfilePanelProps) {
  if (isLoading) {
    return (
      <section className="mt-7 border-t border-slate-200 pt-7">
        <div className="rounded-2xl border border-sky-200 bg-sky-50 p-6 text-sm font-medium text-sky-700">
          Loading structured candidate profile...
        </div>
      </section>
    );
  }
  if (!profile) {
    return (
      <section className="mt-7 border-t border-slate-200 pt-7">
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-7 text-center">
          <h3 className="font-bold text-slate-800">
            No structured profile extracted
          </h3>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            Process the CV first, then select
            Extract structured profile.
          </p>
        </div>
      </section>
    );
  }
  const contactEntries = [
    {
      label: "Email",
      value:
        profile.contact_information.email,
    },
    {
      label: "Phone",
      value:
        profile.contact_information.phone,
    },
    {
      label: "LinkedIn",
      value:
        profile.contact_information.linkedin,
    },
    {
      label: "GitHub",
      value:
        profile.contact_information.github,
    },
    {
      label: "Portfolio",
      value:
        profile.contact_information.portfolio,
    },
  ];
  const visibleContacts =
    contactEntries.filter(
      (entry) =>
        Boolean(entry.value?.trim()),
    );
  const education =
    profile.latest_completed_education;
  return (
    <section className="mt-7 border-t border-slate-200 pt-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-emerald-600">
            AI-extracted information
          </p>
          <h3 className="mt-2 text-2xl font-bold text-slate-950">
            Structured Candidate Profile
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            Verify this information against the
            original CV before using it in any
            recruitment decision.
          </p>
        </div>
        <span className="rounded-full bg-emerald-100 px-3 py-1.5 text-xs font-bold text-emerald-700">
          Profile available
        </span>
      </div>
      <div className="mt-6 rounded-2xl bg-slate-950 p-6 text-white">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-sky-300">
          Candidate name
        </p>
        <h4 className="mt-3 break-words text-2xl font-bold">
          {displayValue(
            profile.candidate_name,
          )}
        </h4>
      </div>
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <article className="rounded-2xl border border-slate-200 p-5">
          <h4 className="text-lg font-bold text-slate-900">
            Contact Information
          </h4>
          {visibleContacts.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">
              No supported contact information
              was found.
            </p>
          ) : (
            <dl className="mt-4 space-y-3">
              {visibleContacts.map(
                (entry) => (
                  <div
                    className="rounded-xl bg-slate-50 px-4 py-3"
                    key={entry.label}
                  >
                    <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                      {entry.label}
                    </dt>
                    <dd className="mt-1 break-all text-sm font-medium text-slate-800">
                      {entry.value}
                    </dd>
                  </div>
                ),
              )}
            </dl>
          )}
        </article>
        <article className="rounded-2xl border border-slate-200 p-5">
          <h4 className="text-lg font-bold text-slate-900">
            Latest Completed Education
          </h4>
          {!education ? (
            <p className="mt-4 text-sm leading-6 text-slate-500">
              A completed academic qualification
              could not be confirmed.
            </p>
          ) : (
            <dl className="mt-4 space-y-3">
              <div>
                <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Degree / Qualification
                </dt>
                <dd className="mt-1 font-semibold text-slate-900">
                  {displayValue(
                    education
                      .degree_or_qualification,
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Institution
                </dt>
                <dd className="mt-1 text-sm text-slate-700">
                  {displayValue(
                    education.institution,
                  )}
                </dd>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Completion year
                  </dt>
                  <dd className="mt-1 text-sm text-slate-700">
                    {displayValue(
                      education.completion_year,
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    CGPA / GPA
                  </dt>
                  <dd className="mt-1 text-sm text-slate-700">
                    {displayValue(
                      education.cgpa_or_gpa,
                    )}
                  </dd>
                </div>
              </div>
            </dl>
          )}
        </article>
      </div>
      <article className="mt-5 rounded-2xl border border-slate-200 p-5">
        <div className="flex items-center justify-between gap-3">
          <h4 className="text-lg font-bold text-slate-900">
            Work Experience
          </h4>
          <span className="text-sm font-medium text-slate-500">
            {
              profile.work_experience
                .length
            }{" "}
            record(s)
          </span>
        </div>
        {profile.work_experience.length
        === 0 ? (
          <p className="mt-4 text-sm text-slate-500">
            No work experience was confirmed.
          </p>
        ) : (
          <div className="mt-4 space-y-3">
            {profile.work_experience.map(
              (
                experience,
                index,
              ) => (
                <div
                  className="rounded-xl bg-slate-50 p-4"
                  key={[
                    experience.company,
                    experience.job_title,
                    index,
                  ].join("-")}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h5 className="font-bold text-slate-900">
                        {displayValue(
                          experience.job_title,
                        )}
                      </h5>
                      <p className="mt-1 text-sm font-medium text-slate-600">
                        {displayValue(
                          experience.company,
                        )}
                      </p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-slate-600 shadow-sm">
                      {displayValue(
                        experience.duration,
                      )}
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-slate-500">
                    {displayValue(
                      experience.start_date,
                    )}
                    {" ? "}
                    {displayValue(
                      experience.end_date,
                    )}
                  </p>
                </div>
              ),
            )}
          </div>
        )}
      </article>
      <article className="mt-5 rounded-2xl border border-slate-200 p-5">
        <h4 className="text-lg font-bold text-slate-900">
          Skills
        </h4>
        <div className="mt-5 space-y-5">
          <SkillGroup
            skills={
              profile.skills
                .technical_skills
            }
            title="Technical skills"
          />
          <SkillGroup
            skills={
              profile.skills
                .tools_and_platforms
            }
            title="Tools and platforms"
          />
          <SkillGroup
            skills={
              profile.skills
                .operational_skills
            }
            title="Relevant operational skills"
          />
        </div>
      </article>
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <article className="rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between gap-3">
            <h4 className="text-lg font-bold text-slate-900">
              Projects
            </h4>
            <span className="text-sm text-slate-500">
              {profile.projects.length}
            </span>
          </div>
          {profile.projects.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">
              No supported project was found.
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {profile.projects.map(
                (
                  project,
                  index,
                ) => (
                  <div
                    className="rounded-xl bg-slate-50 p-4"
                    key={[
                      project.project_title,
                      index,
                    ].join("-")}
                  >
                    <h5 className="font-bold text-slate-900">
                      {displayValue(
                        project.project_title,
                      )}
                    </h5>
                    {project.technologies
                      .length === 0 ? (
                      <p className="mt-2 text-sm text-slate-500">
                        Technologies not confirmed
                      </p>
                    ) : (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {project.technologies.map(
                          (
                            technology,
                            technologyIndex,
                          ) => (
                            <span
                              className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-600"
                              key={[
                                technology,
                                technologyIndex,
                              ].join("-")}
                            >
                              {technology}
                            </span>
                          ),
                        )}
                      </div>
                    )}
                  </div>
                ),
              )}
            </div>
          )}
        </article>
        <article className="rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between gap-3">
            <h4 className="text-lg font-bold text-slate-900">
              Certifications
            </h4>
            <span className="text-sm text-slate-500">
              {
                profile.certifications
                  .length
              }
            </span>
          </div>
          {profile.certifications.length
          === 0 ? (
            <p className="mt-4 text-sm text-slate-500">
              No supported certification was found.
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {profile.certifications.map(
                (
                  certification,
                  index,
                ) => (
                  <div
                    className="rounded-xl bg-slate-50 p-4"
                    key={[
                      certification
                        .certification_title,
                      index,
                    ].join("-")}
                  >
                    <h5 className="font-bold text-slate-900">
                      {displayValue(
                        certification
                          .certification_title,
                      )}
                    </h5>
                    <p className="mt-2 text-sm text-slate-600">
                      {displayValue(
                        certification
                          .issuing_organization,
                      )}
                    </p>
                    <p className="mt-2 text-xs font-medium text-slate-500">
                      Completion date:{" "}
                      {displayValue(
                        certification
                          .completion_date,
                      )}
                    </p>
                  </div>
                ),
              )}
            </div>
          )}
        </article>
      </div>
      <p className="mt-5 text-xs font-medium text-slate-400">
        Last extracted{" "}
        {formatProfileDate(
          profile.updated_at,
        )}
      </p>
    </section>
  );
}

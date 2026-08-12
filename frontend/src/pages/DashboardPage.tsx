import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Link,
} from "react-router-dom";
import {
  listAttendanceEmployees,
  loadAttendanceAnalytics,
  loadAttendanceHistory,
} from "../features/attendance/api";
import {
  listCandidateCVs,
  listJobProfiles,
} from "../features/cv-intelligence/api";
import {
  listDocuments,
} from "../features/documents/api";
type ActivityItem = {
  id: string;
  title: string;
  detail: string;
  timestamp: string;
  href: string;
  label: string;
};
type DashboardData = {
  documents: number;
  candidates: number;
  activeEmployees: number;
  activeJobs: number;
  reportsThisMonth: number;
  attendanceRate: number;
  present: number;
  absent: number;
  onLeave: number;
  weeklyHoliday: number;
  totalAttendanceRecords: number;
  recentActivity: ActivityItem[];
};
const emptyDashboardData: DashboardData = {
  documents: 0,
  candidates: 0,
  activeEmployees: 0,
  activeJobs: 0,
  reportsThisMonth: 0,
  attendanceRate: 0,
  present: 0,
  absent: 0,
  onLeave: 0,
  weeklyHoliday: 0,
  totalAttendanceRecords: 0,
  recentActivity: [],
};
function toApiDate(
  date: Date,
): string {
  const year =
    date.getFullYear();
  const month =
    String(
      date.getMonth() + 1,
    ).padStart(2, "0");
  const day =
    String(
      date.getDate(),
    ).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
function getMonthRange() {
  const today =
    new Date();
  const firstDay =
    new Date(
      today.getFullYear(),
      today.getMonth(),
      1,
    );
  return {
    dateFrom:
      toApiDate(firstDay),
    dateTo:
      toApiDate(today),
  };
}
function normalizeTimestamp(
  value: string,
): string {
  if (
    value.endsWith("Z")
    || /[+-]\d{2}:\d{2}$/.test(value)
  ) {
    return value;
  }
  return `${value}Z`;
}
function timestampValue(
  value: string,
): number {
  const parsed =
    Date.parse(
      normalizeTimestamp(
        value,
      ),
    );
  return Number.isNaN(parsed)
    ? 0
    : parsed;
}
function formatActivityTime(
  value: string,
): string {
  const date =
    new Date(
      normalizeTimestamp(
        value,
      ),
    );
  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "Recent";
  }
  return date.toLocaleString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      timeZone:
        "Asia/Dhaka",
    },
  );
}
function formatAttendanceDate(
  value: string,
): string {
  const parts =
    value.split("-");
  if (
    parts.length !== 3
  ) {
    return value;
  }
  const [
    year,
    month,
    day,
  ] = parts;
  return new Date(
    Number(year),
    Number(month) - 1,
    Number(day),
  ).toLocaleDateString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  );
}
function currentDateLabel():
string {
  return new Date()
    .toLocaleDateString(
      "en-GB",
      {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      },
    );
}
function KpiCard({
  label,
  value,
  detail,
  code,
  badgeClass,
}: {
  label: string;
  value: string;
  detail: string;
  code: string;
  badgeClass: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-500">
            {label}
          </p>
          <p className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            {value}
          </p>
          <p className="mt-2 text-xs font-medium text-slate-400">
            {detail}
          </p>
        </div>
        <div
          className={[
            "flex h-10 min-w-10 items-center justify-center rounded-xl px-2 text-[10px] font-black",
            badgeClass,
          ].join(" ")}
        >
          {code}
        </div>
      </div>
    </article>
  );
}
function StatusRow({
  label,
  value,
  total,
  barClass,
}: {
  label: string;
  value: number;
  total: number;
  barClass: string;
}) {
  const percentage =
    total > 0
      ? Math.min(
          100,
          Math.max(
            0,
            (
              value
              / total
            ) * 100,
          ),
        )
      : 0;
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-semibold text-slate-600">
          {label}
        </span>
        <span className="text-sm font-black text-slate-950">
          {value}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={[
            "h-full rounded-full",
            barClass,
          ].join(" ")}
          style={{
            width:
              `${percentage}%`,
          }}
        />
      </div>
    </div>
  );
}
export function DashboardPage() {
  const [
    data,
    setData,
  ] = useState<DashboardData>(
    emptyDashboardData,
  );
  const [
    isLoading,
    setIsLoading,
  ] = useState(true);
  const [
    warningMessage,
    setWarningMessage,
  ] = useState<
    string | null
  >(null);
  const monthRange =
    useMemo(
      () =>
        getMonthRange(),
      [],
    );
  const loadDashboard =
    useCallback(
      async (): Promise<void> => {
        setIsLoading(true);
        setWarningMessage(
          null,
        );
        const [
          documentsResult,
          candidatesResult,
          jobsResult,
          employeesResult,
          analyticsResult,
          historyResult,
        ] =
          await Promise.allSettled([
            listDocuments(),
            listCandidateCVs(),
            listJobProfiles(),
            listAttendanceEmployees(),
            loadAttendanceAnalytics(
              monthRange.dateFrom,
              monthRange.dateTo,
            ),
            loadAttendanceHistory({
              dateFrom:
                monthRange.dateFrom,
              dateTo:
                monthRange.dateTo,
            }),
          ]);
        const documents =
          documentsResult.status
            === "fulfilled"
            ? documentsResult.value
            : [];
        const candidates =
          candidatesResult.status
            === "fulfilled"
            ? candidatesResult.value
            : [];
        const jobs =
          jobsResult.status
            === "fulfilled"
            ? jobsResult.value
            : [];
        const employees =
          employeesResult.status
            === "fulfilled"
            ? employeesResult.value
            : [];
        const analytics =
          analyticsResult.status
            === "fulfilled"
            ? analyticsResult.value
            : null;
        const history =
          historyResult.status
            === "fulfilled"
            ? historyResult.value
            : null;
        const activities:
          ActivityItem[] = [
            ...documents.map(
              (document) => ({
                id:
                  `doc-${document.id}`,
                title:
                  "HR document added",
                detail:
                  document.original_name,
                timestamp:
                  document.created_at,
                href:
                  "/documents",
                label:
                  "DOC",
              }),
            ),
            ...candidates.map(
              (candidate) => ({
                id:
                  `cv-${candidate.id}`,
                title:
                  "Candidate CV added",
                detail:
                  candidate.original_name,
                timestamp:
                  candidate.created_at,
                href:
                  "/cv-intelligence",
                label:
                  "CV",
              }),
            ),
            ...(
              history?.items
              ?? []
            ).map(
              (report) => ({
                id: [
                  "att",
                  report.attendance_date,
                  report.team_id,
                  report.shift_id,
                ].join("-"),
                title:
                  "Attendance updated",
                detail: [
                  report.team_name,
                  report.shift_name,
                  formatAttendanceDate(
                    report.attendance_date,
                  ),
                ].join(" | "),
                timestamp:
                  report.last_updated_at,
                href:
                  "/attendance",
                label:
                  "ATT",
              }),
            ),
          ];
        activities.sort(
          (a, b) =>
            timestampValue(
              b.timestamp,
            )
            - timestampValue(
              a.timestamp,
            ),
        );
        const failures = [
          documentsResult,
          candidatesResult,
          jobsResult,
          employeesResult,
          analyticsResult,
          historyResult,
        ].filter(
          (result) =>
            result.status
            === "rejected",
        ).length;
        if (
          failures > 0
        ) {
          setWarningMessage(
            "Some dashboard data could not be loaded.",
          );
        }
        setData({
          documents:
            documents.length,
          candidates:
            candidates.length,
          activeEmployees:
            employees.filter(
              (employee) =>
                employee.is_active,
            ).length,
          activeJobs:
            jobs.filter(
              (job) =>
                job.status
                === "active",
            ).length,
          reportsThisMonth:
            history
              ?.total_reports
            ?? 0,
          attendanceRate:
            analytics
              ?.summary
              .attendance_rate
            ?? 0,
          present:
            analytics
              ?.summary
              .present
            ?? 0,
          absent:
            analytics
              ?.summary
              .absent
            ?? 0,
          onLeave:
            analytics
              ?.summary
              .on_leave
            ?? 0,
          weeklyHoliday:
            analytics
              ?.summary
              .weekly_holiday
            ?? 0,
          totalAttendanceRecords:
            analytics
              ?.summary
              .total_records
            ?? 0,
          recentActivity:
            activities.slice(
              0,
              4,
            ),
        });
        setIsLoading(false);
      },
      [
        monthRange.dateFrom,
        monthRange.dateTo,
      ],
    );
  useEffect(() => {
    document.title =
      "Dashboard | PeopleMind AI";
    const timer =
      window.setTimeout(
        () => {
          void loadDashboard();
        },
        0,
      );
    return () => {
      window.clearTimeout(
        timer,
      );
    };
  }, [loadDashboard]);
  const attendanceRate =
    Number.isFinite(
      data.attendanceRate,
    )
      ? data.attendanceRate
      : 0;
  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <section className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-600">
            HR Operations Overview
          </p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950 md:text-4xl">
            PeopleMind AI Dashboard
          </h1>
          <p className="mt-2 text-sm font-medium text-slate-500">
            {currentDateLabel()}
          </p>
        </div>
        <button
          className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
          disabled={isLoading}
          onClick={() => {
            void loadDashboard();
          }}
          type="button"
        >
          {isLoading
            ? "Refreshing..."
            : "Refresh Data"}
        </button>
      </section>
      {warningMessage ? (
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-700">
          {warningMessage}
        </div>
      ) : null}
      <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          badgeClass="bg-emerald-100 text-emerald-700"
          code="EMP"
          detail="Active workforce"
          label="Employees"
          value={
            isLoading
              ? "..."
              : String(
                  data.activeEmployees,
                )
          }
        />
        <KpiCard
          badgeClass="bg-sky-100 text-sky-700"
          code="ATT"
          detail="Month to date"
          label="Attendance Rate"
          value={
            isLoading
              ? "..."
              : `${attendanceRate.toFixed(1)}%`
          }
        />
        <KpiCard
          badgeClass="bg-violet-100 text-violet-700"
          code="CV"
          detail="Candidate profiles"
          label="Candidates"
          value={
            isLoading
              ? "..."
              : String(
                  data.candidates,
                )
          }
        />
        <KpiCard
          badgeClass="bg-amber-100 text-amber-700"
          code="DOC"
          detail="HR knowledge base"
          label="Documents"
          value={
            isLoading
              ? "..."
              : String(
                  data.documents,
                )
          }
        />
      </section>
      <section className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_0.7fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                Workforce Performance
              </p>
              <h2 className="mt-2 text-xl font-black text-slate-950">
                Attendance Overview
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Current month through today
              </p>
            </div>
            <Link
              className="text-sm font-bold text-sky-700 hover:text-sky-900"
              to="/attendance"
            >
              View Details
            </Link>
          </div>
          <div className="mt-8 grid gap-8 md:grid-cols-[230px_1fr] md:items-center">
            <div className="mx-auto">
              <div
                className="relative flex h-48 w-48 items-center justify-center rounded-full"
                style={{
                  background:
                    `conic-gradient(#0f172a ${attendanceRate}%, #e2e8f0 ${attendanceRate}% 100%)`,
                }}
              >
                <div className="flex h-36 w-36 flex-col items-center justify-center rounded-full bg-white shadow-inner">
                  <span className="text-4xl font-black text-slate-950">
                    {isLoading
                      ? "..."
                      : `${attendanceRate.toFixed(0)}%`}
                  </span>
                  <span className="mt-1 text-xs font-bold uppercase tracking-wide text-slate-400">
                    Attendance
                  </span>
                </div>
              </div>
            </div>
            <div className="space-y-5">
              <StatusRow
                barClass="bg-emerald-500"
                label="Present"
                total={
                  data.totalAttendanceRecords
                }
                value={
                  data.present
                }
              />
              <StatusRow
                barClass="bg-red-500"
                label="Absent"
                total={
                  data.totalAttendanceRecords
                }
                value={
                  data.absent
                }
              />
              <StatusRow
                barClass="bg-amber-500"
                label="On Leave"
                total={
                  data.totalAttendanceRecords
                }
                value={
                  data.onLeave
                }
              />
              <StatusRow
                barClass="bg-sky-500"
                label="Weekly Holiday"
                total={
                  data.totalAttendanceRecords
                }
                value={
                  data.weeklyHoliday
                }
              />
            </div>
          </div>
          <div className="mt-8 grid grid-cols-2 gap-4 border-t border-slate-100 pt-5 md:grid-cols-4">
            <div>
              <p className="text-xs font-semibold text-slate-400">
                Present
              </p>
              <p className="mt-1 text-xl font-black text-emerald-600">
                {data.present}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-400">
                Absent
              </p>
              <p className="mt-1 text-xl font-black text-red-600">
                {data.absent}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-400">
                Reports
              </p>
              <p className="mt-1 text-xl font-black text-slate-950">
                {data.reportsThisMonth}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-400">
                Records
              </p>
              <p className="mt-1 text-xl font-black text-slate-950">
                {
                  data
                    .totalAttendanceRecords
                }
              </p>
            </div>
          </div>
        </article>
        <article className="rounded-3xl bg-slate-950 p-6 text-white shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.18em] text-sky-400">
            HR Snapshot
          </p>
          <h2 className="mt-2 text-xl font-black">
            Workspace Summary
          </h2>
          <div className="mt-7 divide-y divide-white/10">
            <div className="flex items-center justify-between py-4">
              <span className="text-sm text-slate-400">
                Active jobs
              </span>
              <span className="text-xl font-black">
                {data.activeJobs}
              </span>
            </div>
            <div className="flex items-center justify-between py-4">
              <span className="text-sm text-slate-400">
                Candidate CVs
              </span>
              <span className="text-xl font-black">
                {data.candidates}
              </span>
            </div>
            <div className="flex items-center justify-between py-4">
              <span className="text-sm text-slate-400">
                HR documents
              </span>
              <span className="text-xl font-black">
                {data.documents}
              </span>
            </div>
            <div className="flex items-center justify-between py-4">
              <span className="text-sm text-slate-400">
                Attendance reports
              </span>
              <span className="text-xl font-black">
                {
                  data
                    .reportsThisMonth
                }
              </span>
            </div>
          </div>
          <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              System Status
            </p>
            <div className="mt-3 flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
              <span className="text-sm font-bold text-emerald-300">
                All HR modules available
              </span>
            </div>
          </div>
        </article>
      </section>
      <section className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">
              Latest Updates
            </p>
            <h2 className="mt-2 text-xl font-black text-slate-950">
              Recent Activity
            </h2>
          </div>
          <div className="mt-5">
            {isLoading ? (
              <p className="py-8 text-center text-sm font-semibold text-slate-400">
                Loading activity...
              </p>
            ) : data.recentActivity.length === 0 ? (
              <p className="py-8 text-center text-sm font-semibold text-slate-400">
                No recent activity.
              </p>
            ) : (
              <div className="divide-y divide-slate-100">
                {data.recentActivity.map(
                  (activity) => (
                    <Link
                      className="flex items-center gap-4 py-4"
                      key={
                        activity.id
                      }
                      to={
                        activity.href
                      }
                    >
                      <div className="flex h-10 min-w-10 items-center justify-center rounded-xl bg-slate-100 px-2 text-[10px] font-black text-slate-600">
                        {
                          activity.label
                        }
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-bold text-slate-900">
                          {
                            activity.title
                          }
                        </p>
                        <p className="mt-1 truncate text-sm text-slate-500">
                          {
                            activity.detail
                          }
                        </p>
                      </div>
                      <time className="hidden text-xs font-bold text-slate-500 sm:block">
                        {formatActivityTime(
                          activity
                            .timestamp,
                        )}
                      </time>
                    </Link>
                  ),
                )}
              </div>
            )}
          </div>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">
            Shortcuts
          </p>
          <h2 className="mt-2 text-xl font-black text-slate-950">
            Quick Actions
          </h2>
          <div className="mt-6 space-y-3">
            <Link
              className="flex items-center justify-between rounded-2xl bg-sky-50 px-5 py-4 font-bold text-sky-800 transition hover:bg-sky-100"
              to="/documents"
            >
              <span>
                Ask Policy AI
              </span>
              <span>&gt;</span>
            </Link>
            <Link
              className="flex items-center justify-between rounded-2xl bg-violet-50 px-5 py-4 font-bold text-violet-800 transition hover:bg-violet-100"
              to="/cv-intelligence"
            >
              <span>
                Review Candidates
              </span>
              <span>&gt;</span>
            </Link>
            <Link
              className="flex items-center justify-between rounded-2xl bg-emerald-50 px-5 py-4 font-bold text-emerald-800 transition hover:bg-emerald-100"
              to="/attendance"
            >
              <span>
                Manage Attendance
              </span>
              <span>&gt;</span>
            </Link>
          </div>
          <div className="mt-7 border-t border-slate-100 pt-5">
            <p className="text-xs leading-5 text-slate-400">
              PeopleMind AI keeps employment
              decisions under human review while
              supporting HR teams with local
              intelligence.
            </p>
          </div>
        </article>
      </section>
    </main>
  );
}

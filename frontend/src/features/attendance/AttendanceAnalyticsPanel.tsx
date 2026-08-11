import axios from "axios";
import {
  useState,
} from "react";
import {
  loadAttendanceAnalytics,
} from "./api";
import type {
  AttendanceAnalyticsRead,
  AttendanceShift,
  AttendanceTeam,
} from "./types";
interface AttendanceAnalyticsPanelProps {
  teams: AttendanceTeam[];
  shifts: AttendanceShift[];
}
function localDateString(
  value: Date,
): string {
  const timezoneOffset =
    value.getTimezoneOffset()
    * 60
    * 1000;
  return new Date(
    value.getTime()
    - timezoneOffset,
  )
    .toISOString()
    .slice(0, 10);
}
function getDefaultDates(): {
  dateFrom: string;
  dateTo: string;
} {
  const now = new Date();
  const firstDay =
    new Date(
      now.getFullYear(),
      now.getMonth(),
      1,
    );
  return {
    dateFrom:
      localDateString(firstDay),
    dateTo:
      localDateString(now),
  };
}
function getApiErrorMessage(
  error: unknown,
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
  return (
    "Could not load attendance analytics."
  );
}
function formatDate(
  value: string,
): string {
  const date =
    new Date(
      `${value}T00:00:00`,
    );
  return date.toLocaleDateString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  );
}
function formatShortDate(
  value: string,
): string {
  const date =
    new Date(
      `${value}T00:00:00`,
    );
  return date.toLocaleDateString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
    },
  );
}
function rateWidth(
  value: number,
): string {
  return `${
    Math.max(
      0,
      Math.min(
        100,
        value,
      ),
    )
  }%`;
}
function rateTextClass(
  value: number,
): string {
  if (value >= 90) {
    return "text-emerald-700";
  }
  if (value >= 75) {
    return "text-amber-700";
  }
  return "text-red-700";
}
function rateBarClass(
  value: number,
): string {
  if (value >= 90) {
    return "bg-emerald-500";
  }
  if (value >= 75) {
    return "bg-amber-500";
  }
  return "bg-red-500";
}
export function AttendanceAnalyticsPanel({
  teams,
  shifts,
}: AttendanceAnalyticsPanelProps) {
  const defaults =
    getDefaultDates();
  const [
    dateFrom,
    setDateFrom,
  ] = useState(
    defaults.dateFrom,
  );
  const [
    dateTo,
    setDateTo,
  ] = useState(
    defaults.dateTo,
  );
  const [
    teamId,
    setTeamId,
  ] = useState("");
  const [
    shiftId,
    setShiftId,
  ] = useState("");
  const [
    analytics,
    setAnalytics,
  ] = useState<
    AttendanceAnalyticsRead | null
  >(null);
  const [
    isLoading,
    setIsLoading,
  ] = useState(false);
  const [
    errorMessage,
    setErrorMessage,
  ] = useState<
    string | null
  >(null);
  async function loadDashboard():
    Promise<void> {
        if (
          !dateFrom
          || !dateTo
        ) {
          setErrorMessage(
            "Select both dates.",
          );
          return;
        }
        if (
          dateFrom > dateTo
        ) {
          setErrorMessage(
            "From date cannot be later than To date.",
          );
          return;
        }
        setIsLoading(true);
        setErrorMessage(null);
        try {
          const result =
            await loadAttendanceAnalytics(
              dateFrom,
              dateTo,
              teamId
                ? Number(teamId)
                : undefined,
              shiftId
                ? Number(shiftId)
                : undefined,
            );
          setAnalytics(result);
        } catch (error) {
          setErrorMessage(
            getApiErrorMessage(
              error,
            ),
          );
        } finally {
          setIsLoading(false);
        }
    }
  const summary =
    analytics?.summary;
  return (
    <section className="mt-8 space-y-7">
      <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm lg:p-7">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-600">
              Workforce intelligence
            </p>
            <h2 className="mt-2 text-2xl font-bold text-slate-950">
              Attendance Analytics
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Analyse attendance performance
              across dates, teams, shifts and
              individual employees.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                From
              </span>
              <input
                className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-800"
                onChange={(event) => {
                  setDateFrom(
                    event.target.value,
                  );
                }}
                type="date"
                value={dateFrom}
              />
            </label>
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                To
              </span>
              <input
                className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-800"
                onChange={(event) => {
                  setDateTo(
                    event.target.value,
                  );
                }}
                type="date"
                value={dateTo}
              />
            </label>
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Team
              </span>
              <select
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800"
                onChange={(event) => {
                  setTeamId(
                    event.target.value,
                  );
                }}
                value={teamId}
              >
                <option value="">
                  All teams
                </option>
                {teams.map(
                  (team) => (
                    <option
                      key={team.id}
                      value={team.id}
                    >
                      {team.name}
                    </option>
                  ),
                )}
              </select>
            </label>
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Shift
              </span>
              <select
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800"
                onChange={(event) => {
                  setShiftId(
                    event.target.value,
                  );
                }}
                value={shiftId}
              >
                <option value="">
                  All shifts
                </option>
                {shifts.map(
                  (shift) => (
                    <option
                      key={shift.id}
                      value={shift.id}
                    >
                      {shift.name}
                    </option>
                  ),
                )}
              </select>
            </label>
            <button
              className="self-end rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-bold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isLoading}
              onClick={() => {
                void loadDashboard();
              }}
              type="button"
            >
              {isLoading
                ? "Loading..."
                : "Refresh"}
            </button>
          </div>
        </div>
        {analytics ? (
          <p className="mt-5 text-xs font-semibold text-slate-500">
            Showing{" "}
            {formatDate(
              analytics.date_from,
            )}{" "}
            to{" "}
            {formatDate(
              analytics.date_to,
            )}
          </p>
        ) : null}
      </article>
      {errorMessage ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {errorMessage}
        </div>
      ) : null}
      {summary ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
            <article className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                Attendance Rate
              </p>
              <p className="mt-3 text-3xl font-black text-emerald-800">
                {summary.attendance_rate.toFixed(
                  1,
                )}
                %
              </p>
              <p className="mt-2 text-xs text-emerald-700">
                Working-day attendance
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Present
              </p>
              <p className="mt-3 text-3xl font-black text-slate-950">
                {summary.present}
              </p>
              <p className="mt-2 text-xs text-slate-500">
                Recorded present
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Absent
              </p>
              <p className="mt-3 text-3xl font-black text-red-600">
                {summary.absent}
              </p>
              <p className="mt-2 text-xs text-slate-500">
                Recorded absent
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                On Leave
              </p>
              <p className="mt-3 text-3xl font-black text-amber-600">
                {summary.on_leave}
              </p>
              <p className="mt-2 text-xs text-slate-500">
                Approved or recorded leave
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Weekly Holiday
              </p>
              <p className="mt-3 text-3xl font-black text-blue-600">
                {summary.weekly_holiday}
              </p>
              <p className="mt-2 text-xs text-slate-500">
                Excluded from rate
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Total Records
              </p>
              <p className="mt-3 text-3xl font-black text-slate-950">
                {summary.total_records}
              </p>
              <p className="mt-2 text-xs text-slate-500">
                Attendance entries
              </p>
            </article>
          </div>
          <article className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
            <p className="text-sm font-semibold text-slate-700">
              Attendance Rate =
              Present /
              (Present + Absent + On Leave).
              Weekly holidays are excluded.
            </p>
          </article>
          <div className="grid gap-7 xl:grid-cols-[1.35fr_0.65fr]">
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-xl font-bold text-slate-950">
                    Daily Attendance Trend
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Attendance rate by recorded day.
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                  {
                    analytics
                      ?.daily_trend
                      .length
                  }{" "}
                  days
                </span>
              </div>
              <div className="mt-6 space-y-5">
                {analytics
                  ?.daily_trend
                  .length ? (
                  analytics.daily_trend.map(
                    (item) => (
                      <div
                        key={
                          item.attendance_date
                        }
                      >
                        <div className="mb-2 flex items-center justify-between gap-4">
                          <div>
                            <p className="text-sm font-bold text-slate-800">
                              {formatShortDate(
                                item.attendance_date,
                              )}
                            </p>
                            <p className="text-xs text-slate-500">
                              {
                                item.present
                              }{" "}
                              present |{" "}
                              {
                                item.absent
                              }{" "}
                              absent |{" "}
                              {
                                item.on_leave
                              }{" "}
                              leave
                            </p>
                          </div>
                          <p
                            className={`text-sm font-black ${rateTextClass(
                              item.attendance_rate,
                            )}`}
                          >
                            {item.attendance_rate.toFixed(
                              1,
                            )}
                            %
                          </p>
                        </div>
                        <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full transition-all ${rateBarClass(
                              item.attendance_rate,
                            )}`}
                            style={{
                              width:
                                rateWidth(
                                  item.attendance_rate,
                                ),
                            }}
                          />
                        </div>
                      </div>
                    ),
                  )
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-300 px-5 py-10 text-center text-sm text-slate-500">
                    No attendance records
                    found for this period.
                  </div>
                )}
              </div>
            </article>
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-xl font-bold text-slate-950">
                Period Summary
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Working days versus holidays.
              </p>
              <div className="mt-6 space-y-4">
                <div className="rounded-2xl bg-slate-50 p-5">
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Working-day records
                  </p>
                  <p className="mt-2 text-3xl font-black text-slate-950">
                    {
                      summary.working_day_records
                    }
                  </p>
                </div>
                <div className="rounded-2xl bg-blue-50 p-5">
                  <p className="text-xs font-bold uppercase tracking-wide text-blue-600">
                    Holiday records
                  </p>
                  <p className="mt-2 text-3xl font-black text-blue-700">
                    {
                      summary.weekly_holiday
                    }
                  </p>
                </div>
                <div className="rounded-2xl bg-emerald-50 p-5">
                  <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                    Present share
                  </p>
                  <p className="mt-2 text-3xl font-black text-emerald-800">
                    {
                      summary.attendance_rate.toFixed(
                        1,
                      )
                    }
                    %
                  </p>
                </div>
              </div>
            </article>
          </div>
          <div className="grid gap-7 xl:grid-cols-2">
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-xl font-bold text-slate-950">
                Team Comparison
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Compare attendance rate
                across recorded teams.
              </p>
              <div className="mt-6 space-y-5">
                {analytics
                  ?.teams
                  .length ? (
                  analytics.teams.map(
                    (item) => (
                      <div
                        key={
                          item.team_id
                        }
                      >
                        <div className="mb-2 flex items-start justify-between gap-4">
                          <div>
                            <p className="font-bold text-slate-800">
                              {
                                item.team_name
                              }
                            </p>
                            <p className="mt-0.5 text-xs text-slate-500">
                              {
                                item.present
                              }{" "}
                              present |{" "}
                              {
                                item.absent
                              }{" "}
                              absent |{" "}
                              {
                                item.on_leave
                              }{" "}
                              leave
                            </p>
                          </div>
                          <p
                            className={`font-black ${rateTextClass(
                              item.attendance_rate,
                            )}`}
                          >
                            {item.attendance_rate.toFixed(
                              1,
                            )}
                            %
                          </p>
                        </div>
                        <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full ${rateBarClass(
                              item.attendance_rate,
                            )}`}
                            style={{
                              width:
                                rateWidth(
                                  item.attendance_rate,
                                ),
                            }}
                          />
                        </div>
                      </div>
                    ),
                  )
                ) : (
                  <p className="text-sm text-slate-500">
                    No team data available.
                  </p>
                )}
              </div>
            </article>
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-xl font-bold text-slate-950">
                Shift Comparison
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Compare attendance rate
                across recorded shifts.
              </p>
              <div className="mt-6 space-y-5">
                {analytics
                  ?.shifts
                  .length ? (
                  analytics.shifts.map(
                    (item) => (
                      <div
                        key={
                          item.shift_id
                        }
                      >
                        <div className="mb-2 flex items-start justify-between gap-4">
                          <div>
                            <p className="font-bold text-slate-800">
                              {
                                item.shift_name
                              }
                            </p>
                            <p className="mt-0.5 text-xs text-slate-500">
                              {
                                item.present
                              }{" "}
                              present |{" "}
                              {
                                item.absent
                              }{" "}
                              absent |{" "}
                              {
                                item.on_leave
                              }{" "}
                              leave
                            </p>
                          </div>
                          <p
                            className={`font-black ${rateTextClass(
                              item.attendance_rate,
                            )}`}
                          >
                            {item.attendance_rate.toFixed(
                              1,
                            )}
                            %
                          </p>
                        </div>
                        <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full ${rateBarClass(
                              item.attendance_rate,
                            )}`}
                            style={{
                              width:
                                rateWidth(
                                  item.attendance_rate,
                                ),
                            }}
                          />
                        </div>
                      </div>
                    ),
                  )
                ) : (
                  <p className="text-sm text-slate-500">
                    No shift data available.
                  </p>
                )}
              </div>
            </article>
          </div>
          <article className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-6 py-5">
              <h3 className="text-xl font-bold text-slate-950">
                Employee Attendance Summary
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Individual attendance
                performance for the selected
                period.
              </p>
            </div>
            {analytics
              ?.employees
              .length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      {[
                        "Employee",
                        "Team / Shift",
                        "Present",
                        "Absent",
                        "Leave",
                        "Holiday",
                        "Rate",
                      ].map(
                        (heading) => (
                          <th
                            className="whitespace-nowrap px-5 py-3 text-left text-xs font-black uppercase tracking-wide text-slate-500"
                            key={
                              heading
                            }
                          >
                            {
                              heading
                            }
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {
                      analytics.employees.map(
                        (employee) => (
                          <tr
                            className="hover:bg-slate-50"
                            key={[
                              employee.employee_id,
                              employee.team_id,
                              employee.shift_id,
                            ].join("-")}
                          >
                            <td className="px-5 py-4">
                              <p className="font-bold text-slate-900">
                                {
                                  employee.full_name
                                }
                              </p>
                              <p className="mt-1 text-xs text-slate-500">
                                {
                                  employee.employee_code
                                }{" "}
                                {" | "}
                                {
                                  employee.designation
                                }
                              </p>
                            </td>
                            <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
                              <p className="font-semibold text-slate-800">
                                {
                                  employee.team_name
                                }
                              </p>
                              <p className="mt-1 text-xs text-slate-500">
                                {
                                  employee.shift_name
                                }
                              </p>
                            </td>
                            <td className="px-5 py-4 text-sm font-bold text-emerald-700">
                              {
                                employee.present
                              }
                            </td>
                            <td className="px-5 py-4 text-sm font-bold text-red-600">
                              {
                                employee.absent
                              }
                            </td>
                            <td className="px-5 py-4 text-sm font-bold text-amber-600">
                              {
                                employee.on_leave
                              }
                            </td>
                            <td className="px-5 py-4 text-sm font-bold text-blue-600">
                              {
                                employee.weekly_holiday
                              }
                            </td>
                            <td className="px-5 py-4">
                              <span
                                className={`whitespace-nowrap rounded-full bg-slate-100 px-3 py-1.5 text-xs font-black ${rateTextClass(
                                  employee.attendance_rate,
                                )}`}
                              >
                                {employee.attendance_rate.toFixed(
                                  1,
                                )}
                                %
                              </span>
                            </td>
                          </tr>
                        ),
                      )
                    }
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="px-6 py-12 text-center text-sm text-slate-500">
                No employee attendance
                records found for this period.
              </div>
            )}
          </article>
        </>
      ) : (
        <article className="rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="text-sm font-semibold text-slate-500">
            {isLoading
              ? "Loading attendance analytics..."
              : "Select a date range to view analytics."}
          </p>
        </article>
      )}
    </section>
  );
}

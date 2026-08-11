import axios from "axios";
import {
  useState,
} from "react";
import {
  downloadEmployeeMonthlyCsv,
  downloadEmployeeMonthlyPdf,
  loadEmployeeMonthlyReport,
} from "./api";
import type {
  AttendanceEmployee,
  AttendanceEmployeeMonthlyReport,
  AttendanceMonthlyDay,
  AttendanceMonthlyDayStatus,
} from "./types";
interface EmployeeMonthlyReportPanelProps {
  employees: AttendanceEmployee[];
}
const monthOptions = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];
const weekdayHeaders = [
  "Mon",
  "Tue",
  "Wed",
  "Thu",
  "Fri",
  "Sat",
  "Sun",
];
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
    "Could not load employee monthly report."
  );
}
function formatStatus(
  status: AttendanceMonthlyDayStatus,
): string {
  const labels: Record<
    AttendanceMonthlyDayStatus,
    string
  > = {
    present: "Present",
    absent: "Absent",
    on_leave: "On Leave",
    weekly_holiday: "Weekly Holiday",
    not_recorded: "Not Recorded",
  };
  return labels[status];
}
function statusCardClass(
  status: AttendanceMonthlyDayStatus,
): string {
  const classes: Record<
    AttendanceMonthlyDayStatus,
    string
  > = {
    present:
      "border-emerald-200 bg-emerald-50 text-emerald-800",
    absent:
      "border-red-200 bg-red-50 text-red-700",
    on_leave:
      "border-amber-200 bg-amber-50 text-amber-800",
    weekly_holiday:
      "border-blue-200 bg-blue-50 text-blue-700",
    not_recorded:
      "border-slate-200 bg-slate-50 text-slate-500",
  };
  return classes[status];
}
function statusBadgeClass(
  status: AttendanceMonthlyDayStatus,
): string {
  const classes: Record<
    AttendanceMonthlyDayStatus,
    string
  > = {
    present:
      "bg-emerald-100 text-emerald-700",
    absent:
      "bg-red-100 text-red-700",
    on_leave:
      "bg-amber-100 text-amber-700",
    weekly_holiday:
      "bg-blue-100 text-blue-700",
    not_recorded:
      "bg-slate-100 text-slate-600",
  };
  return classes[status];
}
function formatDate(
  value: string,
): string {
  return new Date(
    `${value}T00:00:00`,
  ).toLocaleDateString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  );
}
function leaveTypeLabel(
  value: string | null,
): string {
  if (!value) {
    return "";
  }
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}
function firstDayOffset(
  report: AttendanceEmployeeMonthlyReport,
): number {
  const firstDay =
    new Date(
      `${report.year}-${String(
        report.month,
      ).padStart(2, "0")}-01T00:00:00`,
    );
  return (
    firstDay.getDay() + 6
  ) % 7;
}
export function EmployeeMonthlyReportPanel({
  employees,
}: EmployeeMonthlyReportPanelProps) {
  const now = new Date();
  const [
    employeeId,
    setEmployeeId,
  ] = useState("");
  const [
    year,
    setYear,
  ] = useState(
    now.getFullYear(),
  );
  const [
    month,
    setMonth,
  ] = useState(
    now.getMonth() + 1,
  );
  const [
    report,
    setReport,
  ] = useState<
    AttendanceEmployeeMonthlyReport | null
  >(null);
  const [
    isLoading,
    setIsLoading,
  ] = useState(false);
  const [
    isCsvExporting,
    setIsCsvExporting,
  ] = useState(false);
  const [
    isPdfExporting,
    setIsPdfExporting,
  ] = useState(false);
  const [
    errorMessage,
    setErrorMessage,
  ] = useState<
    string | null
  >(null);
  async function loadReport():
    Promise<void> {
    if (!employeeId) {
      setErrorMessage(
        "Select an employee first.",
      );
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const result =
        await loadEmployeeMonthlyReport(
          Number(employeeId),
          year,
          month,
        );
      setReport(result);
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
  function saveBlob(
    blob: Blob,
    filename: string,
  ): void {
    const url =
      URL.createObjectURL(blob);
    const link =
      document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(
      link,
    );
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }
  async function downloadCsv():
    Promise<void> {
    if (!report) {
      return;
    }
    setErrorMessage(null);
    setIsCsvExporting(true);
    try {
      const blob =
        await downloadEmployeeMonthlyCsv(
          report.employee_id,
          report.year,
          report.month,
        );
      saveBlob(
        blob,
        [
          "employee_attendance",
          report.employee_code,
          `${report.year}-${String(
            report.month,
          ).padStart(2, "0")}`,
        ].join("_") + ".csv",
      );
    } catch {
      setErrorMessage(
        "Could not download the CSV report.",
      );
    } finally {
      setIsCsvExporting(false);
    }
  }
  async function downloadPdf():
    Promise<void> {
    if (!report) {
      return;
    }
    setErrorMessage(null);
    setIsPdfExporting(true);
    try {
      const blob =
        await downloadEmployeeMonthlyPdf(
          report.employee_id,
          report.year,
          report.month,
        );
      saveBlob(
        blob,
        [
          "employee_attendance",
          report.employee_code,
          `${report.year}-${String(
            report.month,
          ).padStart(2, "0")}`,
        ].join("_") + ".pdf",
      );
    } catch {
      setErrorMessage(
        "Could not download the PDF report.",
      );
    } finally {
      setIsPdfExporting(false);
    }
  }
  const recordedDays =
    report?.days.filter(
      (day) =>
        day.is_recorded,
    ) ?? [];
  return (
    <section className="mt-8 space-y-7">
      <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm lg:p-7">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-600">
              Individual attendance
            </p>
            <h2 className="mt-2 text-2xl font-bold text-slate-950">
              Employee Monthly Report
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Review one employee's monthly
              attendance, calendar and
              date-wise attendance history.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-[minmax(220px,1.5fr)_110px_150px_auto]">
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Employee
              </span>
              <select
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800"
                onChange={(event) => {
                  setEmployeeId(
                    event.target.value,
                  );
                  setReport(null);
                }}
                value={employeeId}
              >
                <option value="">
                  Select employee
                </option>
                {employees.map(
                  (employee) => (
                    <option
                      key={
                        employee.id
                      }
                      value={
                        employee.id
                      }
                    >
                      {
                        employee.employee_code
                      }{" "}
                      -{" "}
                      {
                        employee.full_name
                      }
                    </option>
                  ),
                )}
              </select>
            </label>
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Year
              </span>
              <input
                className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-800"
                max={2100}
                min={2000}
                onChange={(event) => {
                  setYear(
                    Number(
                      event.target.value,
                    ),
                  );
                  setReport(null);
                }}
                type="number"
                value={year}
              />
            </label>
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Month
              </span>
              <select
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800"
                onChange={(event) => {
                  setMonth(
                    Number(
                      event.target.value,
                    ),
                  );
                  setReport(null);
                }}
                value={month}
              >
                {monthOptions.map(
                  (
                    monthName,
                    index,
                  ) => (
                    <option
                      key={
                        monthName
                      }
                      value={
                        index + 1
                      }
                    >
                      {monthName}
                    </option>
                  ),
                )}
              </select>
            </label>
            <button
              className="self-end rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-bold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isLoading}
              onClick={() => {
                void loadReport();
              }}
              type="button"
            >
              {isLoading
                ? "Loading..."
                : "View Report"}
            </button>
          </div>
        </div>
      </article>
      {errorMessage ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {errorMessage}
        </div>
      ) : null}
      {report ? (
        <>
          <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm lg:p-7">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                  {report.employee_code}
                </p>
                <h3 className="mt-2 text-2xl font-black text-slate-950">
                  {report.full_name}
                </h3>
                <p className="mt-2 text-sm font-semibold text-slate-600">
                  {report.designation}
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  {report.team_name}
                  {" | "}
                  {report.shift_name}
                </p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  className="rounded-xl border border-emerald-300 bg-white px-4 py-3 text-sm font-bold text-emerald-700 transition hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={isCsvExporting}
                  onClick={() => {
                    void downloadCsv();
                  }}
                  type="button"
                >
                  {isCsvExporting
                    ? "Preparing CSV..."
                    : "Download CSV"}
                </button>
                <button
                  className="rounded-xl border border-violet-300 bg-white px-4 py-3 text-sm font-bold text-violet-700 transition hover:bg-violet-50 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={isPdfExporting}
                  onClick={() => {
                    void downloadPdf();
                  }}
                  type="button"
                >
                  {isPdfExporting
                    ? "Preparing PDF..."
                    : "Download PDF"}
                </button>
                <div className="rounded-2xl bg-slate-950 px-6 py-4 text-white">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-300">
                    Reporting month
                  </p>
                  <p className="mt-2 text-xl font-black">
                    {report.month_label}
                  </p>
                </div>
              </div>
            </div>
          </article>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
            <article className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                Attendance Rate
              </p>
              <p className="mt-3 text-3xl font-black text-emerald-800">
                {
                  report.summary.attendance_rate.toFixed(
                    1,
                  )
                }
                %
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Present
              </p>
              <p className="mt-3 text-3xl font-black text-emerald-700">
                {
                  report.summary.present
                }
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Absent
              </p>
              <p className="mt-3 text-3xl font-black text-red-600">
                {
                  report.summary.absent
                }
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                On Leave
              </p>
              <p className="mt-3 text-3xl font-black text-amber-600">
                {
                  report.summary.on_leave
                }
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Holiday
              </p>
              <p className="mt-3 text-3xl font-black text-blue-600">
                {
                  report.summary.weekly_holiday
                }
              </p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Not Recorded
              </p>
              <p className="mt-3 text-3xl font-black text-slate-500">
                {
                  report.summary.not_recorded_days
                }
              </p>
            </article>
          </div>
          <article className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
            <div className="flex flex-wrap gap-x-7 gap-y-2 text-sm font-semibold text-slate-700">
              <span>
                Recorded days:{" "}
                {
                  report.summary.recorded_days
                }
              </span>
              <span>
                Working-day records:{" "}
                {
                  report.summary.working_day_records
                }
              </span>
              <span>
                Days in month:{" "}
                {
                  report.summary.days_in_month
                }
              </span>
              <span>
                Rate = Present /
                (Present + Absent + On Leave)
              </span>
            </div>
          </article>
          <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm lg:p-7">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-xl font-bold text-slate-950">
                  Monthly Calendar
                </h3>
                <p className="mt-1 text-sm text-slate-500">
                  Unsubmitted dates remain
                  Not Recorded.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 text-xs font-bold">
                {[
                  "present",
                  "absent",
                  "on_leave",
                  "weekly_holiday",
                  "not_recorded",
                ].map(
                  (status) => (
                    <span
                      className={`rounded-full px-3 py-1.5 ${statusBadgeClass(
                        status as AttendanceMonthlyDayStatus,
                      )}`}
                      key={
                        status
                      }
                    >
                      {formatStatus(
                        status as AttendanceMonthlyDayStatus,
                      )}
                    </span>
                  ),
                )}
              </div>
            </div>
            <div className="mt-6 grid grid-cols-7 gap-2">
              {weekdayHeaders.map(
                (weekday) => (
                  <div
                    className="px-2 py-2 text-center text-xs font-black uppercase tracking-wide text-slate-400"
                    key={weekday}
                  >
                    {weekday}
                  </div>
                ),
              )}
              {Array.from({
                length:
                  firstDayOffset(
                    report,
                  ),
              }).map(
                (
                  _,
                  index,
                ) => (
                  <div
                    aria-hidden="true"
                    key={`empty-${index}`}
                  />
                ),
              )}
              {report.days.map(
                (day) => (
                  <div
                    className={`min-h-28 rounded-2xl border p-3 ${statusCardClass(
                      day.status,
                    )}`}
                    key={
                      day.attendance_date
                    }
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-lg font-black">
                        {
                          Number(
                            day.attendance_date.slice(
                              -2,
                            ),
                          )
                        }
                      </p>
                      <span className="text-[10px] font-black uppercase tracking-wide opacity-70">
                        {
                          day.weekday.slice(
                            0,
                            3,
                          )
                        }
                      </span>
                    </div>
                    <p className="mt-4 text-xs font-black">
                      {formatStatus(
                        day.status,
                      )}
                    </p>
                    {day.leave_type ? (
                      <p className="mt-1 text-[11px] font-semibold opacity-80">
                        {leaveTypeLabel(
                          day.leave_type,
                        )}
                      </p>
                    ) : null}
                  </div>
                ),
              )}
            </div>
          </article>
          <article className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-6 py-5">
              <h3 className="text-xl font-bold text-slate-950">
                Date-wise Attendance History
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Only submitted attendance
                records are listed here.
              </p>
            </div>
            {recordedDays.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      {[
                        "Date",
                        "Status",
                        "Team / Shift",
                        "Leave Details",
                        "Note",
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
                    {recordedDays.map(
                      (
                        day:
                          AttendanceMonthlyDay,
                      ) => (
                        <tr
                          className="hover:bg-slate-50"
                          key={
                            day.attendance_date
                          }
                        >
                          <td className="whitespace-nowrap px-5 py-4">
                            <p className="font-bold text-slate-900">
                              {formatDate(
                                day.attendance_date,
                              )}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {
                                day.weekday
                              }
                            </p>
                          </td>
                          <td className="px-5 py-4">
                            <span
                              className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-black ${statusBadgeClass(
                                day.status,
                              )}`}
                            >
                              {formatStatus(
                                day.status,
                              )}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
                            <p className="font-semibold text-slate-800">
                              {
                                day.team_name
                              }
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {
                                day.shift_name
                              }
                            </p>
                          </td>
                          <td className="max-w-xs px-5 py-4 text-sm text-slate-600">
                            {day.leave_type ? (
                              <>
                                <p className="font-bold text-slate-800">
                                  {leaveTypeLabel(
                                    day.leave_type,
                                  )}
                                </p>
                                {day.leave_from_date
                                && day.leave_to_date ? (
                                  <p className="mt-1 text-xs text-slate-500">
                                    {formatDate(
                                      day.leave_from_date,
                                    )}
                                    {" to "}
                                    {formatDate(
                                      day.leave_to_date,
                                    )}
                                  </p>
                                ) : null}
                                {day.leave_reason ? (
                                  <p className="mt-1 text-xs text-slate-500">
                                    {
                                      day.leave_reason
                                    }
                                  </p>
                                ) : null}
                              </>
                            ) : (
                              <span className="text-slate-400">
                                -
                              </span>
                            )}
                          </td>
                          <td className="max-w-xs px-5 py-4 text-sm text-slate-600">
                            {day.note
                              || "-"}
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="px-6 py-12 text-center text-sm text-slate-500">
                No submitted attendance
                records exist for this month.
              </div>
            )}
          </article>
        </>
      ) : (
        <article className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center shadow-sm">
          <p className="font-bold text-slate-700">
            Select an employee and month
            to view the monthly report.
          </p>
          <p className="mt-2 text-sm text-slate-500">
            Missing attendance dates will
            remain Not Recorded.
          </p>
        </article>
      )}
    </section>
  );
}
